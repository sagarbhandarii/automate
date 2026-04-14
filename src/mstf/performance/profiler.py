"""ADB-driven Android performance profiling helpers."""

from __future__ import annotations

from dataclasses import dataclass, field
import re
import time
from typing import Callable

from mstf.device_manager.adb_client import ADBClient


_STARTUP_TOTAL_TIME_PATTERN = re.compile(r"TotalTime:\s*(\d+)")
_STARTUP_THIS_TIME_PATTERN = re.compile(r"ThisTime:\s*(\d+)")
_CPUINFO_LINE_PATTERN = re.compile(r"\s*([\d.]+)%\s+\d+/[^:]+:\s+(.+)")
_BATTERY_LEVEL_PATTERN = re.compile(r"level:\s*(\d+)")
_BATTERY_VOLTAGE_PATTERN = re.compile(r"voltage:\s*(\d+)")
_PSS_PATTERN = re.compile(r"TOTAL PSS:\s*(\d+)")
_FALLBACK_TOTAL_PATTERN = re.compile(r"TOTAL\s+(\d+)")


@dataclass(slots=True)
class StartupMeasurement:
    """Startup timing result for a single app launch."""

    mode: str
    total_time_ms: int
    this_time_ms: int


@dataclass(slots=True)
class ResourceSample:
    """Single CPU/memory sample gathered from dumpsys/cpuinfo."""

    timestamp_epoch_s: float
    cpu_percent: float
    total_pss_kb: int


@dataclass(slots=True)
class BatteryApproximation:
    """Approximate battery consumption during a workload window."""

    duration_seconds: float
    level_start_percent: int
    level_end_percent: int
    level_drop_percent: int
    drop_per_hour_percent: float
    voltage_start_mv: int | None = None
    voltage_end_mv: int | None = None


@dataclass(slots=True)
class SoakTestResult:
    """Long-run soak test report with summary statistics."""

    duration_seconds: int
    sample_interval_seconds: int
    sample_count: int
    avg_cpu_percent: float
    peak_cpu_percent: float
    avg_pss_kb: float
    peak_pss_kb: int
    anomalies: list[str] = field(default_factory=list)


class AndroidPerformanceProfiler:
    """Collects startup, runtime, battery, and soak metrics over ADB."""

    def __init__(self, adb_client: ADBClient | None = None) -> None:
        self._adb = adb_client or ADBClient()

    def measure_startup_time(
        self,
        serial: str,
        package_name: str,
        launch_activity: str,
        cold_runs: int = 3,
        warm_runs: int = 3,
    ) -> dict[str, list[StartupMeasurement]]:
        """Measure app startup latency using `am start -W` for cold and warm launches."""
        component = f"{package_name}/{launch_activity}"
        results: dict[str, list[StartupMeasurement]] = {"cold": [], "warm": []}

        for _ in range(max(0, cold_runs)):
            self._adb.shell(serial, f"am force-stop {package_name}")
            output = self._adb.shell(serial, f"am start -W -n {component}")
            results["cold"].append(self._parse_startup_output(output, mode="cold"))

        self._adb.shell(serial, f"am force-stop {package_name}")
        self._adb.shell(serial, f"am start -W -n {component}")
        for _ in range(max(0, warm_runs)):
            output = self._adb.shell(serial, f"am start -W -n {component}")
            results["warm"].append(self._parse_startup_output(output, mode="warm"))

        return results

    def track_cpu_and_memory(
        self,
        serial: str,
        package_name: str,
        samples: int = 10,
        interval_seconds: float = 1.0,
    ) -> list[ResourceSample]:
        """Track process CPU and memory over multiple `dumpsys` samples."""
        captured: list[ResourceSample] = []
        for index in range(max(0, samples)):
            cpu_text = self._adb.shell(serial, "dumpsys cpuinfo")
            mem_text = self._adb.shell(serial, f"dumpsys meminfo {package_name}")
            cpu = self._parse_cpu_percent(cpu_text=cpu_text, package_name=package_name)
            pss = self._parse_total_pss_kb(meminfo_text=mem_text)
            captured.append(
                ResourceSample(
                    timestamp_epoch_s=time.time(),
                    cpu_percent=cpu,
                    total_pss_kb=pss,
                )
            )
            if index < samples - 1:
                time.sleep(max(0.0, interval_seconds))
        return captured

    def approximate_battery_usage(
        self,
        serial: str,
        workload: Callable[[], None],
    ) -> BatteryApproximation:
        """Approximate battery usage by comparing pre/post `dumpsys battery` snapshots."""
        level_start, voltage_start = self._read_battery_snapshot(serial)
        start = time.time()
        workload()
        elapsed = max(0.001, time.time() - start)
        level_end, voltage_end = self._read_battery_snapshot(serial)
        level_drop = max(0, level_start - level_end)

        return BatteryApproximation(
            duration_seconds=elapsed,
            level_start_percent=level_start,
            level_end_percent=level_end,
            level_drop_percent=level_drop,
            drop_per_hour_percent=(level_drop / elapsed) * 3600,
            voltage_start_mv=voltage_start,
            voltage_end_mv=voltage_end,
        )

    def run_soak_test(
        self,
        serial: str,
        package_name: str,
        duration_seconds: int,
        sample_interval_seconds: int = 10,
        cpu_threshold_percent: float = 80.0,
        pss_threshold_kb: int = 800_000,
    ) -> SoakTestResult:
        """Run long-run soak sampling and report sustained resource regressions."""
        start = time.time()
        samples: list[ResourceSample] = []
        anomalies: list[str] = []

        while time.time() - start < duration_seconds:
            sample = self.track_cpu_and_memory(
                serial=serial,
                package_name=package_name,
                samples=1,
                interval_seconds=0,
            )[0]
            samples.append(sample)
            if sample.cpu_percent > cpu_threshold_percent:
                anomalies.append(f"High CPU: {sample.cpu_percent:.2f}%")
            if sample.total_pss_kb > pss_threshold_kb:
                anomalies.append(f"High memory: {sample.total_pss_kb} KB")
            time.sleep(max(1, sample_interval_seconds))

        if not samples:
            return SoakTestResult(
                duration_seconds=duration_seconds,
                sample_interval_seconds=sample_interval_seconds,
                sample_count=0,
                avg_cpu_percent=0.0,
                peak_cpu_percent=0.0,
                avg_pss_kb=0.0,
                peak_pss_kb=0,
                anomalies=anomalies,
            )

        cpu_values = [item.cpu_percent for item in samples]
        pss_values = [item.total_pss_kb for item in samples]
        return SoakTestResult(
            duration_seconds=duration_seconds,
            sample_interval_seconds=sample_interval_seconds,
            sample_count=len(samples),
            avg_cpu_percent=sum(cpu_values) / len(cpu_values),
            peak_cpu_percent=max(cpu_values),
            avg_pss_kb=sum(pss_values) / len(pss_values),
            peak_pss_kb=max(pss_values),
            anomalies=anomalies,
        )

    def _read_battery_snapshot(self, serial: str) -> tuple[int, int | None]:
        battery_text = self._adb.shell(serial, "dumpsys battery")
        level_match = _BATTERY_LEVEL_PATTERN.search(battery_text)
        if not level_match:
            raise ValueError("Unable to parse battery level from dumpsys battery")
        voltage_match = _BATTERY_VOLTAGE_PATTERN.search(battery_text)
        return int(level_match.group(1)), int(voltage_match.group(1)) if voltage_match else None

    def _parse_startup_output(self, output: str, mode: str) -> StartupMeasurement:
        total_match = _STARTUP_TOTAL_TIME_PATTERN.search(output)
        this_match = _STARTUP_THIS_TIME_PATTERN.search(output)
        if not total_match or not this_match:
            raise ValueError(f"Unable to parse am start output for {mode} startup: {output}")
        return StartupMeasurement(
            mode=mode,
            total_time_ms=int(total_match.group(1)),
            this_time_ms=int(this_match.group(1)),
        )

    def _parse_cpu_percent(self, cpu_text: str, package_name: str) -> float:
        for line in cpu_text.splitlines():
            if package_name not in line:
                continue
            match = _CPUINFO_LINE_PATTERN.match(line)
            if match:
                return float(match.group(1))
        return 0.0

    def _parse_total_pss_kb(self, meminfo_text: str) -> int:
        exact = _PSS_PATTERN.search(meminfo_text)
        if exact:
            return int(exact.group(1))
        fallback = _FALLBACK_TOTAL_PATTERN.search(meminfo_text)
        if fallback:
            return int(fallback.group(1))
        raise ValueError("Unable to parse total PSS from dumpsys meminfo output")

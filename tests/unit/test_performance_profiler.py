"""Tests for Android performance profiler module."""

from __future__ import annotations

import time

from mstf.performance.profiler import AndroidPerformanceProfiler


class FakeADBClient:
    def __init__(self) -> None:
        self.commands: list[str] = []
        self.battery_calls = 0

    def shell(self, serial: str, command: str, timeout_seconds: int | None = None) -> str:
        _ = serial, timeout_seconds
        self.commands.append(command)

        if command.startswith("am start -W"):
            return "Status: ok\nThisTime: 120\nTotalTime: 240\n"
        if command == "dumpsys cpuinfo":
            return " 12.5% 1234/com.example.app: 8.1% user + 4.4% kernel\n"
        if command.startswith("dumpsys meminfo"):
            return "Applications Memory Usage (in Kilobytes):\nTOTAL PSS: 456789\n"
        if command == "dumpsys battery":
            self.battery_calls += 1
            if self.battery_calls == 1:
                return "level: 80\nvoltage: 4200\n"
            return "level: 78\nvoltage: 4150\n"
        if command.startswith("am force-stop"):
            return ""

        raise AssertionError(f"Unexpected command: {command}")


def test_measure_startup_time_collects_cold_and_warm_results() -> None:
    profiler = AndroidPerformanceProfiler(adb_client=FakeADBClient())

    result = profiler.measure_startup_time(
        serial="SERIAL",
        package_name="com.example.app",
        launch_activity=".MainActivity",
        cold_runs=2,
        warm_runs=2,
    )

    assert len(result["cold"]) == 2
    assert len(result["warm"]) == 2
    assert all(item.total_time_ms == 240 for item in result["cold"])
    assert all(item.this_time_ms == 120 for item in result["warm"])


def test_track_cpu_and_memory_uses_dumpsys_values() -> None:
    profiler = AndroidPerformanceProfiler(adb_client=FakeADBClient())

    samples = profiler.track_cpu_and_memory(
        serial="SERIAL",
        package_name="com.example.app",
        samples=2,
        interval_seconds=0,
    )

    assert len(samples) == 2
    assert samples[0].cpu_percent == 12.5
    assert samples[0].total_pss_kb == 456789


def test_approximate_battery_usage_returns_level_drop() -> None:
    profiler = AndroidPerformanceProfiler(adb_client=FakeADBClient())

    def workload() -> None:
        time.sleep(0.001)

    result = profiler.approximate_battery_usage(serial="SERIAL", workload=workload)

    assert result.level_start_percent == 80
    assert result.level_end_percent == 78
    assert result.level_drop_percent == 2
    assert result.drop_per_hour_percent > 0


def test_run_soak_test_generates_summary() -> None:
    profiler = AndroidPerformanceProfiler(adb_client=FakeADBClient())

    result = profiler.run_soak_test(
        serial="SERIAL",
        package_name="com.example.app",
        duration_seconds=1,
        sample_interval_seconds=1,
        cpu_threshold_percent=10,
        pss_threshold_kb=100_000,
    )

    assert result.sample_count >= 1
    assert result.avg_cpu_percent >= 12.5
    assert result.peak_pss_kb >= 456789
    assert result.anomalies

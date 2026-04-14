"""Detection logic for crash and stability test signals."""

from __future__ import annotations

from dataclasses import dataclass, field
import re


@dataclass(slots=True, frozen=True)
class CrashStabilityFinding:
    """Single finding emitted by crash/stability analysis."""

    check_id: str
    severity: str
    title: str
    evidence: str


@dataclass(slots=True)
class CrashStabilityReport:
    """Aggregated crash/stability report across all checks."""

    findings: list[CrashStabilityFinding] = field(default_factory=list)

    @property
    def status(self) -> str:
        """Return failed when one or more findings were detected."""
        return "failed" if self.findings else "passed"


class CrashStabilityDetector:
    """Analyze ANR/crash/monkey/stress outputs for instability indicators."""

    _crash_patterns: tuple[tuple[str, re.Pattern[str]], ...] = (
        (
            "crashlog.fatal_exception",
            re.compile(r"(?i)f\s+androidruntime\s*:\s*fatal\s+exception"),
        ),
        (
            "crashlog.native_tombstone",
            re.compile(r"(?i)(backtrace:|signal\s+\d+\s+\(sig[a-z]+\)|tombstone\s+written)"),
        ),
        (
            "crashlog.process_died",
            re.compile(r"(?i)process\s+[\w.]+\s+has\s+died"),
        ),
    )

    _anr_patterns: tuple[re.Pattern[str], ...] = (
        re.compile(r"(?i)anr in [\w.]+"),
        re.compile(r"(?i)input dispatching timed out"),
        re.compile(r"(?i)executing service [\w./]+ timed out"),
    )

    def scan_anr_signals(self, logcat_output: str) -> list[CrashStabilityFinding]:
        """Detect ANR signatures in logcat traces."""
        for pattern in self._anr_patterns:
            match = pattern.search(logcat_output)
            if not match:
                continue
            return [
                CrashStabilityFinding(
                    check_id="stability.anr_detection",
                    severity="high",
                    title="ANR detected during runtime exercise",
                    evidence=f"Matched ANR marker: {match.group(0)[:140]}",
                )
            ]
        return []

    def scan_crash_logs(self, crash_output: str) -> list[CrashStabilityFinding]:
        """Detect app/native crashes in collected crash traces/logcat dumps."""
        findings: list[CrashStabilityFinding] = []
        for check_id, pattern in self._crash_patterns:
            match = pattern.search(crash_output)
            if not match:
                continue
            findings.append(
                CrashStabilityFinding(
                    check_id=check_id,
                    severity="high",
                    title="Crash signature captured",
                    evidence=f"Matched crash marker: {match.group(0)[:140]}",
                )
            )
        return findings

    def scan_monkey_results(self, monkey_output: str) -> list[CrashStabilityFinding]:
        """Parse monkey test output for aborts or excessive crash counts."""
        lowered = monkey_output.lower()
        findings: list[CrashStabilityFinding] = []

        if "monkey aborted" in lowered or "** system appears to have crashed" in lowered:
            findings.append(
                CrashStabilityFinding(
                    check_id="stability.monkey_abort",
                    severity="high",
                    title="Monkey test aborted",
                    evidence="Monkey runner aborted early or framework reported system crash.",
                )
            )

        crash_count_match = re.search(r"(?i)//\s*crashes:\s*(\d+)", monkey_output)
        if crash_count_match and int(crash_count_match.group(1)) > 0:
            findings.append(
                CrashStabilityFinding(
                    check_id="stability.monkey_crashes",
                    severity="high",
                    title="Monkey reported crash count",
                    evidence=f"Monkey summary crash count={crash_count_match.group(1)}",
                )
            )

        anr_count_match = re.search(r"(?i)//\s*anrs?:\s*(\d+)", monkey_output)
        if anr_count_match and int(anr_count_match.group(1)) > 0:
            findings.append(
                CrashStabilityFinding(
                    check_id="stability.monkey_anrs",
                    severity="high",
                    title="Monkey reported ANR count",
                    evidence=f"Monkey summary ANR count={anr_count_match.group(1)}",
                )
            )

        return findings

    def scan_background_foreground_stress(self, lifecycle_output: str) -> list[CrashStabilityFinding]:
        """Detect instability while repeatedly backgrounding/foregrounding the app."""
        lowered = lifecycle_output.lower()
        findings: list[CrashStabilityFinding] = []

        if "activity destroy timeout" in lowered or "app not responding" in lowered:
            findings.append(
                CrashStabilityFinding(
                    check_id="stability.bgfg_timeout",
                    severity="medium",
                    title="Background/foreground timeout",
                    evidence="Lifecycle stress loop hit timeout while moving app across states.",
                )
            )

        if "process died" in lowered or "force finishing activity" in lowered:
            findings.append(
                CrashStabilityFinding(
                    check_id="stability.bgfg_process_death",
                    severity="high",
                    title="Process death during lifecycle stress",
                    evidence="Lifecycle stress output indicates app process termination.",
                )
            )

        transition_match = re.search(r"(?i)successful transitions\s*:\s*(\d+)", lifecycle_output)
        if transition_match and int(transition_match.group(1)) < 20:
            findings.append(
                CrashStabilityFinding(
                    check_id="stability.bgfg_low_coverage",
                    severity="low",
                    title="Lifecycle stress had low transition coverage",
                    evidence=f"Only {transition_match.group(1)} successful transitions completed.",
                )
            )

        return findings

    def run_all(
        self,
        *,
        logcat_output: str,
        crash_output: str,
        monkey_output: str,
        lifecycle_output: str,
    ) -> CrashStabilityReport:
        """Execute ANR/crash/monkey/bgfg analyses and aggregate findings."""
        findings: list[CrashStabilityFinding] = []
        findings.extend(self.scan_anr_signals(logcat_output))
        findings.extend(self.scan_crash_logs(crash_output))
        findings.extend(self.scan_monkey_results(monkey_output))
        findings.extend(self.scan_background_foreground_stress(lifecycle_output))
        return CrashStabilityReport(findings=findings)

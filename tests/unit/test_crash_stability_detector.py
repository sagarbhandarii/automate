"""Unit tests for crash and stability detection logic."""

from __future__ import annotations

from mstf.security_suite.crash_stability import CrashStabilityDetector
from mstf.security_suite.registry import SecurityTestSuite, get_registry


def test_crash_stability_suite_registered() -> None:
    registry = get_registry()

    suite = registry["crash_stability"]
    assert isinstance(suite, SecurityTestSuite)
    assert [check.check_id for check in suite.checks] == [
        "stability.anr_detection",
        "crashlog.capture",
        "stability.monkey_integration",
        "stability.background_foreground_stress",
    ]


def test_detector_flags_crash_and_stability_findings() -> None:
    detector = CrashStabilityDetector()

    report = detector.run_all(
        logcat_output="ANR in com.example.app: Input dispatching timed out",
        crash_output="F AndroidRuntime: FATAL EXCEPTION: main\nProcess com.example.app has died",
        monkey_output="Monkey aborted due to error\n// CRASHES: 2\n// ANRs: 1",
        lifecycle_output="app not responding while resuming\nsuccessful transitions: 8\nprocess died",
    )

    finding_ids = {item.check_id for item in report.findings}

    assert report.status == "failed"
    assert "stability.anr_detection" in finding_ids
    assert "crashlog.fatal_exception" in finding_ids
    assert "crashlog.process_died" in finding_ids
    assert "stability.monkey_abort" in finding_ids
    assert "stability.monkey_crashes" in finding_ids
    assert "stability.monkey_anrs" in finding_ids
    assert "stability.bgfg_timeout" in finding_ids
    assert "stability.bgfg_process_death" in finding_ids
    assert "stability.bgfg_low_coverage" in finding_ids

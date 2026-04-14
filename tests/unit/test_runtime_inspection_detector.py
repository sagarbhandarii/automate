"""Unit tests for runtime inspection detection logic."""

from __future__ import annotations

from mstf.security_suite.runtime_inspection import RuntimeSecurityDetector
from mstf.security_suite.registry import SecurityTestSuite, get_registry


def test_runtime_inspection_suite_registered() -> None:
    registry = get_registry()

    suite = registry["runtime_inspection"]
    assert isinstance(suite, SecurityTestSuite)
    assert [check.check_id for check in suite.checks] == [
        "ssl_pinning.validation",
        "mitm_simulation.hooks",
        "logcat.sensitive_data",
        "storage.shared_prefs",
    ]


def test_detector_flags_expected_findings() -> None:
    detector = RuntimeSecurityDetector()

    report = detector.run_all(
        mitm_probe_output="TLS handshake accepted with injected CA; Certificate pinning bypassed",
        frida_hook_output="hook: okhttp3.certificatepinner.check",
        logcat_output="Authorization=Bearer abcdefghijklmnop1234",
        file_dump_output="-rw-rw-rw- 1 u0_a123 u0_a123 80 token=super-secret-value",
    )

    finding_ids = {item.check_id for item in report.findings}

    assert report.status == "failed"
    assert "ssl_pinning.validation" in finding_ids
    assert "mitm_simulation.hooks" in finding_ids
    assert "logcat.bearer_token" in finding_ids
    assert "storage.world_readable" in finding_ids
    assert "storage.sensitive_key" in finding_ids

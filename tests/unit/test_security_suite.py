"""Unit tests for generated security test suite definitions."""

from __future__ import annotations

from pathlib import Path

from mstf.orchestrator.orchestrator import TestOrchestrator
from mstf.orchestrator.run_context import RunOptions
from mstf.security_suite.registry import SecurityTestSuite, get_registry


def _write_config(path: Path) -> None:
    path.write_text(
        """
framework:
  name: test
  log_level: INFO
  parallel_workers: 1
execution:
  retry_count: 0
devices:
  targets:
    - serial: emulator-5554
security_tests:
  suites:
    - id: root_detection
      enabled: true
    - id: hooking_frida
      enabled: true
    - id: emulator_detection
      enabled: true
    - id: tampering
      enabled: true
performance:
  enabled: false
""",
        encoding="utf-8",
    )


def test_security_suite_contains_required_checks() -> None:
    registry = get_registry()

    root_suite = registry["root_detection"]
    frida_hooking_suite = registry["hooking_frida"]
    emulator_suite = registry["emulator_detection"]
    tamper_suite = registry["tampering"]

    assert isinstance(root_suite, SecurityTestSuite)
    assert isinstance(frida_hooking_suite, SecurityTestSuite)
    assert isinstance(emulator_suite, SecurityTestSuite)
    assert isinstance(tamper_suite, SecurityTestSuite)

    assert [check.check_id for check in root_suite.checks] == ["root.magisk", "root.su_binary"]
    assert [check.check_id for check in frida_hooking_suite.checks] == [
        "frida.server_running",
        "frida.runtime_attach",
        "hooking.xposed_lsposed",
    ]
    assert [check.check_id for check in emulator_suite.checks] == ["emulator.fingerprint"]
    assert [check.check_id for check in tamper_suite.checks] == ["tamper.apk_resigning"]


def test_orchestrator_returns_structured_security_results(tmp_path: Path) -> None:
    config_path = tmp_path / "config.yaml"
    _write_config(config_path)

    orchestrator = TestOrchestrator(
        config_path=str(config_path),
        options=RunOptions(run_security=True),
    )

    results = orchestrator.run()
    security_results = [item for item in results if item["suite_type"] == "security"]

    assert security_results
    assert all(item["status"] in {"passed", "failed"} for item in security_results)

    for suite_result in security_results:
        checks = suite_result.get("checks")
        if checks is None:
            continue
        assert isinstance(checks, list)
        for check_result in checks:
            assert check_result["status"] in {"passed", "failed"}
            assert isinstance(check_result["logs"], list)
            assert check_result["logs"]

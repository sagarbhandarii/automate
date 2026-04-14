"""Unit tests for orchestrator execution flow."""

from __future__ import annotations

from pathlib import Path

from mstf.orchestrator.orchestrator import TestOrchestrator
from mstf.orchestrator.run_context import RunOptions


def _write_config(path: Path, parallel_workers: int = 2, retries: int = 0) -> None:
    path.write_text(
        f"""
framework:
  name: test
  log_level: INFO
  parallel_workers: {parallel_workers}
execution:
  retry_count: {retries}
devices:
  targets:
    - serial: emulator-5554
security_tests:
  suites:
    - id: root_detection
      enabled: true
performance:
  enabled: true
""",
        encoding="utf-8",
    )


def test_orchestrator_can_filter_by_type(tmp_path: Path) -> None:
    config_path = tmp_path / "config.yaml"
    _write_config(config_path)

    orchestrator = TestOrchestrator(
        config_path=str(config_path),
        options=RunOptions(run_performance=True),
    )
    results = orchestrator.run()

    assert results
    assert all(item["suite_type"] == "performance" for item in results)


def test_orchestrator_can_filter_by_tag(tmp_path: Path) -> None:
    config_path = tmp_path / "config.yaml"
    _write_config(config_path)

    orchestrator = TestOrchestrator(
        config_path=str(config_path),
        options=RunOptions(tags={"root"}),
    )
    results = orchestrator.run()

    assert results
    assert {item["suite_id"] for item in results} == {"root_detection"}

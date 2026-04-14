"""CLI tests for main entrypoint."""

from __future__ import annotations

from pathlib import Path

from mstf.main import main


def test_main_runs_selected_suite(tmp_path: Path) -> None:
    config_path = tmp_path / "config.yaml"
    config_path.write_text(
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
performance:
  enabled: true
""",
        encoding="utf-8",
    )

    exit_code = main(["--config", str(config_path), "--suite", "root_detection"])
    assert exit_code == 0

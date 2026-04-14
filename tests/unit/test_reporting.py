"""Tests for report aggregation and dashboard export."""

from __future__ import annotations

import json
from pathlib import Path

from mstf.models.device_models import DeviceInfo
from mstf.models.result_models import TestResult
from mstf.models.run_models import PerformanceMetric
from mstf.reporting.aggregator import ReportAggregator
from mstf.reporting.html_exporter import HTMLDashboardExporter


def test_report_aggregator_builds_expected_sections() -> None:
    aggregator = ReportAggregator()

    report = aggregator.build_report(
        run_id="run-123",
        test_results=[
            TestResult(suite_id="root_detection", status="passed", device_serial="emulator-5554"),
            TestResult(suite_id="network_ssl", status="failed", device_serial="emulator-5554"),
        ],
        device_info=DeviceInfo(serial="emulator-5554", model="Pixel 8", os_version="Android 14"),
        logs=["[INFO] suite started", "[ERROR] certificate pinning bypass detected"],
        performance_metrics=[
            PerformanceMetric(name="cpu_avg", value=22.8, unit="%"),
            PerformanceMetric(name="startup_ms", value=745, unit="ms", threshold=900),
        ],
    )

    assert report["run_id"] == "run-123"
    assert report["summary"] == {"total": 2, "passed": 1, "failed": 1, "skipped": 0, "unknown": 0}
    assert report["device_info"]["model"] == "Pixel 8"
    assert len(report["performance_metrics"]) == 2


def test_report_aggregator_writes_json_to_disk(tmp_path: Path) -> None:
    aggregator = ReportAggregator()
    report = aggregator.build_report(
        run_id="run-001",
        test_results=[],
        device_info={"serial": "ABC"},
        logs=[],
        performance_metrics={"memory_peak_kb": 123456},
    )

    output = aggregator.write_json(report, tmp_path / "reports" / "run-001.json")

    parsed = json.loads(output.read_text(encoding="utf-8"))
    assert parsed["run_id"] == "run-001"
    assert parsed["performance_metrics"]["memory_peak_kb"] == 123456


def test_html_dashboard_exporter_contains_structured_sections(tmp_path: Path) -> None:
    report = {
        "run_id": "run-html-1",
        "summary": {"total": 1, "passed": 1, "failed": 0, "skipped": 0},
        "device_info": {"serial": "emulator-5554", "model": "Pixel"},
        "test_results": [
            {
                "suite_id": "root_detection",
                "status": "passed",
                "device_serial": "emulator-5554",
                "duration_seconds": 3.21,
            }
        ],
        "logs": ["run started", "run finished"],
        "performance_metrics": {"cpu_avg": "19%", "pss_peak_kb": 456789},
    }

    exporter = HTMLDashboardExporter()
    html_path = exporter.write(report, tmp_path / "dashboard.html")
    html = html_path.read_text(encoding="utf-8")

    assert "Execution Report" in html
    assert "Device Info" in html
    assert "Test Results" in html
    assert "Performance Metrics" in html
    assert "Logs" in html
    assert "root_detection" in html
    assert "cpu_avg" in html

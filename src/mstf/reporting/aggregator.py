"""Utilities for building JSON-ready report payloads."""

from __future__ import annotations

from collections import Counter
from dataclasses import asdict, is_dataclass
import json
from pathlib import Path
from typing import Any


class ReportAggregator:
    """Builds structured run reports from execution artifacts."""

    def build_report(
        self,
        *,
        run_id: str,
        test_results: list[dict[str, Any] | Any],
        device_info: dict[str, Any] | Any,
        logs: list[str],
        performance_metrics: dict[str, Any] | list[dict[str, Any] | Any],
    ) -> dict[str, Any]:
        """Assemble a complete report payload with summary and detailed sections."""
        normalized_results = [self._normalize_item(item) for item in test_results]
        normalized_device = self._normalize_item(device_info)
        normalized_metrics = self._normalize_metrics(performance_metrics)

        statuses = [str(result.get("status", "unknown")).lower() for result in normalized_results]
        status_counter = Counter(statuses)

        return {
            "run_id": run_id,
            "summary": {
                "total": len(normalized_results),
                "passed": status_counter.get("passed", 0),
                "failed": status_counter.get("failed", 0),
                "skipped": status_counter.get("skipped", 0),
                "unknown": status_counter.get("unknown", 0),
            },
            "test_results": normalized_results,
            "device_info": normalized_device,
            "logs": logs,
            "performance_metrics": normalized_metrics,
        }

    def to_json(self, report: dict[str, Any], *, indent: int = 2) -> str:
        """Render a report dictionary into JSON text."""
        return json.dumps(report, indent=indent, sort_keys=False)

    def write_json(self, report: dict[str, Any], output_path: str | Path, *, indent: int = 2) -> Path:
        """Write report JSON to disk and return the destination path."""
        path = Path(output_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(self.to_json(report, indent=indent), encoding="utf-8")
        return path

    def _normalize_metrics(
        self,
        performance_metrics: dict[str, Any] | list[dict[str, Any] | Any],
    ) -> dict[str, Any] | list[dict[str, Any]]:
        if isinstance(performance_metrics, list):
            return [self._normalize_item(item) for item in performance_metrics]
        if isinstance(performance_metrics, dict):
            return performance_metrics
        return self._normalize_item(performance_metrics)

    def _normalize_item(self, item: dict[str, Any] | Any) -> dict[str, Any]:
        if isinstance(item, dict):
            return item
        if is_dataclass(item):
            return asdict(item)
        if hasattr(item, "to_dict") and callable(item.to_dict):
            return item.to_dict()
        raise TypeError(f"Unsupported report item type: {type(item)!r}")

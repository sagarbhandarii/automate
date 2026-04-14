"""Utilities for persisting performance measurement artifacts."""

from __future__ import annotations

from dataclasses import asdict, is_dataclass
import json
from pathlib import Path
from typing import Any


class PerformanceMetricsStore:
    """Append/save performance artifacts as JSON for downstream analysis."""

    def __init__(self, output_dir: str | Path) -> None:
        self._output_dir = Path(output_dir)
        self._output_dir.mkdir(parents=True, exist_ok=True)

    def write_json(self, file_name: str, payload: Any) -> Path:
        """Write one JSON document."""
        path = self._output_dir / file_name
        serializable = self._to_serializable(payload)
        path.write_text(json.dumps(serializable, indent=2, sort_keys=True), encoding="utf-8")
        return path

    def append_jsonl(self, file_name: str, records: list[Any]) -> Path:
        """Append newline-delimited JSON records."""
        path = self._output_dir / file_name
        with path.open("a", encoding="utf-8") as handle:
            for record in records:
                handle.write(json.dumps(self._to_serializable(record), sort_keys=True))
                handle.write("\n")
        return path

    def _to_serializable(self, value: Any) -> Any:
        if is_dataclass(value):
            return asdict(value)
        if isinstance(value, list):
            return [self._to_serializable(item) for item in value]
        if isinstance(value, dict):
            return {key: self._to_serializable(item) for key, item in value.items()}
        return value

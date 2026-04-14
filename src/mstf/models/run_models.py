"""Run-level model definitions for aggregated reporting outputs."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone


@dataclass(slots=True)
class PerformanceMetric:
    """Single named performance metric item."""

    name: str
    value: float
    unit: str = ""
    threshold: float | None = None

    def to_dict(self) -> dict[str, object]:
        """Serialize metric into a report-friendly shape."""
        return asdict(self)


@dataclass(slots=True)
class RunMetadata:
    """Top-level metadata for a run report."""

    run_id: str
    started_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    framework_version: str = "dev"

    def to_dict(self) -> dict[str, object]:
        """Serialize metadata for report generation."""
        return asdict(self)

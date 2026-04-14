"""Result model definitions for test execution and reporting."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field


@dataclass(slots=True)
class TestResult:
    """Represents the outcome of one suite execution on one device."""

    __test__ = False

    suite_id: str
    status: str
    device_serial: str
    duration_seconds: float = 0.0
    severity: str = "info"
    details: dict[str, object] = field(default_factory=dict)

    def to_dict(self) -> dict[str, object]:
        """Serialize the result model to a JSON-compatible dictionary."""
        return asdict(self)

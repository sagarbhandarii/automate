"""Device model definitions used by reporting and orchestration layers."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field


@dataclass(slots=True)
class DeviceInfo:
    """Normalized device metadata for a test run."""

    serial: str
    model: str = "unknown"
    os_version: str = "unknown"
    manufacturer: str = "unknown"
    abi: str = "unknown"
    tags: dict[str, str] = field(default_factory=dict)

    def to_dict(self) -> dict[str, object]:
        """Serialize the device info for report output."""
        return asdict(self)

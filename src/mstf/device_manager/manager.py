"""Device detection and selection manager."""

from __future__ import annotations

from dataclasses import dataclass

from mstf.utils.config_loader import DeviceTarget


@dataclass(slots=True)
class Device:
    """Runtime device model."""

    serial: str
    alias: str | None = None


class DeviceManager:
    """Discovers available test devices."""

    def detect(self, targets: list[DeviceTarget]) -> list[Device]:
        """Detect configured targets.

        In this bootstrap implementation, configured targets are treated as connected.
        """
        return [Device(serial=target.serial, alias=target.alias) for target in targets]

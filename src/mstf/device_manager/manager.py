"""Device detection and ADB device operation manager."""

from __future__ import annotations

from dataclasses import dataclass

from mstf.device_manager.adb_client import ADBClient, ADBCommandError
from mstf.utils.config_loader import DeviceTarget


@dataclass(slots=True)
class Device:
    """Runtime device model."""

    serial: str
    alias: str | None = None
    model: str | None = None
    state: str = "unknown"
    rooted: bool | None = None


class DeviceManager:
    """Discovers and manages connected Android devices over ADB."""

    def __init__(self, adb_client: ADBClient | None = None) -> None:
        self._adb = adb_client or ADBClient()

    def detect(self, targets: list[DeviceTarget] | None = None) -> list[Device]:
        """Detect connected devices and optionally filter by configured targets."""
        try:
            connected = self._parse_devices_output(self._adb.devices())
        except ADBCommandError:
            connected = []
        if not targets:
            return connected

        if not connected:
            # Graceful fallback for local/unit-test environments without ADB.
            return [Device(serial=target.serial, alias=target.alias, state="configured") for target in targets]

        by_serial = {item.serial: item for item in connected}
        selected: list[Device] = []
        for target in targets:
            device = by_serial.get(target.serial)
            if not device:
                continue
            selected.append(
                Device(
                    serial=device.serial,
                    alias=target.alias or device.alias,
                    model=device.model,
                    state=device.state,
                    rooted=device.rooted,
                )
            )
        return selected

    def is_rooted(self, serial: str) -> bool:
        """Determine if device has root shell access."""
        try:
            probe = self.execute_shell(serial, "su -c id")
            if "uid=0" in probe:
                return True
        except ADBCommandError:
            pass

        try:
            fallback = self.execute_shell(serial, "which su")
            return bool(fallback and "not found" not in fallback.lower())
        except ADBCommandError:
            return False

    def install_apk(self, serial: str, apk_path: str, reinstall: bool = True) -> str:
        """Install APK to target device."""
        return self._adb.install_apk(serial, apk_path, reinstall=reinstall)

    def uninstall_apk(self, serial: str, package_name: str, keep_data: bool = False) -> str:
        """Uninstall package from target device."""
        return self._adb.uninstall_package(serial, package_name, keep_data=keep_data)

    def reboot(self, serial: str, rooted: bool | None = None) -> str:
        """Reboot device.

        Rooted automation first attempts shell reboot for environments where privileged
        device-management workflows require root shell invocation.
        """
        if rooted is None:
            rooted = self.is_rooted(serial)

        if rooted:
            try:
                return self.execute_shell(serial, "su -c reboot")
            except ADBCommandError:
                # Fallback to standard adb reboot if root automation path fails.
                return self._adb.reboot(serial)

        return self._adb.reboot(serial)

    def execute_shell(self, serial: str, command: str, timeout_seconds: int | None = None) -> str:
        """Execute arbitrary shell command on target device."""
        return self._adb.shell(serial, command=command, timeout_seconds=timeout_seconds)

    def fetch_logs(self, serial: str, *, lines: int = 1000, clear_first: bool = False) -> str:
        """Fetch device logcat output."""
        return self._adb.logcat(serial, lines=lines, clear=clear_first)

    @staticmethod
    def _parse_devices_output(raw_output: str) -> list[Device]:
        devices: list[Device] = []
        for line in raw_output.splitlines():
            entry = line.strip()
            if not entry or entry.startswith("List of devices attached"):
                continue

            parts = entry.split()
            if len(parts) < 2:
                continue

            serial = parts[0]
            state = parts[1]
            metadata = {
                item.split(":", 1)[0]: item.split(":", 1)[1]
                for item in parts[2:]
                if ":" in item
            }
            if state != "device":
                continue

            devices.append(
                Device(
                    serial=serial,
                    state=state,
                    model=metadata.get("model"),
                    alias=metadata.get("device"),
                )
            )
        return devices

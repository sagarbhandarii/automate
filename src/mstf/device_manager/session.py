"""Convenience session object for repeatedly operating on one device."""

from __future__ import annotations

from dataclasses import dataclass

from mstf.device_manager.manager import DeviceManager


@dataclass(slots=True)
class DeviceSession:
    """Reusable high-level API scoped to one device serial."""

    serial: str
    manager: DeviceManager

    def is_rooted(self) -> bool:
        return self.manager.is_rooted(self.serial)

    def install_apk(self, apk_path: str, reinstall: bool = True) -> str:
        return self.manager.install_apk(self.serial, apk_path=apk_path, reinstall=reinstall)

    def uninstall_apk(self, package_name: str, keep_data: bool = False) -> str:
        return self.manager.uninstall_apk(self.serial, package_name=package_name, keep_data=keep_data)

    def reboot(self, rooted: bool | None = None) -> str:
        return self.manager.reboot(self.serial, rooted=rooted)

    def shell(self, command: str, timeout_seconds: int | None = None) -> str:
        return self.manager.execute_shell(self.serial, command=command, timeout_seconds=timeout_seconds)

    def logs(self, lines: int = 1000, clear_first: bool = False) -> str:
        return self.manager.fetch_logs(self.serial, lines=lines, clear_first=clear_first)

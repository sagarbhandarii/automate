"""Integration-ish tests for device manager logic using fake adb client."""

from __future__ import annotations

from mstf.device_manager.adb_client import ADBCommandError
from mstf.device_manager.manager import DeviceManager
from mstf.utils.config_loader import DeviceTarget


class FakeADBClient:
    def __init__(self) -> None:
        self.shell_calls: list[tuple[str, str]] = []

    def devices(self) -> str:
        return """List of devices attached
emulator-5554 device product:sdk model:Pixel_8 device:emu
bad-state unauthorized
"""

    def shell(self, serial: str, command: str, timeout_seconds: int | None = None) -> str:
        self.shell_calls.append((serial, command))
        if command == "su -c id":
            return "uid=0(root) gid=0(root)"
        if command == "su -c reboot":
            raise ADBCommandError("root reboot unavailable")
        if command == "which su":
            return "/system/xbin/su"
        return "ok"

    def install_apk(self, serial: str, apk_path: str, reinstall: bool = True) -> str:
        return f"Success install {serial} {apk_path} reinstall={reinstall}"

    def uninstall_package(self, serial: str, package_name: str, keep_data: bool = False) -> str:
        return f"Success uninstall {serial} {package_name} keep={keep_data}"

    def reboot(self, serial: str) -> str:
        return f"reboot {serial}"

    def logcat(self, serial: str, *, clear: bool = False, lines: int = 1000) -> str:
        return f"logcat {serial} lines={lines} clear={clear}"


def test_detects_and_filters_connected_devices() -> None:
    manager = DeviceManager(adb_client=FakeADBClient())
    detected = manager.detect()

    assert len(detected) == 1
    assert detected[0].serial == "emulator-5554"
    assert detected[0].model == "Pixel_8"

    filtered = manager.detect([DeviceTarget(serial="emulator-5554", alias="local")])
    assert len(filtered) == 1
    assert filtered[0].alias == "local"


def test_device_lifecycle_operations() -> None:
    adb = FakeADBClient()
    manager = DeviceManager(adb_client=adb)

    assert manager.is_rooted("emulator-5554") is True
    assert manager.install_apk("emulator-5554", "/tmp/app.apk") == "Success install emulator-5554 /tmp/app.apk reinstall=True"
    assert manager.uninstall_apk("emulator-5554", "com.example.app", keep_data=True) == (
        "Success uninstall emulator-5554 com.example.app keep=True"
    )

    # Root reboot path fails and must fallback to plain adb reboot.
    assert manager.reboot("emulator-5554", rooted=True) == "reboot emulator-5554"

    assert manager.execute_shell("emulator-5554", "id") == "ok"
    assert manager.fetch_logs("emulator-5554", lines=200, clear_first=True) == "logcat emulator-5554 lines=200 clear=True"

    assert ("emulator-5554", "su -c reboot") in adb.shell_calls

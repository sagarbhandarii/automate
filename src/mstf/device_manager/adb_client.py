"""ADB client for device operations."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import subprocess


class ADBCommandError(RuntimeError):
    """Raised when an ADB command fails."""


@dataclass(slots=True)
class CompletedADBCommand:
    """Normalized subprocess result for ADB command execution."""

    args: list[str]
    returncode: int
    stdout: str
    stderr: str


class ADBClient:
    """Small, reusable ADB command runner with strong defaults."""

    def __init__(self, adb_path: str = "adb", timeout_seconds: int = 30) -> None:
        self._adb_path = adb_path
        self._timeout_seconds = timeout_seconds

    def devices(self) -> str:
        """Return raw output from `adb devices -l`."""
        return self._run(["devices", "-l"]).stdout

    def shell(self, serial: str, command: str, timeout_seconds: int | None = None) -> str:
        """Execute shell command on a specific device and return stdout."""
        return self._run(["-s", serial, "shell", command], timeout_seconds=timeout_seconds).stdout

    def install_apk(self, serial: str, apk_path: str | Path, reinstall: bool = True) -> str:
        """Install APK and return adb stdout."""
        path = Path(apk_path)
        if not path.exists():
            raise FileNotFoundError(f"APK path does not exist: {path}")

        args = ["-s", serial, "install"]
        if reinstall:
            args.append("-r")
        args.append(str(path))
        return self._run(args, timeout_seconds=180).stdout

    def uninstall_package(self, serial: str, package_name: str, keep_data: bool = False) -> str:
        """Uninstall package and return adb stdout."""
        args = ["-s", serial, "uninstall"]
        if keep_data:
            args.append("-k")
        args.append(package_name)
        return self._run(args, timeout_seconds=120).stdout

    def reboot(self, serial: str) -> str:
        """Reboot device normally and return adb stdout."""
        return self._run(["-s", serial, "reboot"]).stdout

    def logcat(self, serial: str, *, clear: bool = False, lines: int = 1000) -> str:
        """Read logcat output from device."""
        if clear:
            self._run(["-s", serial, "logcat", "-c"])
        return self._run(["-s", serial, "logcat", "-d", "-t", str(lines)], timeout_seconds=120).stdout

    def _run(self, args: list[str], timeout_seconds: int | None = None) -> CompletedADBCommand:
        command = [self._adb_path, *args]
        timeout = timeout_seconds if timeout_seconds is not None else self._timeout_seconds
        try:
            result = subprocess.run(
                command,
                check=False,
                capture_output=True,
                text=True,
                timeout=timeout,
            )
        except FileNotFoundError as exc:
            raise ADBCommandError(f"ADB executable not found: {self._adb_path}") from exc
        except subprocess.TimeoutExpired as exc:
            raise ADBCommandError(f"ADB command timed out after {timeout}s: {' '.join(command)}") from exc

        completed = CompletedADBCommand(
            args=command,
            returncode=result.returncode,
            stdout=result.stdout.strip(),
            stderr=result.stderr.strip(),
        )
        if completed.returncode != 0:
            raise ADBCommandError(
                f"ADB command failed ({completed.returncode}): {' '.join(command)}; stderr={completed.stderr or '<empty>'}"
            )
        return completed

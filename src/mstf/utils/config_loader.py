"""Configuration loader for test orchestrator."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path


@dataclass(slots=True)
class RetryPolicy:
    """Retry policy for failed suites."""

    count: int = 0


@dataclass(slots=True)
class ParallelConfig:
    """Concurrency configuration."""

    workers: int = 1


@dataclass(slots=True)
class DeviceTarget:
    """Configured device target."""

    serial: str
    alias: str | None = None


@dataclass(slots=True)
class ExecutionConfig:
    """Execution controls for the run."""

    timeout_seconds: int = 900
    retry: RetryPolicy = field(default_factory=RetryPolicy)
    parallel: ParallelConfig = field(default_factory=ParallelConfig)


@dataclass(slots=True)
class SuiteConfig:
    """Suite-level metadata from config."""

    suite_id: str
    enabled: bool = True
    tags: list[str] = field(default_factory=list)


@dataclass(slots=True)
class AppConfig:
    """Top-level orchestrator configuration."""

    name: str = "mstf"
    log_level: str = "INFO"
    devices: list[DeviceTarget] = field(default_factory=list)
    execution: ExecutionConfig = field(default_factory=ExecutionConfig)
    security_enabled: bool = True
    performance_enabled: bool = True
    suites: list[SuiteConfig] = field(default_factory=list)


class ConfigLoader:
    """Loads and normalizes framework configuration from YAML-like text."""

    def __init__(self, path: str | Path) -> None:
        self._path = Path(path)

    def load(self) -> AppConfig:
        """Load and normalize config."""
        raw_text = self._path.read_text(encoding="utf-8")

        framework = _parse_scalar_section(raw_text, "framework")
        execution = _parse_scalar_section(raw_text, "execution")
        performance = _parse_scalar_section(raw_text, "performance")
        devices = _parse_device_targets(raw_text)
        suites = _parse_suite_entries(raw_text)

        return AppConfig(
            name=framework.get("name", "mstf"),
            log_level=framework.get("log_level", "INFO"),
            devices=devices,
            execution=ExecutionConfig(
                timeout_seconds=int(execution.get("timeout_seconds", 900)),
                retry=RetryPolicy(count=int(execution.get("retry_count", 0))),
                parallel=ParallelConfig(workers=int(framework.get("parallel_workers", 1))),
            ),
            security_enabled=bool(suites),
            performance_enabled=_to_bool(performance.get("enabled", "false")),
            suites=suites,
        )


def _parse_scalar_section(text: str, section_name: str) -> dict[str, str]:
    section_indent = 0
    in_section = False
    parsed: dict[str, str] = {}

    for line in text.splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue

        indent = len(line) - len(line.lstrip())
        if stripped == f"{section_name}:":
            in_section = True
            section_indent = indent
            continue

        if in_section and indent <= section_indent and stripped.endswith(":"):
            break

        if in_section and ":" in stripped and not stripped.startswith("-"):
            key, value = stripped.split(":", 1)
            parsed[key.strip()] = value.strip().strip('"')

    return parsed


def _parse_device_targets(text: str) -> list[DeviceTarget]:
    targets: list[DeviceTarget] = []
    in_devices = False
    in_targets = False
    section_indent = 0
    current: dict[str, str] = {}

    for line in text.splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        indent = len(line) - len(line.lstrip())

        if stripped == "devices:":
            in_devices = True
            section_indent = indent
            in_targets = False
            current = {}
            continue

        if in_devices and indent <= section_indent and stripped.endswith(":") and stripped != "devices:":
            break

        if in_devices and stripped == "targets:":
            in_targets = True
            continue

        if in_targets and stripped.startswith("- "):
            if current.get("serial"):
                targets.append(DeviceTarget(serial=current["serial"], alias=current.get("alias")))
            current = {}
            token = stripped[2:]
            if ":" in token:
                key, value = token.split(":", 1)
                current[key.strip()] = value.strip()
            continue

        if in_targets and ":" in stripped and not stripped.endswith(":"):
            key, value = stripped.split(":", 1)
            current[key.strip()] = value.strip()

    if current.get("serial"):
        targets.append(DeviceTarget(serial=current["serial"], alias=current.get("alias")))

    return targets


def _parse_suite_entries(text: str) -> list[SuiteConfig]:
    suites: list[SuiteConfig] = []
    in_security = False
    in_suites = False
    section_indent = 0
    current: dict[str, str] = {}

    for line in text.splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        indent = len(line) - len(line.lstrip())

        if stripped == "security_tests:":
            in_security = True
            section_indent = indent
            in_suites = False
            current = {}
            continue

        if in_security and indent <= section_indent and stripped.endswith(":") and stripped != "security_tests:":
            break

        if in_security and stripped == "suites:":
            in_suites = True
            continue

        if in_suites and stripped.startswith("- "):
            if current.get("id"):
                suites.append(
                    SuiteConfig(
                        suite_id=current["id"],
                        enabled=_to_bool(current.get("enabled", "true")),
                        tags=["security", current["id"]],
                    )
                )
            current = {}
            token = stripped[2:]
            if ":" in token:
                key, value = token.split(":", 1)
                current[key.strip()] = value.strip()
            continue

        if in_suites and ":" in stripped and not stripped.endswith(":"):
            key, value = stripped.split(":", 1)
            current[key.strip()] = value.strip()

    if current.get("id"):
        suites.append(
            SuiteConfig(
                suite_id=current["id"],
                enabled=_to_bool(current.get("enabled", "true")),
                tags=["security", current["id"]],
            )
        )

    return suites


def _to_bool(value: str) -> bool:
    return value.strip().lower() in {"1", "true", "yes", "on"}

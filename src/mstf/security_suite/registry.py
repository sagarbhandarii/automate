"""Suite registry used by the orchestrator."""

from __future__ import annotations

from dataclasses import dataclass, field
from time import sleep


@dataclass(slots=True)
class TestSuite:
    """Executable test suite definition."""

    suite_id: str
    suite_type: str
    tags: set[str] = field(default_factory=set)

    def execute(self, device_serial: str) -> dict[str, str]:
        """Run suite against a specific device.

        Placeholder execution behavior for bootstrap orchestration.
        """
        sleep(0.05)
        return {
            "suite_id": self.suite_id,
            "suite_type": self.suite_type,
            "device": device_serial,
            "status": "passed",
        }


def get_registry() -> dict[str, TestSuite]:
    """Return available suite definitions."""
    suites = [
        TestSuite("root_detection", "security", {"security", "root", "android"}),
        TestSuite("hooking_frida", "security", {"security", "frida", "dynamic"}),
        TestSuite("tampering", "security", {"security", "integrity"}),
        TestSuite("network_ssl", "security", {"security", "network", "ssl"}),
        TestSuite("manifest_config", "security", {"security", "manifest", "static"}),
        TestSuite("performance_baseline", "performance", {"performance", "benchmark"}),
    ]
    return {suite.suite_id: suite for suite in suites}

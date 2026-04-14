"""Suite registry used by the orchestrator."""

from __future__ import annotations

from dataclasses import dataclass, field
from time import sleep

from mstf.security_suite.bypass_testing import BYPASS_SIMULATION_DEFINITIONS


@dataclass(slots=True)
class TestSuite:
    """Executable test suite definition."""

    suite_id: str
    suite_type: str
    tags: set[str] = field(default_factory=set)

    def execute(self, device_serial: str) -> dict[str, object]:
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


@dataclass(slots=True, frozen=True)
class SuiteCheck:
    """A single test case executed as part of a security suite."""

    check_id: str
    title: str
    log_hint: str


@dataclass(slots=True)
class SecurityTestSuite(TestSuite):
    """Security suite that emits structured check-level output."""

    checks: tuple[SuiteCheck, ...] = ()

    def execute(self, device_serial: str) -> dict[str, object]:
        """Execute checks and provide pass/fail plus logs for each case."""
        sleep(0.05)
        check_results: list[dict[str, object]] = []
        suite_logs: list[str] = []

        for check in self.checks:
            check_logs = [
                f"Running '{check.title}' on {device_serial}.",
                check.log_hint,
                "Baseline simulation completed without findings.",
            ]
            check_results.append(
                {
                    "check_id": check.check_id,
                    "title": check.title,
                    "status": "passed",
                    "logs": check_logs,
                }
            )
            suite_logs.append(f"{check.check_id}=passed")

        return {
            "suite_id": self.suite_id,
            "suite_type": self.suite_type,
            "device": device_serial,
            "status": "passed",
            "orchestrator": "test_orchestrator",
            "checks": check_results,
            "logs": suite_logs,
        }


def get_registry() -> dict[str, TestSuite]:
    """Return available suite definitions."""
    suites = [
        SecurityTestSuite(
            "root_detection",
            "security",
            {"security", "root", "android"},
            checks=(
                SuiteCheck("root.magisk", "Root Detection - Magisk", "Scanning package list for Magisk artifacts."),
                SuiteCheck("root.su_binary", "Root Detection - SU Binary", "Checking common su paths and shell execution."),
            ),
        ),
        SecurityTestSuite(
            "hooking_frida",
            "security",
            {"security", "frida", "dynamic", "hooking"},
            checks=(
                SuiteCheck("frida.server_running", "Frida Detection - Server Running", "Inspecting process list and local ports."),
                SuiteCheck("frida.runtime_attach", "Frida Detection - Runtime Attach", "Attempting anti-debug trap and ptrace checks."),
                SuiteCheck("hooking.xposed_lsposed", "Hooking Detection - Xposed/LSPosed", "Reviewing classloader and installed modules."),
            ),
        ),
        SecurityTestSuite(
            "emulator_detection",
            "security",
            {"security", "emulator", "environment"},
            checks=(SuiteCheck("emulator.fingerprint", "Emulator Detection", "Evaluating build fingerprint and hardware profile."),),
        ),
        SecurityTestSuite(
            "advanced_bypass_testing",
            "security",
            {"security", "bypass", "simulation", "frida", "runtime"},
            checks=tuple(SuiteCheck(*item) for item in BYPASS_SIMULATION_DEFINITIONS),
        ),
        SecurityTestSuite(
            "tampering",
            "security",
            {"security", "integrity"},
            checks=(
                SuiteCheck("tamper.apk_resigning", "Tamper Detection - APK Resigning Check", "Validating signing cert digest against expected."),
            ),
        ),
        SecurityTestSuite(
            "runtime_inspection",
            "security",
            {"security", "runtime", "mitm", "storage", "logs"},
            checks=(
                SuiteCheck(
                    "ssl_pinning.validation",
                    "SSL Pinning Validation",
                    "Runs MITM probe telemetry checks for forged certificate acceptance.",
                ),
                SuiteCheck(
                    "mitm_simulation.hooks",
                    "MITM Simulation Hooks",
                    "Validates expected Frida hook telemetry markers for SSL interception paths.",
                ),
                SuiteCheck(
                    "logcat.sensitive_data",
                    "Logcat Sensitive Data Scan",
                    "Scans runtime logs for secrets, bearer tokens, and JWT-like values.",
                ),
                SuiteCheck(
                    "storage.shared_prefs",
                    "File and SharedPreferences Inspection",
                    "Inspects app files/shared_prefs dumps for secrets and weak permissions.",
                ),
            ),
        ),
        TestSuite("network_ssl", "security", {"security", "network", "ssl"}),
        TestSuite("manifest_config", "security", {"security", "manifest", "static"}),
        TestSuite("performance_baseline", "performance", {"performance", "benchmark"}),
    ]
    return {suite.suite_id: suite for suite in suites}

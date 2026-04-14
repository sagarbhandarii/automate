"""Test orchestration logic for planning and executing suites."""

from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass

from mstf.device_manager.manager import DeviceManager
from mstf.orchestrator.run_context import RunOptions
from mstf.security_suite.registry import TestSuite, get_registry
from mstf.utils.config_loader import AppConfig, ConfigLoader
from mstf.utils.logger import configure_logging
from mstf.utils.retry import retry_call


@dataclass(slots=True)
class SuiteRun:
    """One suite execution unit."""

    suite: TestSuite
    device_serial: str


class TestOrchestrator:
    """Coordinates module lifecycle for a framework run."""

    def __init__(self, config_path: str = "config.yaml", options: RunOptions | None = None) -> None:
        self._config = ConfigLoader(config_path).load()
        self._options = options or RunOptions()
        self._logger = configure_logging(self._config.log_level)
        self._registry = get_registry()
        self._device_manager = DeviceManager()

    def run(self) -> list[dict[str, object]]:
        """Start one test run."""
        devices = self._device_manager.detect(self._config.devices)
        if not devices:
            self._logger.warning("No devices detected; exiting without running suites.")
            return []

        selected_suites = self._select_suites(self._config)
        if not selected_suites:
            self._logger.warning("No suites selected by current filters.")
            return []

        run_units = [SuiteRun(suite, device.serial) for suite in selected_suites for device in devices]
        workers = self._options.max_workers or self._config.execution.parallel.workers
        workers = max(1, workers)

        self._logger.info("Running %s suites across %s devices with %s worker(s).", len(selected_suites), len(devices), workers)

        results: list[dict[str, object]] = []
        with ThreadPoolExecutor(max_workers=workers) as executor:
            futures = [executor.submit(self._run_with_retry, unit) for unit in run_units]
            for future in as_completed(futures):
                results.append(future.result())

        passed = sum(1 for result in results if result["status"] == "passed")
        self._logger.info("Execution complete. Passed: %s / %s", passed, len(results))
        return results

    def _run_with_retry(self, unit: SuiteRun) -> dict[str, object]:
        attempts = self._config.execution.retry.count
        return retry_call(lambda: unit.suite.execute(unit.device_serial), attempts=attempts)

    def _select_suites(self, config: AppConfig) -> list[TestSuite]:
        explicit_selection = bool(
            self._options.run_security
            or self._options.run_performance
            or self._options.suite_ids
            or self._options.tags
        )

        suites: list[TestSuite] = []
        for suite in self._registry.values():
            if not self._suite_allowed_by_config(suite, config):
                continue
            if explicit_selection and not self._suite_allowed_by_options(suite):
                continue
            suites.append(suite)
        return suites

    def _suite_allowed_by_config(self, suite: TestSuite, config: AppConfig) -> bool:
        if suite.suite_type == "security":
            if not config.security_enabled:
                return False
            if config.suites:
                suite_cfg = next((item for item in config.suites if item.suite_id == suite.suite_id), None)
                return bool(suite_cfg and suite_cfg.enabled)
        if suite.suite_type == "performance":
            return config.performance_enabled
        return True

    def _suite_allowed_by_options(self, suite: TestSuite) -> bool:
        if self._options.suite_ids and suite.suite_id in self._options.suite_ids:
            return True
        if self._options.tags and (suite.tags & self._options.tags):
            return True
        if self._options.run_security and suite.suite_type == "security":
            return True
        if self._options.run_performance and suite.suite_type == "performance":
            return True
        return False

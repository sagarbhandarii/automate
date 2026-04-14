"""Tests for advanced bypass simulation suite and Frida templates."""

from __future__ import annotations

import pytest

from mstf.integrations.frida.controller import FridaController
from mstf.security_suite.registry import SecurityTestSuite, get_registry


def test_registry_contains_advanced_bypass_suite() -> None:
    registry = get_registry()

    suite = registry["advanced_bypass_testing"]
    assert isinstance(suite, SecurityTestSuite)
    assert [check.check_id for check in suite.checks] == [
        "bypass.hidden_root.magisk_zygisk",
        "bypass.frida.obfuscated_probe",
        "bypass.sdk.hook_simulation",
        "bypass.runtime.patch_simulation",
    ]


def test_frida_controller_loads_simulation_scripts() -> None:
    controller = FridaController()
    script_ids = {item.script_id for item in controller.available_scripts()}

    assert script_ids == {
        "obfuscated_probe",
        "sdk_hook_simulation",
        "runtime_patch_simulation",
    }

    payload = controller.load_script("sdk_hook_simulation")
    assert "Simulation-only" in payload
    assert "return original" in payload


def test_frida_controller_rejects_unknown_script() -> None:
    controller = FridaController()

    with pytest.raises(ValueError, match="Unknown Frida simulation script"):
        controller.load_script("unknown")

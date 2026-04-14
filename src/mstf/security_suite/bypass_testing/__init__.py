"""Advanced bypass simulation metadata.

This module intentionally provides **simulation-only** checks for authorized
security testing workflows. It does not implement real bypass behavior.
"""

from __future__ import annotations

BYPASS_SIMULATION_DEFINITIONS: tuple[tuple[str, str, str], ...] = (
    (
        "bypass.hidden_root.magisk_zygisk",
        "Hidden Root Detection Simulation - Magisk Hide/Zygisk",
        "Runs signal-based checks for concealed root indicators (simulation only).",
    ),
    (
        "bypass.frida.obfuscated_probe",
        "Obfuscated Frida Script Simulation",
        "Loads non-invasive Frida probes with encoded labels to emulate obfuscated delivery.",
    ),
    (
        "bypass.sdk.hook_simulation",
        "SDK Method Hook Simulation",
        "Attaches logging-only hooks to test method interception telemetry.",
    ),
    (
        "bypass.runtime.patch_simulation",
        "Runtime Patch Simulation",
        "Exercises a dry-run runtime patch path without mutating business logic.",
    ),
)

__all__ = ["BYPASS_SIMULATION_DEFINITIONS"]

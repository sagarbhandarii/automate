"""Frida script controller utilities."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True, slots=True)
class FridaScriptTemplate:
    """Represents a simulation script available to the test framework."""

    script_id: str
    description: str
    relative_path: str


class FridaController:
    """Loads simulation-only Frida scripts bundled with the framework."""

    _templates: tuple[FridaScriptTemplate, ...] = (
        FridaScriptTemplate(
            script_id="obfuscated_probe",
            description="Encoded-label probe used for anti-obfuscation telemetry tests.",
            relative_path="sample_obfuscated_probe.js",
        ),
        FridaScriptTemplate(
            script_id="sdk_hook_simulation",
            description="Logging-only SDK hook simulation that keeps original behavior.",
            relative_path="sdk_hook_simulation.js",
        ),
        FridaScriptTemplate(
            script_id="runtime_patch_simulation",
            description="Dry-run runtime patch simulation without state mutation.",
            relative_path="runtime_patch_simulation.js",
        ),
    )

    def __init__(self) -> None:
        self._scripts_dir = Path(__file__).resolve().parent / "scripts"

    def available_scripts(self) -> tuple[FridaScriptTemplate, ...]:
        """Return available simulation templates."""
        return self._templates

    def load_script(self, script_id: str) -> str:
        """Load script content by id.

        Raises ValueError when the script id is unknown.
        """
        template = next((item for item in self._templates if item.script_id == script_id), None)
        if template is None:
            raise ValueError(f"Unknown Frida simulation script: {script_id}")
        return (self._scripts_dir / template.relative_path).read_text(encoding="utf-8")

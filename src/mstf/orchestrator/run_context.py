"""Run context models for orchestrator."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(slots=True)
class RunOptions:
    """CLI and runtime options for filtering execution."""

    run_security: bool = False
    run_performance: bool = False
    suite_ids: set[str] = field(default_factory=set)
    tags: set[str] = field(default_factory=set)
    max_workers: int | None = None

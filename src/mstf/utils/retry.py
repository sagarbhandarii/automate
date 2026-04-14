"""Retry helpers."""

from __future__ import annotations

from collections.abc import Callable
from typing import TypeVar


T = TypeVar("T")


def retry_call(func: Callable[[], T], attempts: int) -> T:
    """Execute callable with retry attempts.

    Args:
        func: Callable to execute.
        attempts: Number of retry attempts after the initial attempt.
    """
    last_error: Exception | None = None
    for _ in range(attempts + 1):
        try:
            return func()
        except Exception as exc:  # pragma: no cover - branch tested via loop behavior
            last_error = exc
    assert last_error is not None
    raise last_error

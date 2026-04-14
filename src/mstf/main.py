"""Framework entrypoint module."""

from __future__ import annotations

import argparse

from mstf.orchestrator.orchestrator import TestOrchestrator
from mstf.orchestrator.run_context import RunOptions


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Mobile Security Test Framework orchestrator")
    parser.add_argument("--config", default="config.yaml", help="Path to YAML config file")
    parser.add_argument("--security", action="store_true", help="Run security suites")
    parser.add_argument("--performance", action="store_true", help="Run performance suites")
    parser.add_argument(
        "--suite",
        action="append",
        default=[],
        help="Specific suite id to run (repeatable)",
    )
    parser.add_argument(
        "--tag",
        action="append",
        default=[],
        help="Run suites matching one or more tags (repeatable)",
    )
    parser.add_argument("--workers", type=int, default=None, help="Override parallel worker count")
    return parser


def main(argv: list[str] | None = None) -> int:
    """Run framework orchestrator."""
    parser = _build_parser()
    args = parser.parse_args(argv)

    options = RunOptions(
        run_security=args.security,
        run_performance=args.performance,
        suite_ids=set(args.suite),
        tags=set(args.tag),
        max_workers=args.workers,
    )
    orchestrator = TestOrchestrator(config_path=args.config, options=options)
    orchestrator.run()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

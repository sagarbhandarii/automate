"""Framework entrypoint module."""

from mstf.orchestrator.orchestrator import TestOrchestrator


def main() -> int:
    """Run framework orchestrator."""
    orchestrator = TestOrchestrator()
    orchestrator.run()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

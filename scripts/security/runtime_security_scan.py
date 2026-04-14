#!/usr/bin/env python3
"""Runtime security scanner script.

Collects runtime artifacts via ADB and applies detection logic for:
1) SSL pinning validation
2) MITM simulation hooks
3) Logcat sensitive data scanning
4) File/SharedPreferences inspection
"""

from __future__ import annotations

import argparse
import json

from mstf.device_manager.adb_client import ADBClient
from mstf.security_suite.runtime_inspection import RuntimeSecurityDetector


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Runtime mobile security scanner")
    parser.add_argument("--serial", required=True, help="ADB device serial")
    parser.add_argument("--package", required=True, help="Application package name")
    parser.add_argument("--logcat-lines", type=int, default=2000, help="Number of logcat lines to collect")
    parser.add_argument(
        "--mitm-probe-output",
        default="",
        help="Optional MITM probe output text captured from external interception harness",
    )
    parser.add_argument(
        "--frida-hook-output",
        default="",
        help="Optional Frida runtime hook telemetry output",
    )
    return parser


def main() -> int:
    parser = _build_parser()
    args = parser.parse_args()

    adb = ADBClient()
    detector = RuntimeSecurityDetector()

    logcat_output = adb.logcat(args.serial, lines=args.logcat_lines)
    file_dump_output = adb.shell(
        args.serial,
        (
            f"run-as {args.package} sh -c \""
            "echo '[shared_prefs]'; "
            "ls -la shared_prefs 2>/dev/null; "
            "for f in shared_prefs/*.xml; do [ -f $f ] && echo '---' && cat $f; done; "
            "echo '[files]'; "
            "ls -la files 2>/dev/null\""
        ),
    )

    report = detector.run_all(
        mitm_probe_output=args.mitm_probe_output,
        frida_hook_output=args.frida_hook_output,
        logcat_output=logcat_output,
        file_dump_output=file_dump_output,
    )

    print(
        json.dumps(
            {
                "status": report.status,
                "findings": [
                    {
                        "check_id": finding.check_id,
                        "severity": finding.severity,
                        "title": finding.title,
                        "evidence": finding.evidence,
                    }
                    for finding in report.findings
                ],
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

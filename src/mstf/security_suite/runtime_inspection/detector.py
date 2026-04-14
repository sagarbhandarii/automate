"""Detection logic for runtime mobile security inspections."""

from __future__ import annotations

from dataclasses import dataclass, field
import re


@dataclass(slots=True, frozen=True)
class RuntimeSecurityFinding:
    """Single finding produced by runtime inspection logic."""

    check_id: str
    severity: str
    title: str
    evidence: str


@dataclass(slots=True)
class RuntimeSecurityReport:
    """Aggregated report from runtime inspection checks."""

    findings: list[RuntimeSecurityFinding] = field(default_factory=list)

    @property
    def status(self) -> str:
        """Return failed when at least one finding exists."""
        return "failed" if self.findings else "passed"


class RuntimeSecurityDetector:
    """Implements detection logic for common runtime exposure checks."""

    _sensitive_log_patterns: tuple[tuple[str, re.Pattern[str]], ...] = (
        (
            "logcat.api_token",
            re.compile(r"(?i)(api[_-]?key|access[_-]?token|secret|client[_-]?secret)\s*[:=]\s*['\"]?[A-Za-z0-9_.-]{12,}"),
        ),
        (
            "logcat.bearer_token",
            re.compile(r"(?i)authorization\s*[:=]\s*bearer\s+[A-Za-z0-9._-]{16,}"),
        ),
        (
            "logcat.jwt",
            re.compile(r"eyJ[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+"),
        ),
    )

    _sensitive_key_patterns: tuple[re.Pattern[str], ...] = (
        re.compile(r"(?i)(password|passwd|token|secret|session|refresh)"),
        re.compile(r"(?i)(authorization|cookie|private[_-]?key|credential)"),
    )

    def scan_ssl_pinning_validation(self, mitm_probe_output: str) -> list[RuntimeSecurityFinding]:
        """Detect weak SSL pinning behavior from MITM probe output.

        Expected probe text can include signals like:
        - "TLS handshake accepted with injected CA"
        - "Certificate pinning bypassed"
        - "CERTIFICATE_VERIFY_FAILED"
        """
        lowered = mitm_probe_output.lower()
        findings: list[RuntimeSecurityFinding] = []

        if "accepted with injected ca" in lowered or "pinning bypassed" in lowered:
            findings.append(
                RuntimeSecurityFinding(
                    check_id="ssl_pinning.validation",
                    severity="high",
                    title="SSL pinning bypass detected",
                    evidence="MITM probe accepted a forged/intercepting certificate chain.",
                )
            )

        if "certificate_verify_failed" in lowered or "pinning enforced" in lowered:
            return findings

        if not mitm_probe_output.strip():
            findings.append(
                RuntimeSecurityFinding(
                    check_id="ssl_pinning.validation",
                    severity="medium",
                    title="SSL pinning validation inconclusive",
                    evidence="No MITM probe output was provided for SSL pinning validation.",
                )
            )

        return findings

    def scan_mitm_simulation_hooks(self, frida_hook_output: str) -> list[RuntimeSecurityFinding]:
        """Verify that MITM simulation hooks are present and instrumented."""
        lowered = frida_hook_output.lower()
        findings: list[RuntimeSecurityFinding] = []

        expected_markers = (
            "hook: okhttp3.certificatepinner.check",
            "hook: x509trustmanager.checkservertrusted",
            "hook: hostnameverifier.verify",
        )

        missing = [marker for marker in expected_markers if marker not in lowered]
        if missing:
            findings.append(
                RuntimeSecurityFinding(
                    check_id="mitm_simulation.hooks",
                    severity="medium",
                    title="MITM simulation hooks missing",
                    evidence=f"Missing expected hook telemetry markers: {', '.join(missing)}",
                )
            )

        if "hook_error" in lowered or "classnotfoundexception" in lowered:
            findings.append(
                RuntimeSecurityFinding(
                    check_id="mitm_simulation.hooks",
                    severity="low",
                    title="MITM hook runtime errors observed",
                    evidence="Hook runtime emitted class resolution/installation errors.",
                )
            )

        return findings

    def scan_logcat_for_sensitive_data(self, logcat_output: str) -> list[RuntimeSecurityFinding]:
        """Find sensitive values emitted to Logcat."""
        findings: list[RuntimeSecurityFinding] = []
        for check_id, pattern in self._sensitive_log_patterns:
            match = pattern.search(logcat_output)
            if not match:
                continue
            snippet = match.group(0)
            findings.append(
                RuntimeSecurityFinding(
                    check_id=check_id,
                    severity="high",
                    title="Sensitive data in Logcat",
                    evidence=f"Matched pattern in runtime logs: {snippet[:120]}",
                )
            )
        return findings

    def scan_files_and_shared_prefs(self, file_dump_output: str) -> list[RuntimeSecurityFinding]:
        """Inspect exported file/SharedPreferences dump for secrets and weak permissions."""
        findings: list[RuntimeSecurityFinding] = []
        lines = [line.strip() for line in file_dump_output.splitlines() if line.strip()]

        for line in lines:
            if line.startswith("-rw-rw-rw-"):
                findings.append(
                    RuntimeSecurityFinding(
                        check_id="storage.world_readable",
                        severity="medium",
                        title="World-readable app data file",
                        evidence=f"Insecure file permission detected: {line}",
                    )
                )
            if any(pattern.search(line) for pattern in self._sensitive_key_patterns):
                findings.append(
                    RuntimeSecurityFinding(
                        check_id="storage.sensitive_key",
                        severity="high",
                        title="Sensitive key/value in file or SharedPreferences",
                        evidence=f"Potential secret material in storage artifact: {line[:160]}",
                    )
                )

        return findings

    def run_all(
        self,
        *,
        mitm_probe_output: str,
        frida_hook_output: str,
        logcat_output: str,
        file_dump_output: str,
    ) -> RuntimeSecurityReport:
        """Execute all runtime inspection checks and combine findings."""
        findings: list[RuntimeSecurityFinding] = []
        findings.extend(self.scan_ssl_pinning_validation(mitm_probe_output))
        findings.extend(self.scan_mitm_simulation_hooks(frida_hook_output))
        findings.extend(self.scan_logcat_for_sensitive_data(logcat_output))
        findings.extend(self.scan_files_and_shared_prefs(file_dump_output))
        return RuntimeSecurityReport(findings=findings)

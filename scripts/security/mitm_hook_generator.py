#!/usr/bin/env python3
"""Generate MITM simulation Frida hook script (telemetry only)."""

from __future__ import annotations

from textwrap import dedent


def generate_hook_script() -> str:
    """Return JavaScript hooks for SSL/MITM simulation telemetry.

    Hooks are non-invasive: they emit events and call original methods.
    """
    return dedent(
        """
        // Simulation-only MITM hook telemetry.
        Java.perform(function () {
          function emit(msg) { send(msg); }

          try {
            var Pinner = Java.use('okhttp3.CertificatePinner');
            Pinner.check.overload('java.lang.String', 'java.util.List').implementation = function(host, pins) {
              emit('hook: okhttp3.certificatepinner.check host=' + host);
              return this.check(host, pins);
            };
          } catch (e) { emit('hook_error: okhttp3.CertificatePinner ' + e); }

          try {
            var X509TM = Java.use('javax.net.ssl.X509TrustManager');
            X509TM.checkServerTrusted.implementation = function(chain, authType) {
              emit('hook: x509trustmanager.checkservertrusted auth=' + authType);
              return this.checkServerTrusted(chain, authType);
            };
          } catch (e) { emit('hook_error: javax.net.ssl.X509TrustManager ' + e); }

          try {
            var HostnameVerifier = Java.use('javax.net.ssl.HostnameVerifier');
            HostnameVerifier.verify.implementation = function(host, session) {
              emit('hook: hostnameverifier.verify host=' + host);
              return this.verify(host, session);
            };
          } catch (e) { emit('hook_error: javax.net.ssl.HostnameVerifier ' + e); }
        });
        """
    ).strip() + "\n"


if __name__ == "__main__":
    print(generate_hook_script())

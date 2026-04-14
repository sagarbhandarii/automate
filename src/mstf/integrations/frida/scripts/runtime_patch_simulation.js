/*
 * Runtime patch dry-run simulation: computes a hypothetical patch plan only.
 */

Java.perform(function () {
  const plan = {
    target: 'com.example.security.AttestationVerifier#verify',
    operation: 'dry_run_patch',
    mutation: false,
    timestamp_ms: Date.now(),
  };

  send({ type: 'runtime_patch_simulation', plan: plan });
});

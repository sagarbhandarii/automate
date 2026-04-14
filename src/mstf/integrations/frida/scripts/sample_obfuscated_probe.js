/*
 * Simulation-only probe for authorized testing.
 * This script logs instrumentation points and does not bypass protections.
 */

(function () {
  const encodedTag = [0x62, 0x79, 0x70, 0x61, 0x73, 0x73, 0x5f, 0x73, 0x69, 0x6d]
    .map((c) => String.fromCharCode(c))
    .join('');

  send({ type: 'sim_probe', tag: encodedTag, stage: 'attach' });

  Java.perform(function () {
    send({
      type: 'sim_probe',
      stage: 'java_perform',
      note: 'No-op instrumentation active',
    });
  });
})();

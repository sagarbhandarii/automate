/*
 * Simulation-only method hook. Logs invocations and preserves original behavior.
 */

Java.perform(function () {
  const targetClass = 'com.example.security.SecuritySDK';
  try {
    const SDK = Java.use(targetClass);
    const method = SDK.isDeviceTrusted.overload();

    method.implementation = function () {
      const original = method.call(this);
      send({
        type: 'sdk_hook_simulation',
        class: targetClass,
        method: 'isDeviceTrusted',
        original_result: original,
      });
      return original;
    };
  } catch (error) {
    send({
      type: 'sdk_hook_simulation',
      status: 'skipped',
      reason: String(error),
    });
  }
});

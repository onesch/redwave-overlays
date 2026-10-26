// Recording stub of the `createSettingsApi()` facade: `createSettingsApiStub(values)` feeds the
// loaded values, and the mount tests assert on `api.calls` / `api.lastCall()`.

const READ_METHODS = [
  'openOverlay',
  'getZoom', 'setZoom',
  'getBackgroundOpacity', 'setBackgroundOpacity',
  'getDisplayMode', 'setDisplayMode',
  'getAutoStartMode', 'setAutoStartMode',
  'getMovementState', 'toggleMovementState',
  'getLastLapFormat', 'setLastLapFormat',
  'getSpeedUnit', 'setSpeedUnit',
  'getRadarVisibility', 'setRadarVisibility',
  'getTrackType', 'setTrackType',
];

const SUBSCRIBE_METHODS = ['onMovementStateChange'];

function createSettingsApiStub(values = {}) {
  const calls = [];
  const listeners = new Map();

  const stub = {
    calls,

    // Arguments of the most recent call to a given method, for assertions.
    lastCall(name) {
      return calls.filter((call) => call.name === name).at(-1)?.args;
    },

    // Fire a subscribed listener, like the main process would.
    trigger(name, ...args) {
      (listeners.get(name) ?? []).forEach((listener) => listener(...args));
    },
  };

  READ_METHODS.forEach((name) => {
    stub[name] = (...args) => {
      calls.push({ name, args });
      return values[name];
    };
  });

  SUBSCRIBE_METHODS.forEach((name) => {
    stub[name] = (listener) => {
      listeners.set(name, [...(listeners.get(name) ?? []), listener]);
    };
  });

  return stub;
}

module.exports = { createSettingsApiStub };

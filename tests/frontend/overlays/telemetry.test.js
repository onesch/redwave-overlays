const test = require('node:test');
const assert = require('node:assert/strict');

test('TelemetryApi uses the telemetry endpoint and validates responses', async () => {
  const { TelemetryApi } = await import(
    '../../../frontend/overlays/telemetry/telemetryApi.js'
  );
  const dto = { status: 'ok', throttle: 0.5 };
  let requestedEndpoint;
  const api = new TelemetryApi(undefined, async (endpoint) => {
    requestedEndpoint = endpoint;
    return { ok: true, json: async () => dto };
  });

  assert.equal(await api.getTelemetry(), dto);
  assert.equal(requestedEndpoint, '/api/telemetry');

  const failingApi = new TelemetryApi('/api/telemetry', async () => ({
    ok: false,
    status: 500,
  }));
  await assert.rejects(failingApi.getTelemetry(), /Failed to fetch telemetry: 500/);
});

test('TelemetryUpdater uses the shared updater with the original 50 ms interval', async () => {
  const { BaseUpdater } = await import('../../../frontend/overlays/shared/baseUpdater.js');
  const { TelemetryUpdater } = await import(
    '../../../frontend/overlays/telemetry/telemetryUpdater.js'
  );
  const dto = { status: 'ok' };
  const updater = new TelemetryUpdater(
    { getTelemetry: async () => dto },
    {},
    { electronAPI: {} },
  );

  assert.ok(updater instanceof BaseUpdater);
  assert.equal(updater.updateInterval, 50);
  assert.equal(updater.overlayName, 'telemetry');
  assert.equal(await updater.getDto(), dto);
});

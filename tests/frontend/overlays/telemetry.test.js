const test = require('node:test');
const assert = require('node:assert/strict');

const { FakeDocument, FakeWindow } = require('../helpers/dom');
const { describeApiContract } = require('../helpers/api_contract');

const TELEMETRY_API = '../../../frontend/overlays/telemetry/telemetryApi.js';
const TELEMETRY_UPDATER = '../../../frontend/overlays/telemetry/telemetryUpdater.js';
const TELEMETRY_RENDERER = '../../../frontend/overlays/telemetry/telemetryRenderer.js';
const BASE_UPDATER = '../../../frontend/overlays/shared/baseUpdater.js';

describeApiContract({
  title: 'TelemetryApi',
  loadApi: async () => (await import(TELEMETRY_API)).TelemetryApi,
  method: 'getTelemetry',
  endpoint: '/api/telemetry',
});

// Telemetry overlay markup: scope canvas plus pedal, gear and speed readouts.
function createTelemetryDocument() {
  return new FakeDocument({
    'telemetry-canvas': '',
    'gear-header': '',
    'speed-header': '',
    'throttle-pct-header': '',
    'throttle-fill-peak': '',
    'throttle-fill-mid': '',
    'throttle-fill-dead': '',
    'brake-pct-header': '',
    'brake-fill-peak': '',
    'brake-fill-mid': '',
    'brake-fill-dead': '',
  });
}

test('TelemetryUpdater polls telemetry data on its own interval', async () => {
  const { BaseUpdater } = await import(BASE_UPDATER);
  const { TelemetryUpdater } = await import(TELEMETRY_UPDATER);
  const dto = { status: 'ok' };

  const updater = new TelemetryUpdater(
    { getTelemetry: async () => dto },
    {},
    { electronAPI: {} },
  );

  assert.ok(updater instanceof BaseUpdater);
  assert.equal(updater.overlayName, 'telemetry');
  assert.equal(updater.updateInterval, 50);
  assert.equal(await updater.getDto(), dto);
});

test('TelemetryRenderer renders readouts and records pedal history', async () => {
  const { TelemetryRenderer } = await import(TELEMETRY_RENDERER);
  const document = createTelemetryDocument();
  const renderer = new TelemetryRenderer(document, new FakeWindow());

  renderer.render({
    throttle: 0.75,
    throttle_pct: 75,
    brake: 0.25,
    brake_pct: 25,
    is_brake_abs: true,
    gear: 3,
    speed_km: 123.6,
  });

  assert.equal(document.getElementById('gear-header').textContent, '3');
  assert.equal(document.getElementById('speed-header').textContent, 124);
  assert.equal(document.getElementById('throttle-pct-header').textContent, '75');
  assert.equal(document.getElementById('brake-pct-header').textContent, '25');
  assert.equal(renderer.thrHistory.at(-1), 0.75);
  assert.equal(renderer.brkHistory.at(-1), 0.25);
  assert.equal(renderer.brkAbsHistory.at(-1), true);

  // Reverse and neutral are labelled instead of numbered.
  renderer.renderGear(-1);
  assert.equal(document.getElementById('gear-header').textContent, 'R');
  renderer.renderGear(0);
  assert.equal(document.getElementById('gear-header').textContent, 'N');
});

test('TelemetryRenderer normalizes pedal values and fills the pedal zones', async () => {
  const { TelemetryRenderer } = await import(TELEMETRY_RENDERER);
  const document = createTelemetryDocument();
  const renderer = new TelemetryRenderer(document, new FakeWindow());

  renderer.renderPedal('throttle', 1, 100);
  assert.equal(document.getElementById('throttle-pct-header').textContent, 'FL');
  assert.equal(document.getElementById('throttle-fill-peak').style.height, '100%');

  // Out-of-range values are clamped into the pedal zones.
  renderer.renderPedal('brake', -10, undefined);
  assert.equal(document.getElementById('brake-pct-header').textContent, '0');
  assert.equal(document.getElementById('brake-fill-dead').style.height, '0%');
});

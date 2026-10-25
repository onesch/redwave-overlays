const test = require('node:test');
const assert = require('node:assert/strict');

const { FakeDocument, FakeWindow } = require('../helpers/dom');
const { describeApiContract } = require('../helpers/api_contract');
const { BASE_UPDATER } = require('../helpers/modules');

const TELEMETRY_API = '../../../frontend/overlays/telemetry/telemetryApi.js';
const TELEMETRY_UPDATER = '../../../frontend/overlays/telemetry/telemetryUpdater.js';
const TELEMETRY_RENDERER = '../../../frontend/overlays/telemetry/telemetryRenderer.js';

describeApiContract({
  title: 'TelemetryApi',
  loadApi: async () => (await import(TELEMETRY_API)).TelemetryApi,
  method: 'getTelemetry',
  endpoint: '/api/telemetry',
});

// Telemetry overlay markup: scope canvas plus pedal, gear and speed readouts.
function createTelemetryDocument() {
  const document = new FakeDocument({
    'telemetry-canvas': '',
    'gear-header': '',
    'speed-header': '',
    'speed-value': '',
    'top-speed-header': '',
    'exit-speed-header': '',
    'throttle-pct-header': '',
    'throttle-fill-peak': '',
    'throttle-fill-mid': '',
    'throttle-fill-dead': '',
    'brake-pct-header': '',
    'brake-fill-peak': '',
    'brake-fill-mid': '',
    'brake-fill-dead': '',
  });

  document.querySelector = (selector) => {
    if (selector === '#speed-header .speed-value') {
      return document.getElementById('speed-value');
    }

    return null;
  };

  return document;
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
  assert.equal(document.querySelector('#speed-header .speed-value').textContent, 124);
  assert.equal(document.getElementById('top-speed-header').textContent, '--');
  assert.equal(document.getElementById('exit-speed-header').textContent, '--');
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

test('TelemetryRenderer shows latched top and exit speed', async () => {
  const { TelemetryRenderer } = await import(TELEMETRY_RENDERER);
  const document = createTelemetryDocument();
  const renderer = new TelemetryRenderer(document, new FakeWindow());

  renderer.render({
    throttle: 1,
    throttle_pct: 100,
    brake: 0,
    brake_pct: 0,
    gear: 5,
    speed_km: 201.4,
    top_speed_km: 287.6,
    exit_speed_km: 152.2,
  });

  assert.equal(document.getElementById('top-speed-header').textContent, 288);
  assert.equal(document.getElementById('exit-speed-header').textContent, 152);

  // Values are cleared back to the placeholder until they are latched again.
  renderer.renderSpeedMetric('top-speed-header', null);
  renderer.renderSpeedMetric('exit-speed-header', undefined);
  assert.equal(document.getElementById('top-speed-header').textContent, '--');
  assert.equal(document.getElementById('exit-speed-header').textContent, '--');
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

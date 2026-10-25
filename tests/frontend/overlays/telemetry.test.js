const test = require('node:test');
const assert = require('node:assert/strict');

const { FakeDocument, FakeWindow } = require('../helpers/dom');
const { describeApiContract } = require('../helpers/api_contract');
const { BASE_UPDATER } = require('../helpers/modules');

const TELEMETRY_API = '../../../frontend/overlays/telemetry/telemetryApi.js';
const TELEMETRY_UPDATER = '../../../frontend/overlays/telemetry/telemetryUpdater.js';
const TELEMETRY_RENDERER = '../../../frontend/overlays/telemetry/telemetryRenderer.js';
const SPEED_UNIT = '../../../frontend/overlays/telemetry/speedUnit.js';

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
    'speed-unit-label': 'KM/H',
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

test('TelemetryUpdater loads the speed unit and follows runtime changes', async () => {
  const { TelemetryUpdater } = await import(TELEMETRY_UPDATER);
  const units = [];
  let unitListener;

  const updater = new TelemetryUpdater(
    { getTelemetry: async () => ({ status: 'ok' }) },
    { setSpeedUnit: (unit) => units.push(unit) },
    {
      electronAPI: {
        getSpeedUnit: async () => 'mph',
        onSpeedUnitUpdate: (listener) => { unitListener = listener; },
      },
    },
  );

  await updater.initFeature();
  unitListener('kmh');
  assert.deepEqual(units, ['mph', 'kmh']);
});

test('SpeedUnit converts km/h speeds and labels the readouts', async () => {
  const SpeedUnit = await import(SPEED_UNIT);

  assert.equal(SpeedUnit.normalizeSpeedUnit('mph'), 'mph');
  assert.equal(SpeedUnit.normalizeSpeedUnit('bogus'), SpeedUnit.DEFAULT_SPEED_UNIT);
  assert.equal(SpeedUnit.speedUnitLabel('kmh'), 'KM/H');
  assert.equal(SpeedUnit.speedUnitLabel('mph'), 'MPH');

  // The backend always reports km/h, so only mph needs converting.
  assert.equal(SpeedUnit.toDisplaySpeed(100, 'kmh'), 100);
  assert.ok(Math.abs(SpeedUnit.toDisplaySpeed(100, 'mph') - 62.1371) < 1e-9);
  // Missing speeds are passed through so they render as a placeholder.
  assert.equal(SpeedUnit.toDisplaySpeed(undefined, 'mph'), undefined);
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

test('TelemetryRenderer renders every speed readout in the selected unit', async () => {
  const { TelemetryRenderer } = await import(TELEMETRY_RENDERER);
  const document = createTelemetryDocument();
  const renderer = new TelemetryRenderer(document, new FakeWindow());

  renderer.setSpeedUnit('mph');
  assert.equal(document.getElementById('speed-unit-label').textContent, 'MPH');

  renderer.render({
    throttle: 1,
    throttle_pct: 100,
    brake: 0,
    brake_pct: 0,
    gear: 5,
    speed_km: 123.6,
    top_speed_km: 287.6,
    exit_speed_km: 152.2,
  });

  assert.equal(document.querySelector('#speed-header .speed-value').textContent, 77);
  assert.equal(document.getElementById('top-speed-header').textContent, 179);
  assert.equal(document.getElementById('exit-speed-header').textContent, 95);

  // Back to metric, and an unsupported unit falls back to the default.
  renderer.setSpeedUnit('kmh');
  assert.equal(document.getElementById('speed-unit-label').textContent, 'KM/H');
  renderer.setSpeedUnit('furlongs');
  assert.equal(renderer.speedUnit, 'kmh');
  assert.equal(document.getElementById('speed-unit-label').textContent, 'KM/H');
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

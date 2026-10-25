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
    'speed-unit-label': '',
    'top-speed-header': '--',
    'exit-speed-header': '--',
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

// The backend DTO always reports speeds in m/s.
const telemetryDto = (speeds = {}) => ({
  throttle: 0.75,
  throttle_pct: 75,
  brake: 0.25,
  brake_pct: 25,
  is_brake_abs: true,
  gear: 3,
  speed_ms: 34.4,
  top_speed_ms: null,
  exit_speed_ms: null,
  ...speeds,
});

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

test('SpeedUnit converts m/s speeds and labels the readouts', async () => {
  const SpeedUnit = await import(SPEED_UNIT);

  assert.equal(SpeedUnit.DEFAULT_SPEED_UNIT, 'kmh');
  assert.equal(SpeedUnit.normalizeSpeedUnit('mph'), 'mph');
  assert.equal(SpeedUnit.normalizeSpeedUnit('bogus'), SpeedUnit.DEFAULT_SPEED_UNIT);
  assert.equal(SpeedUnit.speedUnitLabel('kmh'), 'KM/H');
  assert.equal(SpeedUnit.speedUnitLabel('mph'), 'MPH');

  assert.equal(SpeedUnit.toDisplaySpeed(10, 'kmh'), 36);
  assert.ok(Math.abs(SpeedUnit.toDisplaySpeed(10, 'mph') - 22.369356) < 1e-9);
  assert.equal(SpeedUnit.toDisplaySpeed(0, 'mph'), 0);
  // Missing speeds are passed through so they render as a placeholder.
  assert.equal(SpeedUnit.toDisplaySpeed(undefined, 'mph'), undefined);
  assert.equal(SpeedUnit.toDisplaySpeed(null, 'kmh'), null);
  assert.equal(SpeedUnit.toDisplaySpeed('not a number', 'mph'), 'not a number');
});

test('TelemetryRenderer renders readouts and records pedal history', async () => {
  const { TelemetryRenderer } = await import(TELEMETRY_RENDERER);
  const document = createTelemetryDocument();
  const renderer = new TelemetryRenderer(document, new FakeWindow());

  renderer.render(telemetryDto());

  assert.equal(renderer.speedUnit, 'kmh');
  assert.equal(document.getElementById('speed-unit-label').textContent, 'KM/H');
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
  const speeds = { top_speed_ms: 79.9, exit_speed_ms: 42.3 };

  renderer.render(telemetryDto(speeds));
  assert.equal(document.querySelector('#speed-header .speed-value').textContent, 124);
  assert.equal(document.getElementById('top-speed-header').textContent, 288);
  assert.equal(document.getElementById('exit-speed-header').textContent, 152);

  renderer.setSpeedUnit('mph');
  assert.equal(document.getElementById('speed-unit-label').textContent, 'MPH');
  assert.equal(document.querySelector('#speed-header .speed-value').textContent, 77);
  assert.equal(document.getElementById('top-speed-header').textContent, 179);
  assert.equal(document.getElementById('exit-speed-header').textContent, 95);

  renderer.render(telemetryDto(speeds));
  assert.equal(document.querySelector('#speed-header .speed-value').textContent, 77);
  assert.equal(document.getElementById('top-speed-header').textContent, 179);

  // Back to metric, and an unsupported unit falls back to the default.
  renderer.setSpeedUnit('kmh');
  assert.equal(document.getElementById('speed-unit-label').textContent, 'KM/H');
  assert.equal(document.querySelector('#speed-header .speed-value').textContent, 124);
  assert.equal(document.getElementById('top-speed-header').textContent, 288);

  renderer.setSpeedUnit('furlongs');
  assert.equal(renderer.speedUnit, 'kmh');
  assert.equal(document.getElementById('speed-unit-label').textContent, 'KM/H');
});

test('TelemetryRenderer refreshes latched speeds on a unit change without new data', async () => {
  const { TelemetryRenderer } = await import(TELEMETRY_RENDERER);
  const document = createTelemetryDocument();
  const renderer = new TelemetryRenderer(document, new FakeWindow());

  renderer.render(telemetryDto({ top_speed_ms: 79.9, exit_speed_ms: 42.3 }));

  // Record the raw m/s values used to redraw the latched readouts.
  const redrawn = [];
  const renderSpeedMetric = renderer.renderSpeedMetric.bind(renderer);
  renderer.renderSpeedMetric = (elementId, speedMs) => {
    redrawn.push([elementId, speedMs]);
    renderSpeedMetric(elementId, speedMs);
  };

  renderer.setSpeedUnit('mph');

  assert.deepEqual(redrawn, [
    ['top-speed-header', 79.9],
    ['exit-speed-header', 42.3],
  ]);
  assert.equal(document.getElementById('top-speed-header').textContent, 179);
  assert.equal(document.getElementById('exit-speed-header').textContent, 95);

  renderer.setSpeedUnit('kmh');
  assert.equal(document.getElementById('top-speed-header').textContent, 288);
  assert.equal(document.getElementById('exit-speed-header').textContent, 152);
});

test('A speed unit change refreshes latched readouts without another fetch', async () => {
  const { TelemetryRenderer } = await import(TELEMETRY_RENDERER);
  const { TelemetryUpdater } = await import(TELEMETRY_UPDATER);
  const document = createTelemetryDocument();
  const renderer = new TelemetryRenderer(document, new FakeWindow());
  const dto = telemetryDto({ top_speed_ms: 79.9, exit_speed_ms: 42.3 });
  let fetches = 0;
  let unitListener;

  const updater = new TelemetryUpdater(
    { getTelemetry: async () => { fetches += 1; return dto; } },
    renderer,
    {
      electronAPI: {
        getSpeedUnit: async () => 'kmh',
        onSpeedUnitUpdate: (listener) => { unitListener = listener; },
      },
      timer: { setInterval: () => {} },
    },
  );

  await updater.start();
  assert.equal(fetches, 1);
  assert.equal(document.getElementById('top-speed-header').textContent, 288);
  assert.equal(document.getElementById('exit-speed-header').textContent, 152);

  // The settings page pushed a new unit; the already latched values change
  // immediately, without waiting for the next 50 ms telemetry poll.
  unitListener('mph');
  assert.equal(fetches, 1);
  assert.equal(document.getElementById('speed-unit-label').textContent, 'MPH');
  assert.equal(document.getElementById('top-speed-header').textContent, 179);
  assert.equal(document.getElementById('exit-speed-header').textContent, 95);
  assert.equal(document.querySelector('#speed-header .speed-value').textContent, 77);
});

test('TelemetryRenderer shows latched top and exit speed', async () => {
  const { TelemetryRenderer } = await import(TELEMETRY_RENDERER);
  const document = createTelemetryDocument();
  const renderer = new TelemetryRenderer(document, new FakeWindow());

  renderer.render(telemetryDto({ speed_ms: 55.94, top_speed_ms: 79.9, exit_speed_ms: 42.3 }));

  assert.equal(document.getElementById('top-speed-header').textContent, 288);
  assert.equal(document.getElementById('exit-speed-header').textContent, 152);

  // Values are cleared back to the placeholder until they are latched again.
  renderer.renderSpeedMetric('top-speed-header', null);
  renderer.renderSpeedMetric('exit-speed-header', undefined);
  assert.equal(document.getElementById('top-speed-header').textContent, '--');
  assert.equal(document.getElementById('exit-speed-header').textContent, '--');
});

test('TelemetryRenderer keeps speed placeholders for missing or invalid values', async () => {
  const { TelemetryRenderer } = await import(TELEMETRY_RENDERER);
  const document = createTelemetryDocument();
  const renderer = new TelemetryRenderer(document, new FakeWindow());

  renderer.render(telemetryDto({
    speed_ms: undefined,
    top_speed_ms: null,
    exit_speed_ms: NaN,
  }));

  assert.equal(document.querySelector('#speed-header .speed-value').textContent, '--');
  assert.equal(document.getElementById('top-speed-header').textContent, '--');
  assert.equal(document.getElementById('exit-speed-header').textContent, '--');

  // Switching units must not turn an unavailable value into a number.
  renderer.setSpeedUnit('mph');
  assert.equal(document.querySelector('#speed-header .speed-value').textContent, '--');
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

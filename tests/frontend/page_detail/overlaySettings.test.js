const test = require('node:test');
const assert = require('node:assert/strict');

const { FakeDocument } = require('../helpers/dom');
const { createSettingsApiStub } = require('../helpers/settings_api');

const PAGE_DETAIL = '../../../frontend/static/js/page_detail/index.js';

const DISPLAY_BUTTONS = ['DisplayAllTimeBtn', 'DisplayTrackBtn', 'DisplayGarageBtn'];
const AUTO_START_BUTTONS = ['AutoStartOnBtn', 'AutoStartOffBtn'];
const RADAR_BUTTONS = ['dimBtn', 'showBtn', 'hideBtn'];
const SPEED_UNIT_BUTTONS = ['kmhBtn', 'mphBtn'];

const activeIds = (document, ids) =>
  ids.filter((id) => document.getElementById(id).classList.contains('active'));

// Markup shared by every detail page (pages/card_detail/base_detail.html).
function createDetailPageDocument(elements = {}) {
  return new FakeDocument({
    OpenBtn: 'button primary-btn',
    ToggleMovementBtn: '',
    zoomRange: '',
    zoomValue: '',
    DisplayAllTimeBtn: 'active',
    DisplayTrackBtn: '',
    DisplayGarageBtn: '',
    AutoStartOnBtn: '',
    AutoStartOffBtn: 'active',
    ...elements,
  });
}

test('overlaySettings applies the settings loaded from the api to the mounted controls', async () => {
  const { mountOverlaySettings, createRadarVisibilitySetting } = await import(PAGE_DETAIL);
  const document = createDetailPageDocument({ dimBtn: '', showBtn: '', hideBtn: '' });
  const api = createSettingsApiStub({
    getZoom: 1.5,
    getDisplayMode: 'garage',
    getAutoStartMode: 'on',
    getMovementState: true,
    getRadarVisibility: 'dim',
  });

  await mountOverlaySettings({
    overlayName: 'radar',
    settings: [createRadarVisibilitySetting],
    document,
    api,
  });

  assert.equal(document.getElementById('zoomRange').value, '150');
  assert.equal(document.getElementById('zoomValue').textContent, '150%');
  assert.deepEqual(activeIds(document, DISPLAY_BUTTONS), ['DisplayGarageBtn']);
  assert.deepEqual(activeIds(document, AUTO_START_BUTTONS), ['AutoStartOnBtn']);
  assert.deepEqual(activeIds(document, RADAR_BUTTONS), ['dimBtn']);

  const movementButton = document.getElementById('ToggleMovementBtn');
  assert.equal(movementButton.classList.contains('primary-btn'), true);
  assert.match(movementButton.innerHTML, /lock_open_right/);
});

test('overlaySettings sends user changes of the mounted settings to the api', async () => {
  const { mountOverlaySettings, createRadarVisibilitySetting } = await import(PAGE_DETAIL);
  const document = createDetailPageDocument({ dimBtn: '', showBtn: '', hideBtn: '' });
  const api = createSettingsApiStub({
    getZoom: 1,
    getDisplayMode: 'all_time',
    getAutoStartMode: 'off',
    getRadarVisibility: 'dim',
  });

  await mountOverlaySettings({
    overlayName: 'radar',
    settings: [createRadarVisibilitySetting],
    document,
    api,
  });
  api.calls.length = 0; // ignore the initial loads

  document.getElementById('zoomRange').setValue('200');
  assert.deepEqual(api.lastCall('setZoom'), ['radar', 2]);

  document.getElementById('DisplayTrackBtn').click();
  assert.deepEqual(api.lastCall('setDisplayMode'), ['radar', 'track']);
  assert.deepEqual(activeIds(document, DISPLAY_BUTTONS), ['DisplayTrackBtn']);

  document.getElementById('AutoStartOnBtn').click();
  assert.deepEqual(api.lastCall('setAutoStartMode'), ['radar', 'on']);

  document.getElementById('hideBtn').click();
  assert.deepEqual(api.lastCall('setRadarVisibility'), ['radar', 'hide']);
  assert.deepEqual(activeIds(document, RADAR_BUTTONS), ['hideBtn']);

  document.getElementById('OpenBtn').click();
  assert.deepEqual(api.lastCall('openOverlay'), ['radar']);

  // Movement state changed elsewhere (hotkey or another page).
  api.trigger('onMovementStateChange', true);
  assert.match(document.getElementById('ToggleMovementBtn').innerHTML, /lock_open_right/);

  document.getElementById('ToggleMovementBtn').click();
  assert.deepEqual(api.lastCall('toggleMovementState'), []);
});

test('overlaySettings logs a failing setting without breaking the rest of the page', async () => {
  const { mountOverlaySettings, createRadarVisibilitySetting } = await import(PAGE_DETAIL);
  const document = createDetailPageDocument({ dimBtn: '', showBtn: '', hideBtn: '' });
  const api = createSettingsApiStub({ getZoom: 1, getRadarVisibility: 'dim' });
  const logged = [];
  const consoleError = console.error;
  console.error = (message) => logged.push(message);

  try {
    await mountOverlaySettings({
      overlayName: 'radar',
      settings: [
        () => ({ mount: async () => { throw new Error('broken setting'); } }),
        createRadarVisibilitySetting,
      ],
      document,
      api,
    });
  } finally {
    console.error = consoleError;
  }

  assert.equal(logged.length, 1);
  // The remaining settings still mounted.
  assert.equal(document.getElementById('zoomValue').textContent, '100%');
  assert.deepEqual(activeIds(document, RADAR_BUTTONS), ['dimBtn']);
});

test('overlaySettings loads and saves the telemetry speed unit', async () => {
  const { mountOverlaySettings, createSpeedUnitSetting } = await import(PAGE_DETAIL);
  const document = createDetailPageDocument({ kmhBtn: '', mphBtn: '' });
  const api = createSettingsApiStub({
    getZoom: 1,
    getDisplayMode: 'all_time',
    getAutoStartMode: 'off',
    getSpeedUnit: 'mph',
  });

  await mountOverlaySettings({
    overlayName: 'telemetry',
    settings: [createSpeedUnitSetting],
    document,
    api,
  });

  assert.deepEqual(activeIds(document, SPEED_UNIT_BUTTONS), ['mphBtn']);

  api.calls.length = 0; // ignore the initial loads
  document.getElementById('kmhBtn').click();

  assert.deepEqual(api.lastCall('setSpeedUnit'), ['telemetry', 'kmh']);
  assert.deepEqual(activeIds(document, SPEED_UNIT_BUTTONS), ['kmhBtn']);
});

test('overlaySettings speed unit keeps the HTML default when the api has no value', async () => {
  const { mountOverlaySettings, createSpeedUnitSetting } = await import(PAGE_DETAIL);
  const document = createDetailPageDocument({ kmhBtn: 'active', mphBtn: '' });

  await mountOverlaySettings({
    overlayName: 'telemetry',
    settings: [createSpeedUnitSetting],
    document,
    api: createSettingsApiStub(),
  });

  assert.deepEqual(activeIds(document, SPEED_UNIT_BUTTONS), ['kmhBtn']);
});

test('overlaySettings zoom keeps the HTML defaults when the api has no zoom value', async () => {
  const { createZoomSetting } = await import(
    '../../../frontend/static/js/page_detail/features/shared/zoomSetting.js'
  );
  const document = createDetailPageDocument();
  const range = document.getElementById('zoomRange');
  const value = document.getElementById('zoomValue');
  range.value = '100'; // defaults rendered by the template
  value.textContent = '100%';

  await createZoomSetting({ api: createSettingsApiStub(), overlayName: 'radar', document }).mount();

  assert.equal(range.value, '100');
  assert.equal(value.textContent, '100%');
});

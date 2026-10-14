const test = require('node:test');
const assert = require('node:assert/strict');

const { FakeDocument } = require('../helpers/dom');
const { describeApiContract } = require('../helpers/api_contract');

const RADAR_API = '../../../frontend/overlays/radar/radarApi.js';
const RADAR_UPDATER = '../../../frontend/overlays/radar/radarUpdater.js';
const RADAR_RENDERER = '../../../frontend/overlays/radar/radarRenderer.js';
const BASE_UPDATER = '../../../frontend/overlays/shared/baseUpdater.js';

describeApiContract({
  title: 'RadarApi',
  loadApi: async () => (await import(RADAR_API)).RadarApi,
  method: 'getRadar',
  endpoint: '/api/radar',
});

// Radar overlay markup: container plus the ahead/behind and side indicators.
function createRadarDocument() {
  return new FakeDocument({
    radar: 'radar-container overlay-bg-opacity-target',
    'fb-ahead': 'fb-box ahead',
    'fb-behind': 'fb-box behind',
    'side-left': 'side-box left',
    'side-right': 'side-box right',
  })
    .registerSelector('.radar-container', 'radar')
    .registerSelector('.overlay-bg-opacity-target', 'radar');
}

const noCarsNearby = () => ({
  ahead_m: null,
  behind_m: null,
  ahead_nearby: false,
  behind_nearby: false,
  left: null,
  right: null,
});

test('RadarUpdater delegates loading and radar visibility settings', async () => {
  const { BaseUpdater } = await import(BASE_UPDATER);
  const { RadarUpdater } = await import(RADAR_UPDATER);
  const dto = { status: 'ok' };
  const modes = [];
  let visibilityListener;

  const updater = new RadarUpdater(
    { getRadar: async () => dto },
    { setRadarMode: (mode) => modes.push(mode) },
    {
      electronAPI: {
        getRadarVisibility: async () => 'hide',
        onRadarVisibilityUpdate: (listener) => { visibilityListener = listener; },
      },
    },
  );

  assert.ok(updater instanceof BaseUpdater);
  assert.equal(await updater.getDto(), dto);

  await updater.initFeature();
  visibilityListener('show');
  assert.deepEqual(modes, ['hide', 'show']);
});

test('RadarRenderer keeps indicator state, positions and reappearance', async () => {
  const { RadarRenderer } = await import(RADAR_RENDERER);
  const document = createRadarDocument();
  const renderer = new RadarRenderer(document);

  renderer.render({
    ahead_m: 2,
    ahead_severity: 'red',
    behind_m: null,
    behind_severity: 'none',
    ahead_nearby: true,
    behind_nearby: false,
    left: { offset_ratio: 1 },
    right: null,
  });

  assert.equal(document.getElementById('fb-ahead').style.opacity, 1);
  assert.ok(document.getElementById('fb-ahead').classList.contains('sev-red'));
  assert.equal(document.getElementById('fb-behind').style.opacity, 0);
  assert.equal(document.getElementById('side-left').style.top, '-40px');
  assert.equal(document.getElementById('side-right'), null);

  const previousLeft = document.getElementById('side-left');
  renderer.render(noCarsNearby());
  assert.equal(document.getElementById('side-left'), null);

  // Indicators on both sides sit at the same height and the left one is
  // rebuilt, so it cannot glide in from its previous position.
  renderer.render({ ...noCarsNearby(), left: { offset_ratio: -1 }, right: { offset_ratio: 1 } });
  assert.notEqual(document.getElementById('side-left'), previousLeft);
  assert.equal(document.getElementById('side-left').style.top, '70px');
  assert.equal(document.getElementById('side-right').style.top, '70px');
});

test('RadarRenderer applies dim, hide and show visibility', async () => {
  const { RadarRenderer } = await import(RADAR_RENDERER);
  const document = createRadarDocument();
  const renderer = new RadarRenderer(document);
  const container = document.getElementById('radar');

  // Without a mode the radar dims when no cars are nearby.
  renderer.render(noCarsNearby());
  assert.equal(container.style.opacity, 0.35);

  renderer.setRadarMode('hide');
  renderer.render(noCarsNearby());
  assert.equal(container.style.opacity, 0);
  assert.equal(container.style.pointerEvents, 'none');

  renderer.setRadarMode('show');
  renderer.render(noCarsNearby());
  assert.equal(container.style.opacity, 1);

  renderer.setVisible(false);
  assert.equal(document.body.style.visibility, 'hidden');
});

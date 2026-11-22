const test = require('node:test');
const assert = require('node:assert/strict');

const { FakeDocument } = require('../helpers/dom');
const { describeApiContract } = require('../helpers/api_contract');
const { BASE_UPDATER } = require('../helpers/modules');

const TRACK_MAP_API = '../../../frontend/overlays/track-map/track-mapApi.js';
const TRACK_MAP_UPDATER = '../../../frontend/overlays/track-map/track-mapUpdater.js';
const TRACK_MAP_RENDERER = '../../../frontend/overlays/track-map/track-mapRenderer.js';

describeApiContract({
  title: 'TrackMapApi',
  loadApi: async () => (await import(TRACK_MAP_API)).TrackMapApi,
  method: 'getTrackMap',
  endpoint: '/api/track-map',
});

// Track-map overlay markup: the map container and the track line.
function createTrackMapDocument() {
  const document = new FakeDocument({ 'track-container': '', 'track-line': '' });
  document.getElementById('track-container').rect = { width: 300, height: 100, left: 0, top: 0 };
  return document;
}

test('TrackMapUpdater delegates loading and track type settings', async () => {
  const { BaseUpdater } = await import(BASE_UPDATER);
  const { TrackMapUpdater } = await import(TRACK_MAP_UPDATER);
  const dto = { status: 'ok' };
  const types = [];
  let typeListener;

  const updater = new TrackMapUpdater(
    { getTrackMap: async () => dto },
    { setTrackType: (type) => types.push(type) },
    {
      electronAPI: {
        getTrackType: async () => 'circle',
        onTrackTypeUpdate: (listener) => { typeListener = listener; },
      },
    },
  );

  assert.ok(updater instanceof BaseUpdater);
  assert.equal(await updater.getDto(), dto);

  await updater.initFeature();
  typeListener('linear');
  assert.deepEqual(types, ['circle', 'linear']);
});

// The SVG drawn into #track-line by the last layout.
function getTrackSvg(document) {
  return document.getElementById('track-line').children[0];
}

test('TrackMapRenderer draws the synthetic layouts as SVG', async () => {
  const { TrackMapRenderer } = await import(TRACK_MAP_RENDERER);
  const document = createTrackMapDocument();
  const renderer = new TrackMapRenderer(document);
  const trackLine = document.getElementById('track-line');

  renderer.setTrackType('circle');
  assert.equal(document.body.dataset.trackType, 'circle');
  assert.equal(document.getElementById('track-container').style.aspectRatio, '100 / 100');
  assert.ok(trackLine.classList.contains('circle'));

  // Outline, surface and the 2x5 start/finish grid.
  const [outer, surface, startFinish] = getTrackSvg(document).children;
  assert.ok(outer.classList.contains('outer'));
  assert.ok(surface.classList.contains('surface'));
  assert.ok(startFinish.classList.contains('track-start-finish'));
  assert.equal(startFinish.children.length, 10);

  // Switching the type replaces the previous drawing.
  renderer.setTrackType('linear');
  assert.equal(trackLine.children.length, 1);
  assert.ok(trackLine.classList.contains('linear'));
  assert.ok(!trackLine.classList.contains('circle'));
  assert.equal(getTrackSvg(document).getAttribute('viewBox'), '0 0 300 75');
});

test('TrackMapRenderer fits the real track to its points', async () => {
  const { TrackMapRenderer } = await import(TRACK_MAP_RENDERER);
  const document = createTrackMapDocument();
  const renderer = new TrackMapRenderer(document);

  // Nothing to draw until the backend sends the geometry.
  renderer.setTrackType('track');
  assert.equal(document.getElementById('track-line').children.length, 0);

  renderer.render({
    status: 'ok',
    cars: [],
    track: {
      id: 145,
      points: [[10, 20], [110, 20], [110, 70]],
      start_finish: { pct: 0, direction: 1 },
    },
  });

  assert.equal(getTrackSvg(document).getAttribute('viewBox'), '10 20 100 50');
  assert.equal(document.getElementById('track-container').style.aspectRatio, '');
});

test('TrackMapRenderer positions cars and removes them when they leave the track', async () => {
  const { TrackMapRenderer } = await import(TRACK_MAP_RENDERER);
  const document = createTrackMapDocument();
  const renderer = new TrackMapRenderer(document);

  renderer.setTrackType('linear');
  renderer.render({
    status: 'ok',
    player_id: 7,
    cars: [{ player_id: 7, car_number: '07', color: '#f00', lap_dist_pct: 0.5 }],
  });

  // Half a lap is the middle of the line; the 300x75 view box is centered
  // vertically in the 300x100 container.
  const car = renderer.cars[7];
  assert.equal(car.textContent, '07');
  assert.ok(car.classList.contains('player'));
  assert.equal(car.style.transform, 'translate3d(150px, 50px, 0) translate(-50%, -50%)');

  renderer.render({ status: 'ok', player_id: 7, cars: [{ player_id: 7, lap_dist_pct: -1 }] });
  assert.equal(renderer.cars[7], undefined);
  assert.equal(car.removed, true);
});

test('TrackMapRenderer styles cars by class only in multiclass sessions', async () => {
  const { TrackMapRenderer } = await import(TRACK_MAP_RENDERER);
  const document = createTrackMapDocument();
  const renderer = new TrackMapRenderer(document);
  const cars = [
    { player_id: 1, car_number: '1', class_id: 10, color: '#ffda59', lap_dist_pct: 0.1 },
    { player_id: 2, car_number: '2', class_id: 20, color: '#000080', lap_dist_pct: 0.2 },
  ];

  renderer.setTrackType('circle');
  renderer.render({ status: 'ok', multiclass: true, cars });

  const [light, dark] = [renderer.cars[1], renderer.cars[2]];
  assert.equal(light.style['--car-color'], '#ffda59');
  assert.equal(light.dataset.shape, 'circle');
  assert.equal(dark.dataset.shape, 'square');

  // White number on a dark class color, the default dark number otherwise.
  assert.ok(!light.classList.contains('dark-color'));
  assert.ok(dark.classList.contains('dark-color'));

  // A single-class session falls back to the default color and shape.
  renderer.render({ status: 'ok', multiclass: false, cars });
  assert.equal(dark.style['--car-color'], undefined);
  assert.equal(dark.dataset.shape, 'circle');
  assert.ok(!dark.classList.contains('dark-color'));
});

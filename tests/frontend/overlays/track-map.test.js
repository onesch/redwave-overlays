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

test('TrackMapRenderer switches layouts and tracks the car lifecycle', async () => {
  const { TrackMapRenderer } = await import(TRACK_MAP_RENDERER);
  const document = createTrackMapDocument();
  const renderer = new TrackMapRenderer(document);

  renderer.setTrackType('circle');
  assert.equal(document.body.dataset.trackType, 'circle');
  assert.equal(document.getElementById('track-container').style.aspectRatio, '1 / 1');
  assert.ok(document.getElementById('track-line').classList.contains('circle'));
  assert.equal(document.getElementById('track-line').children[0].className, 'track-finish-line');

  renderer.render({
    status: 'ok',
    player_id: 7,
    cars: [{ player_id: 7, car_number: '07', color: '#f00', lap_dist_pct: 0.25 }],
  });

  const car = renderer.cars[7];
  assert.equal(car.innerText, '07');
  assert.ok(car.classList.contains('player'));
  assert.equal(car.style.left, '185px');
  assert.equal(car.style.top, '50px');

  // Cars that left the track are removed again.
  renderer.render({ status: 'ok', player_id: 7, cars: [{ player_id: 7, lap_dist_pct: -1 }] });
  assert.equal(renderer.cars[7], undefined);
  assert.equal(car.removed, true);
});

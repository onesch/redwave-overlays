const test = require('node:test');
const assert = require('node:assert/strict');

test('TrackMapApi uses the track map endpoint and validates responses', async () => {
  const { TrackMapApi } = await import(
    '../../../frontend/overlays/track-map/track-mapApi.js'
  );
  const dto = { status: 'ok', cars: [] };
  const requested = [];
  const api = new TrackMapApi(undefined, async (endpoint) => {
    requested.push(endpoint);
    return { ok: true, json: async () => dto };
  });

  assert.equal(await api.getTrackMap(), dto);
  assert.deepEqual(requested, ['/api/track-map']);

  const failingApi = new TrackMapApi('/api/track-map', async () => ({
    ok: false,
    status: 503,
  }));
  await assert.rejects(failingApi.getTrackMap(), /Failed to fetch track map: 503/);
});

test('TrackMapUpdater delegates loading and track type settings', async () => {
  const { BaseUpdater } = await import('../../../frontend/overlays/shared/baseUpdater.js');
  const { TrackMapUpdater } = await import(
    '../../../frontend/overlays/track-map/track-mapUpdater.js'
  );
  const dto = { status: 'ok', cars: [] };
  const types = [];
  let typeListener;
  const updater = new TrackMapUpdater(
    { getTrackMap: async () => dto },
    { setTrackType: (type) => types.push(type) },
    {
      electronAPI: {
        getTrackType: async (name) => name === 'track-map' ? 'circle' : null,
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

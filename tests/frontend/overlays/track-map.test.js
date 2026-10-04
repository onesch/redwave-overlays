const test = require('node:test');
const assert = require('node:assert/strict');

class FakeClassList {
  constructor() { this.names = new Set(); }
  add(...names) { names.forEach((name) => this.names.add(name)); }
  remove(...names) { names.forEach((name) => this.names.delete(name)); }
  contains(name) { return this.names.has(name); }
}

class FakeElement {
  constructor() {
    this.children = [];
    this.classList = new FakeClassList();
    this.dataset = {};
    this.innerHTML = '';
    this.innerText = '';
    this.style = { setProperty: (name, value) => { this.style[name] = value; } };
  }
  appendChild(child) { this.children.push(child); child.parentNode = this; }
  remove() { this.removed = true; }
  getBoundingClientRect() { return { width: 300, height: 100, left: 0, top: 0 }; }
  querySelector() { return null; }
}

class FakeDocument {
  constructor() {
    this.body = new FakeElement();
    this.overlayBody = new FakeElement();
    this.trackContainer = new FakeElement();
    this.trackLine = new FakeElement();
  }
  getElementById(id) {
    if (id === 'track-container') return this.trackContainer;
    if (id === 'track-line') return this.trackLine;
    return null;
  }
  createElement() { return new FakeElement(); }
  querySelector(selector) {
    if (selector === '.overlay-body') return this.overlayBody;
    return null;
  }
}

test('TrackMapApi requests /api/track-map and returns the DTO unchanged', async () => {
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
});

test('TrackMapApi reports non-success responses', async () => {
  const { TrackMapApi } = await import(
    '../../../frontend/overlays/track-map/track-mapApi.js'
  );
  const api = new TrackMapApi(undefined, async () => ({ ok: false, status: 503 }));
  await assert.rejects(api.getTrackMap(), /Failed to fetch track map: 503/);
});

test('TrackMapUpdater delegates loading and track type settings', async () => {
  const { BaseUpdater } = await import('../../../frontend/overlays/shared/baseUpdater.js');
  const { TrackMapUpdater } = await import(
    '../../../frontend/overlays/track-map/track-mapUpdater.js'
  );
  const dto = { status: 'ok' };
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

test('TrackMapRenderer preserves geometric layouts and car lifecycle', async () => {
  const { TrackMapRenderer } = await import(
    '../../../frontend/overlays/track-map/track-mapRenderer.js'
  );
  const document = new FakeDocument();
  const renderer = new TrackMapRenderer(document);

  renderer.setTrackType('circle');
  assert.equal(document.body.dataset.trackType, 'circle');
  assert.equal(document.trackContainer.style.aspectRatio, '1 / 1');
  assert.ok(document.trackLine.classList.contains('circle'));
  assert.equal(document.trackLine.children[0].className, 'track-finish-line');

  renderer.render({ status: 'ok', cars: [{
    player_id: 7, car_number: '07', color: '#f00', lap_dist_pct: 0.25,
  }], player_id: 7 });
  const car = renderer.cars[7];
  assert.equal(car.innerText, '07');
  assert.ok(car.classList.contains('player'));
  assert.equal(car.style.left, '185px');
  assert.equal(car.style.top, '50px');

  renderer.render({ status: 'ok', cars: [{ player_id: 7, lap_dist_pct: -1 }], player_id: 7 });
  assert.equal(renderer.cars[7], undefined);
  assert.equal(car.removed, true);
});

const test = require('node:test');
const assert = require('node:assert/strict');

class FakeClassList {
  constructor(names = '') {
    this.names = new Set(names.split(/\s+/).filter(Boolean));
  }

  add(...names) { names.forEach((name) => this.names.add(name)); }
  remove(...names) { names.forEach((name) => this.names.delete(name)); }
  contains(name) { return this.names.has(name); }
}

class FakeElement {
  constructor(document, id = '', className = '') {
    this.document = document;
    this.id = id;
    this.style = { setProperty: (name, value) => { this.style[name] = value; } };
    this.children = [];
    this.className = className;
  }

  set className(value) {
    this._className = value;
    this.classList = new FakeClassList(value);
  }

  get className() { return this._className; }

  appendChild(child) {
    this.children.push(child);
    this.document.elements.set(child.id, child);
  }

  remove() {
    this.document.elements.delete(this.id);
  }
}

class FakeDocument {
  constructor() {
    this.elements = new Map();
    this.overlayBody = this.add('overlay-body', 'overlay-body');
    this.container = this.add('radar', 'radar-container overlay-bg-opacity-target');
    this.add('fb-ahead', 'fb-box ahead');
    this.add('fb-behind', 'fb-box behind');
    this.add('side-left', 'side-box left');
    this.add('side-right', 'side-box right');
  }

  add(id, className) {
    const element = new FakeElement(this, id, className);
    this.elements.set(id, element);
    return element;
  }

  getElementById(id) { return this.elements.get(id) ?? null; }
  createElement() { return new FakeElement(this); }
  querySelector(selector) {
    if (selector === '.overlay-body') return this.overlayBody;
    if (selector === '.radar-container' || selector === '.overlay-bg-opacity-target') {
      return this.container;
    }
    return null;
  }
}

test('RadarApi requests /api/radar and returns the DTO unchanged', async () => {
  const { RadarApi } = await import('../../../frontend/overlays/radar/radarApi.js');
  const dto = { status: 'ok', ahead_m: 3 };
  const requested = [];
  const api = new RadarApi(undefined, async (endpoint) => {
    requested.push(endpoint);
    return { ok: true, json: async () => dto };
  });

  assert.equal(await api.getRadar(), dto);
  assert.deepEqual(requested, ['/api/radar']);
});

test('RadarApi reports non-success responses', async () => {
  const { RadarApi } = await import('../../../frontend/overlays/radar/radarApi.js');
  const api = new RadarApi('/api/radar', async () => ({ ok: false, status: 503 }));

  await assert.rejects(api.getRadar(), /Failed to fetch radar: 503/);
});

test('RadarUpdater delegates DTO loading and radar visibility settings', async () => {
  const { BaseUpdater } = await import('../../../frontend/overlays/shared/baseUpdater.js');
  const { RadarUpdater } = await import('../../../frontend/overlays/radar/radarUpdater.js');
  const dto = { status: 'ok' };
  const modes = [];
  let visibilityListener;
  const updater = new RadarUpdater(
    { getRadar: async () => dto },
    { setRadarMode: (mode) => modes.push(mode) },
    {
      electronAPI: {
        getRadarVisibility: async (name) => name === 'radar' ? 'hide' : null,
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

test('RadarRenderer preserves indicator state, positioning, and reappearance behavior', async () => {
  const { RadarRenderer } = await import('../../../frontend/overlays/radar/radarRenderer.js');
  const document = new FakeDocument();
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

  const oldLeft = document.getElementById('side-left');
  renderer.render({
    ahead_m: null,
    behind_m: null,
    ahead_nearby: false,
    behind_nearby: false,
    left: null,
    right: null,
  });
  assert.equal(document.getElementById('side-left'), null);

  renderer.render({
    ahead_m: null,
    behind_m: null,
    ahead_nearby: false,
    behind_nearby: false,
    left: { offset_ratio: -1 },
    right: { offset_ratio: 1 },
  });
  assert.notEqual(document.getElementById('side-left'), oldLeft);
  assert.equal(document.getElementById('side-left').style.top, '70px');
  assert.equal(document.getElementById('side-right').style.top, '70px');
});

test('RadarRenderer applies hide, dim, and shared visibility states', async () => {
  const { RadarRenderer } = await import(
    '../../../frontend/overlays/radar/radarRenderer.js'
  );

  const document = new FakeDocument();
  const renderer = new RadarRenderer(document);

  const empty = {
    ahead_m: null,
    behind_m: null,
    ahead_nearby: false,
    behind_nearby: false,
    left: null,
    right: null,
  };

  renderer.render(empty);
  assert.equal(document.container.style.opacity, 0.35);

  renderer.setRadarMode('hide');
  renderer.render(empty);

  assert.equal(document.container.style.opacity, 0);
  assert.equal(document.container.style.pointerEvents, 'none');

  renderer.setVisible(false);
  assert.equal(document.overlayBody.style.visibility, 'hidden');
});

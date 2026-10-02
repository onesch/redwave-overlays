const test = require('node:test');
const assert = require('node:assert/strict');

class FakeElement {
  constructor(id = '') {
    this.id = id;
    this.textContent = '';
    this.style = {};
    this.parentElement = {
      getBoundingClientRect: () => ({
        width: 200,
        height: 100,
      }),
    };
  }
}

class FakeCanvas extends FakeElement {
  getContext() {
    return {
      setTransform() {},
      clearRect() {},
      beginPath() {},
      moveTo() {},
      lineTo() {},
      stroke() {},
    };
  }
}

class FakeDocument {
  constructor() {
    this.documentElement = {};

    this.elements = new Map([
      ['telemetry-canvas', new FakeCanvas('telemetry-canvas')],
      ['gear-header', new FakeElement('gear-header')],
      ['speed-header', new FakeElement('speed-header')],

      ['throttle-pct-header', new FakeElement('throttle-pct-header')],
      ['throttle-fill-peak', new FakeElement('throttle-fill-peak')],
      ['throttle-fill-mid', new FakeElement('throttle-fill-mid')],
      ['throttle-fill-dead', new FakeElement('throttle-fill-dead')],

      ['brake-pct-header', new FakeElement('brake-pct-header')],
      ['brake-fill-peak', new FakeElement('brake-fill-peak')],
      ['brake-fill-mid', new FakeElement('brake-fill-mid')],
      ['brake-fill-dead', new FakeElement('brake-fill-dead')],
    ]);
  }

  getElementById(id) {
    return this.elements.get(id) ?? null;
  }
}

class FakeWindow {
  constructor() {
    this.devicePixelRatio = 1;
  }

  getComputedStyle() {
    return {
      getPropertyValue() {
        return '#fff';
      },
    };
  }

  addEventListener() {}
}

test('TelemetryApi requests /api/telemetry and returns the DTO unchanged', async () => {
  const { TelemetryApi } = await import(
    '../../../frontend/overlays/telemetry/telemetryApi.js'
  );

  const dto = {
    status: 'ok',
    throttle: 0.5,
  };

  let requestedEndpoint;

  const api = new TelemetryApi(undefined, async (endpoint) => {
    requestedEndpoint = endpoint;

    return {
      ok: true,
      json: async () => dto,
    };
  });

  assert.equal(await api.getTelemetry(), dto);
  assert.equal(requestedEndpoint, '/api/telemetry');
});

test('TelemetryApi rejects non-success responses', async () => {
  const { TelemetryApi } = await import(
    '../../../frontend/overlays/telemetry/telemetryApi.js'
  );

  const api = new TelemetryApi('/api/telemetry', async () => ({
    ok: false,
    status: 500,
  }));

  await assert.rejects(
    api.getTelemetry(),
    /Failed to fetch telemetry: 500/,
  );
});

test('TelemetryUpdater preserves telemetry configuration and delegates loading', async () => {
  const { BaseUpdater } = await import(
    '../../../frontend/overlays/shared/baseUpdater.js'
  );

  const { TelemetryUpdater } = await import(
    '../../../frontend/overlays/telemetry/telemetryUpdater.js'
  );

  const dto = { status: 'ok' };

  const updater = new TelemetryUpdater(
    {
      getTelemetry: async () => dto,
    },
    {},
    {
      electronAPI: {},
    },
  );

  assert.ok(updater instanceof BaseUpdater);
  assert.equal(updater.overlayName, 'telemetry');
  assert.equal(updater.updateInterval, 50);
  assert.equal(await updater.getDto(), dto);
});

test('TelemetryRenderer renders telemetry values and updates history', async () => {
  const { TelemetryRenderer } = await import(
    '../../../frontend/overlays/telemetry/telemetryRenderer.js'
  );

  const document = new FakeDocument();
  const renderer = new TelemetryRenderer(
    document,
    new FakeWindow(),
  );

  renderer.render({
    throttle: 0.75,
    throttle_pct: 75,
    brake: 0.25,
    brake_pct: 25,
    is_brake_abs: true,
    gear: 3,
    speed_km: 123.6,
  });

  assert.equal(
    document.getElementById('gear-header').textContent,
    '3',
  );

  assert.equal(
    document.getElementById('speed-header').textContent,
    124,
  );

  assert.equal(
    document.getElementById('throttle-pct-header').textContent,
    '75',
  );

  assert.equal(
    document.getElementById('brake-pct-header').textContent,
    '25',
  );

  assert.equal(renderer.thrHistory.at(-1), 0.75);
  assert.equal(renderer.brkHistory.at(-1), 0.25);
  assert.equal(renderer.brkAbsHistory.at(-1), true);

  assert.equal(renderer.thrHistory.length, 200);
  assert.equal(renderer.brkHistory.length, 200);
});

test('TelemetryRenderer normalizes invalid pedal values and renders full pedal state', async () => {
  const { TelemetryRenderer } = await import(
    '../../../frontend/overlays/telemetry/telemetryRenderer.js'
  );

  const document = new FakeDocument();
  const renderer = new TelemetryRenderer(
    document,
    new FakeWindow(),
  );

  renderer.renderPedal('throttle', 1, 100);

  assert.equal(
    document.getElementById('throttle-pct-header').textContent,
    'FL',
  );

  assert.equal(
    document.getElementById('throttle-fill-peak').style.height,
    '100%',
  );

  renderer.renderPedal('brake', -10, undefined);

  assert.equal(
    document.getElementById('brake-pct-header').textContent,
    '0',
  );

  assert.equal(
    document.getElementById('brake-fill-dead').style.height,
    '0%',
  );
});

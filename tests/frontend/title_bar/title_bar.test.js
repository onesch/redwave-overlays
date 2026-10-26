const test = require('node:test');
const assert = require('node:assert/strict');

const { FakeDocument } = require('../helpers/dom');

const TITLE_BAR = '../../../frontend/static/js/title_bar.js';

// Markup of the title bar (frontend/templates/base/base.html).
function createTitleBarDocument() {
  return new FakeDocument({
    'title-bar': 'title-bar',
    'title-bar-minimize': 'title-bar-button',
    'title-bar-close': 'title-bar-button title-bar-button--close',
  });
}

// Recording stub of the window controls the preload bridge exposes.
function createElectronApiStub() {
  const calls = [];
  const record = (name) => () => calls.push(name);

  return {
    calls,
    minimizeWindow: record('minimizeWindow'),
    closeWindow: record('closeWindow'),
    startWindowDrag: record('startWindowDrag'),
    dragWindow: record('dragWindow'),
    endWindowDrag: record('endWindowDrag'),
  };
}

test('Title bar buttons minimize and close the window through the preload api', async () => {
  const { mountTitleBar } = await import(TITLE_BAR);
  const document = createTitleBarDocument();
  const electronAPI = createElectronApiStub();

  mountTitleBar({ document, electronAPI });
  document.getElementById('title-bar-minimize').click();
  document.getElementById('title-bar-close').click();

  assert.deepEqual(electronAPI.calls, ['minimizeWindow', 'closeWindow']);
});

test('Title bar window controls forward every call and tolerate a missing preload api', async (t) => {
  const { createWindowControls } = await import(TITLE_BAR);
  const electronAPI = createElectronApiStub();
  const controls = createWindowControls(electronAPI);

  controls.minimize();
  controls.close();
  controls.startDrag();
  controls.drag();
  controls.endDrag();

  assert.deepEqual(electronAPI.calls, [
    'minimizeWindow',
    'closeWindow',
    'startWindowDrag',
    'dragWindow',
    'endWindowDrag',
  ]);

  // A partial api leaves the missing controls as no-ops.
  assert.doesNotThrow(() => createWindowControls({}).minimize());

  // Without Electron the controls warn once and still do not throw.
  const warned = [];
  const originalWarn = console.warn;
  console.warn = (...args) => warned.push(args);
  t.after(() => { console.warn = originalWarn; });

  assert.doesNotThrow(() => createWindowControls().close());
  assert.match(warned[0][0], /window\.electronAPI is unavailable/);
});

test('Title bar stays inert on pages without a title bar', async () => {
  const { mountTitleBar } = await import(TITLE_BAR);
  const document = new FakeDocument({ 'title-bar-minimize': 'title-bar-button' });
  const electronAPI = createElectronApiStub();

  assert.equal(mountTitleBar({ document, electronAPI }), null);

  document.getElementById('title-bar-minimize').click();
  assert.deepEqual(electronAPI.calls, []);
});

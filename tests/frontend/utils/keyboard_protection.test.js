const test = require('node:test');
const assert = require('node:assert/strict');

const { loadFrontendModule } = require('../helpers/modules');
const { createOverlayWindow, useElectronMock } = require('../helpers/electron');

const electron = useElectronMock();

test('Keyboard protection blocks developer and fullscreen shortcuts while regular keys pass through', () => {
  const { protectWindowShortcuts } = loadFrontendModule('utils/keyboard_protection');
  const overlay = createOverlayWindow();
  protectWindowShortcuts(overlay, { allowDevTools: false });

  assert.equal(overlay.pressKey({ type: 'keyDown', key: 'F12' }), true);
  assert.equal(overlay.pressKey({ type: 'keyDown', key: 'F11' }), true);
  assert.equal(overlay.pressKey({ type: 'keyDown', key: 'I', control: true, shift: true }), true);
  assert.equal(overlay.pressKey({ type: 'keyDown', key: 'K' }), false);
  assert.equal(overlay.webContents.devtoolsToggles, 0);

  const devOverlay = createOverlayWindow();
  protectWindowShortcuts(devOverlay, { allowDevTools: true });

  assert.equal(devOverlay.pressKey({ type: 'keyDown', key: 'F12' }), true);
  assert.equal(devOverlay.webContents.devtoolsToggles, 1);
  assert.equal(devOverlay.menuBarVisible, true);
});

test('Keyboard protection blocks zoom shortcuts for both modifiers', () => {
  const { disableZoomShortcuts } = loadFrontendModule('utils/keyboard_protection');
  const overlay = createOverlayWindow();
  disableZoomShortcuts(overlay);

  for (const key of ['+', '=', '-', '0']) {
    assert.equal(overlay.pressKey({ type: 'keyDown', key, control: true }), true, `ctrl+${key}`);
    assert.equal(overlay.pressKey({ type: 'keyDown', key, meta: true }), true, `cmd+${key}`);
  }

  assert.equal(overlay.pressKey({ type: 'keyDown', key: '+' }), false);
  assert.equal(overlay.pressKey({ type: 'keyDown', key: 'a', control: true }), false);
});

test('Keyboard protection registers the hotkey that toggles overlay movement', () => {
  const { registerOverlayMoveShortcuts } = loadFrontendModule('utils/keyboard_protection');
  const { getOverlayMovementState } = loadFrontendModule('utils/overlays/overlay_movement');
  const overlays = { radar: createOverlayWindow() };
  registerOverlayMoveShortcuts(electron.app, overlays);

  assert.ok(electron.globalShortcut.registered.has('Control+Shift+P'));

  electron.globalShortcut.trigger('Control+Shift+P');

  assert.equal(getOverlayMovementState(), true);
  assert.equal(overlays.radar.movable, true);
});

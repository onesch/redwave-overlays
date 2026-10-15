const test = require('node:test');
const assert = require('node:assert/strict');

const { loadFrontendModule } = require('../helpers/modules');
const { createOverlayWindow, useElectronMock } = require('../helpers/electron');

const electron = useElectronMock();

test('Overlay movement toggles between locked and movable for every window', async () => {
  const { registerOverlayMovementHandlers } = loadFrontendModule(
    'utils/overlays/overlay_movement',
  );
  const overlays = {
    radar: createOverlayWindow(),
    leaderboard: createOverlayWindow(),
    closed: createOverlayWindow({ destroyed: true }),
  };
  const settingsWindow = createOverlayWindow();
  registerOverlayMovementHandlers(overlays);

  assert.equal(await electron.ipcMain.invoke('get-overlay-movement-state'), false);

  assert.equal(await electron.ipcMain.invoke('update-overlay-movement-state'), true);
  assert.deepEqual(
    [overlays.radar, overlays.leaderboard].map((win) => [win.movable, win.ignoreMouseEvents]),
    [[true, false], [true, false]],
  );
  // Closed overlays are left alone, open ones and the settings page are notified.
  assert.equal(overlays.closed.movable, null);
  assert.deepEqual(settingsWindow.sent, [
    { channel: 'overlay-movement-state-updated', args: [true] },
  ]);
  assert.equal(electron.readSettings().__isOverlayMovementEnabled, true);

  assert.equal(await electron.ipcMain.invoke('update-overlay-movement-state'), false);
  assert.deepEqual(
    [overlays.radar, overlays.leaderboard].map((win) => [win.movable, win.ignoreMouseEvents]),
    [[false, true], [false, true]],
  );
});

test('Overlay movement starts locked on app start even if movement was enabled before', () => {
  electron.writeSettings({ __isOverlayMovementEnabled: true });
  const { getOverlayMovementState, resetOverlayMovementStateOnAppStart } = loadFrontendModule(
    'utils/overlays/overlay_movement',
  );

  assert.equal(getOverlayMovementState(), true);

  resetOverlayMovementStateOnAppStart();

  assert.equal(getOverlayMovementState(), false);
  assert.equal(electron.readSettings().__isOverlayMovementEnabled, false);
});

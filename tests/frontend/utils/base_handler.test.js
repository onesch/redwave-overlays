const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');

const { loadFrontendModule } = require('../helpers/modules');
const { createOverlayWindow, useElectronMock } = require('../helpers/electron');

const electron = useElectronMock();
const LAST_LAP_FORMAT = 'utils/overlays/features/leaderboard/last_lap_format';

test('Base handler falls back to the default for missing or unsupported stored values', async () => {
  const { registerLastLapFormatHandlers, DEFAULT_LAST_LAP_FORMAT } =
    loadFrontendModule(LAST_LAP_FORMAT);
  registerLastLapFormatHandlers({ leaderboard: createOverlayWindow() });

  // Nothing stored yet.
  assert.equal(
    await electron.ipcMain.invoke('get-last-lap-format', 'leaderboard'),
    DEFAULT_LAST_LAP_FORMAT,
  );

  // A value the overlay does not support must not leak into the renderer.
  electron.writeSettings({ leaderboard: { LastLapFormat: 'bogus' } });
  assert.equal(
    await electron.ipcMain.invoke('get-last-lap-format', 'leaderboard'),
    DEFAULT_LAST_LAP_FORMAT,
  );

  electron.writeSettings({ leaderboard: { LastLapFormat: 'SS.ss' } });
  assert.equal(await electron.ipcMain.invoke('get-last-lap-format', 'leaderboard'), 'SS.ss');
});

test('Base handler persists updates, normalizes them, and pushes them to the open overlay', () => {
  const { registerLastLapFormatHandlers, DEFAULT_LAST_LAP_FORMAT } =
    loadFrontendModule(LAST_LAP_FORMAT);
  const overlay = createOverlayWindow();
  registerLastLapFormatHandlers({ leaderboard: overlay });

  electron.ipcMain.emit('set-last-lap-format', { overlayName: 'leaderboard', value: 'SS.ss' });

  assert.equal(electron.readSettings().leaderboard.LastLapFormat, 'SS.ss');
  assert.deepEqual(overlay.sent, [{ channel: 'update-last-lap-format', args: ['SS.ss'] }]);

  overlay.sent.length = 0;
  electron.ipcMain.emit('set-last-lap-format', { overlayName: 'leaderboard', value: 'nope' });

  assert.equal(electron.readSettings().leaderboard.LastLapFormat, DEFAULT_LAST_LAP_FORMAT);
  assert.deepEqual(
    overlay.sent,
    [{ channel: 'update-last-lap-format', args: [DEFAULT_LAST_LAP_FORMAT] }],
  );
});

test('Base handler stores updates without notifying an overlay that is not open', () => {
  const { registerLastLapFormatHandlers } = loadFrontendModule(LAST_LAP_FORMAT);
  const closedOverlay = createOverlayWindow({ destroyed: true });
  registerLastLapFormatHandlers({ leaderboard: closedOverlay });

  electron.ipcMain.emit('set-last-lap-format', { overlayName: 'leaderboard', value: 'SS.ss' });
  electron.ipcMain.emit('set-last-lap-format', { overlayName: 'never-opened', value: 'SS.ss' });

  assert.deepEqual(closedOverlay.sent, []);
  assert.equal(electron.readSettings().leaderboard.LastLapFormat, 'SS.ss');
  assert.equal(electron.readSettings()['never-opened'].LastLapFormat, 'SS.ss');
});

test('Base handler recovers from a corrupt settings file instead of failing to load or save', async () => {
  const { registerLastLapFormatHandlers, DEFAULT_LAST_LAP_FORMAT } =
    loadFrontendModule(LAST_LAP_FORMAT);

  fs.writeFileSync(electron.settingsFile, '{ not json');

  const logged = [];
  const consoleError = console.error;
  console.error = (message) => logged.push(message);

  try {
    registerLastLapFormatHandlers({ leaderboard: createOverlayWindow() });

    assert.equal(
      await electron.ipcMain.invoke('get-last-lap-format', 'leaderboard'),
      DEFAULT_LAST_LAP_FORMAT,
    );

    assert.match(logged[0], /Failed to load settings/);

    electron.ipcMain.emit('set-last-lap-format', {
      overlayName: 'leaderboard',
      value: 'SS.ss',
    });

    assert.equal(electron.readSettings().leaderboard.LastLapFormat, 'SS.ss');
  } finally {
    console.error = consoleError;
  }
});

const test = require('node:test');
const assert = require('node:assert/strict');

const { loadFrontendModule } = require('../helpers/modules');
const { createOverlayWindow, useElectronMock } = require('../helpers/electron');

const electron = useElectronMock();

test('Window events minimize and close the main window, ignoring one that is gone', () => {
  const { registerWindowEvents } = loadFrontendModule('ipc/WindowEvents');
  let mainWindow = null;
  registerWindowEvents(() => mainWindow);

  // The window has not been created yet (or is already closed).
  electron.ipcMain.emit('window-minimize');
  electron.ipcMain.emit('window-close');

  mainWindow = createOverlayWindow();
  electron.ipcMain.emit('window-minimize');
  electron.ipcMain.emit('window-close');

  assert.equal(mainWindow.minimized, true);
  assert.equal(mainWindow.closed, true);

  const destroyed = createOverlayWindow({ destroyed: true });
  mainWindow = destroyed;
  electron.ipcMain.emit('window-minimize');
  electron.ipcMain.emit('window-close');

  assert.equal(destroyed.minimized, false);
  assert.equal(destroyed.closed, false);
});

test('Window events drag the window by the offset where the drag started', () => {
  const { registerWindowEvents } = loadFrontendModule('ipc/WindowEvents');
  let mainWindow = createOverlayWindow({
    bounds: { x: 100, y: 50, width: 800, height: 600 },
  });
  registerWindowEvents(() => mainWindow);

  // Moving without a drag start does not move the window.
  electron.screen.cursor = { x: 500, y: 400 };
  electron.ipcMain.emit('window-drag-move');
  assert.deepEqual(mainWindow.getPosition(), [100, 50]);

  // The cursor grabbed the window 30px in from its top-left corner.
  electron.screen.cursor = { x: 130, y: 80 };
  electron.ipcMain.emit('window-drag-start');
  electron.screen.cursor = { x: 330, y: 280 };
  electron.ipcMain.emit('window-drag-move');
  assert.deepEqual(mainWindow.getPosition(), [300, 250]);

  // After the drag ends the window stays where it was dropped.
  electron.ipcMain.emit('window-drag-end');
  electron.screen.cursor = { x: 900, y: 900 };
  electron.ipcMain.emit('window-drag-move');
  assert.deepEqual(mainWindow.getPosition(), [300, 250]);

  // A drag that starts on a destroyed window does not move its replacement.
  mainWindow = createOverlayWindow({ destroyed: true });
  electron.ipcMain.emit('window-drag-start');
  mainWindow = createOverlayWindow({
    bounds: { x: 10, y: 20, width: 800, height: 600 },
  });
  electron.ipcMain.emit('window-drag-move');
  assert.deepEqual(mainWindow.getPosition(), [10, 20]);
});

test('Preload exposes the title bar controls on the channels window events listen to', () => {
  loadFrontendModule('preload');
  const api = electron.contextBridge.exposedApi;

  api.minimizeWindow();
  api.closeWindow();
  api.startWindowDrag();
  api.dragWindow();
  api.endWindowDrag();

  assert.deepEqual(
    electron.ipcRenderer.sent.map(({ channel }) => channel),
    ['window-minimize', 'window-close', 'window-drag-start', 'window-drag-move', 'window-drag-end'],
  );
});

const { app } = require('electron');

const { createMainWindow } = require('./windows/mainWindow');
const registerRadarEvents = require('./ipc/RadarEvents');
const registerLeaderboardEvents = require('./ipc/LeaderboardEvents');
const registerSettingsEvents = require('./ipc/SettingsEvents');
const { startBackend, stopBackend } = require('./utils/backendManager');

let mainWindow = null;


async function createWindow() {
  if (mainWindow) {
    mainWindow.focus();
    return;
  }

  await startBackend();

  mainWindow = createMainWindow();

  registerRadarEvents();
  registerLeaderboardEvents();
  registerSettingsEvents();

  mainWindow.on('closed', () => {
    mainWindow = null;
  });
}

const gotTheLock = app.requestSingleInstanceLock();
if (!gotTheLock) {
  app.quit();
  return;
}

app.whenReady().then(createWindow);

app.on('activate', () => {
  if (!mainWindow) createWindow();
});

app.on('second-instance', () => {
  if (!mainWindow) return;
  if (mainWindow.isMinimized()) mainWindow.restore();
  mainWindow.focus();
});

function shutdown() {
  stopBackend();
}

app.on('before-quit', shutdown);
app.on('will-quit', shutdown);

process.on('exit', shutdown);
process.on('SIGINT', shutdown);
process.on('SIGTERM', shutdown);
process.on('uncaughtException', shutdown);

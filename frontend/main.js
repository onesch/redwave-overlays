const { app } = require('electron');

const { createMainWindow } = require('./windows/mainWindow');
const { createOverlay } = require('./windows/overlayWindow');
const { loadSettings } = require('./utils/overlay_settings');
const overlaysConfig = require('./windows/overlays_config');
const { startBackend, stopBackend } = require('./utils/backendManager');

const { registerAllOverlayEvents } = require('./ipc/OverlayEvents');
const registerSettingsEvents = require('./ipc/SettingsEvents');

let mainWindow = null;

// Launches overlays that have AutoStart enabled
function autoStartOverlays() {
  const settings = loadSettings();

  for (const overlayName of Object.keys(overlaysConfig)) {
    // Default to 'off' if setting is missing
    const autoStart = settings[overlayName]?.AutoStart ?? 'off';
    if (autoStart === 'on') {
      createOverlay(overlayName);
    }
  }
}

async function createWindow() {
  // Prevent multiple main windows
  if (mainWindow) {
    mainWindow.focus();
    return;
  }

  // Wait for FastAPI backend to be ready
  await startBackend();

  mainWindow = createMainWindow();

  // Registers IPC events for all overlays
  registerAllOverlayEvents();

  // Registers IPC event for reset overlay settings
  registerSettingsEvents();

  // Open overlays marked as auto-start in settings
  autoStartOverlays();

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

const { ipcMain } = require('electron');
const { loadSettings, saveSettings } = require('./overlay_settings');

// Apply saved position when the window is created
function applySavedPosition(overlay, route) {
  const settings = loadSettings();
  const savedPos = settings[route]?.position;
  if (savedPos && Array.isArray(savedPos) && savedPos.length === 2) {
    overlay.setBounds({
      x: savedPos[0],
      y: savedPos[1],
      width: overlay.getBounds().width,
      height: overlay.getBounds().height
    });
  }
}

// Register IPC handlers to read position
function registerPositionHandlers() {
  ipcMain.handle('get-overlay-position', (event, overlayName) => {
    const settings = loadSettings();
    return settings[overlayName]?.position ?? null;
  });
}

// Subscribe to the close event to save the position
function watchOverlayPosition(overlay, route) {
  overlay.on('close', () => {
    const bounds = overlay.getBounds();
    const settings = loadSettings();
    settings[route] = settings[route] || {};
    settings[route].position = [bounds.x, bounds.y];
    saveSettings(settings);
  });
}

module.exports = {
  applySavedPosition,
  registerPositionHandlers,
  watchOverlayPosition,
};

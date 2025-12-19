const { ipcMain } = require('electron');
const { loadSettings, saveSettings } = require('../utils/overlay_settings');

// Load saved zoom factor and apply it to the window after it finishes loading
function applySavedZoom(overlay, route) {
  const settings = loadSettings();
  const savedZoom = settings[route]?.zoom ?? 1;
  overlay.webContents.on('did-finish-load', () => {
    overlay.webContents.setZoomFactor(savedZoom);
  });
}

// Register IPC handlers to manage overlay zoom
function registerZoomHandlers(overlays) {
  ipcMain.on('set-overlay-zoom', (event, { overlayName, zoomFactor }) => {
    const settings = loadSettings();
    settings[overlayName] = settings[overlayName] || {};
    settings[overlayName].zoom = zoomFactor;
    saveSettings(settings);

    const win = overlays[overlayName];
    if (win && !win.isDestroyed()) {
      win.webContents.setZoomFactor(zoomFactor);
    }
  });

  ipcMain.handle('get-overlay-zoom', (event, overlayName) => {
    const settings = loadSettings();
    return settings[overlayName]?.zoom ?? 1;
  });
}

module.exports = {
  applySavedZoom,
  registerZoomHandlers,
};

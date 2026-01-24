const { ipcMain } = require('electron');
const { loadSettings, saveSettings } = require('../utils/overlay_settings');

// Cache of current zoom factors in memory
// Priority: memory - file - default
const currentZoomFactors = {};

// Apply the saved zoom when loading the overlay
function applySavedZoom(overlay, route) {
  overlay.webContents.on('did-finish-load', () => {
    const zoomFactor = currentZoomFactors[route] ?? loadSettings()[route]?.zoom ?? 1;
    overlay.webContents.setZoomFactor(zoomFactor);
    // Update the cache
    currentZoomFactors[route] = zoomFactor;
  });
}

// Register IPC handlers to manage overlay zoom
function registerZoomHandlers(overlays) {
  ipcMain.on('set-overlay-zoom', (event, { overlayName, zoomFactor }) => {
    // Update the live value in memory (for the current session)
    currentZoomFactors[overlayName] = zoomFactor;
    
    // Save to a file so that the changes remain after a restart.
    const settings = loadSettings();
    settings[overlayName] = settings[overlayName] || {};
    settings[overlayName].zoom = zoomFactor;
    saveSettings(settings);

    // Apply to window
    const win = overlays[overlayName];
    if (win && !win.isDestroyed()) {
      win.webContents.setZoomFactor(zoomFactor);
    }
  });

  ipcMain.handle('get-overlay-zoom', (event, overlayName) => {
    return currentZoomFactors[overlayName] ?? loadSettings()[overlayName]?.zoom ?? 1;
  });
}

// Clear zoom cache (for reset)
function clearZoomCache() {
  for (const key in currentZoomFactors) {
    delete currentZoomFactors[key];
  }
}

module.exports = {
  applySavedZoom,
  registerZoomHandlers,
  clearZoomCache,
};

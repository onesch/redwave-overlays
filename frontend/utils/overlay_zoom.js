const { ipcMain } = require('electron');
const { loadSettings, saveSettings } = require('./overlay_settings');
const { applyOverlaySize } = require('./overlay_size');

// In-memory cache of current zoom factors.
const currentZoomFactors = {};

function getTrackType(overlayName, settings) {
  if (overlayName !== 'track-map') return undefined;
  return settings[overlayName]?.TrackType ?? 'linear';
}

// Apply persisted zoom settings when an overlay finishes loading.
function applySavedZoom(overlay, overlayName) {
  overlay.webContents.on('did-finish-load', () => {
    const settings = loadSettings();
    const zoomFactor = currentZoomFactors[overlayName] ?? settings[overlayName]?.zoom ?? 1;
    currentZoomFactors[overlayName] = zoomFactor;

    applyOverlaySize(
      overlay,
      overlayName,
      zoomFactor,
      getTrackType(overlayName, settings),
      false
    );
  });
}

// Register IPC handlers for managing overlay zoom.
function registerZoomHandlers(overlays) {
  ipcMain.on('set-overlay-zoom', (event, { overlayName, zoomFactor }) => {
    currentZoomFactors[overlayName] = zoomFactor;

    const settings = loadSettings();
    settings[overlayName] = settings[overlayName] || {};
    settings[overlayName].zoom = zoomFactor;
    saveSettings(settings);

    const win = overlays[overlayName];
    if (!win || win.isDestroyed()) return;

    applyOverlaySize(
      win,
      overlayName,
      zoomFactor,
      getTrackType(overlayName, settings),
      true
    );
  });

  ipcMain.handle('get-overlay-zoom', (event, overlayName) => {
    const settings = loadSettings();
    return currentZoomFactors[overlayName] ?? settings[overlayName]?.zoom ?? 1;
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
  currentZoomFactors,
};

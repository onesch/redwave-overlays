const { registerOverlaySetting } = require('./base_handler');
const { loadSettings } = require('./overlay_settings');
const { applyOverlaySize } = require('./overlay_size');
const { getTrackType } = require('./track_type');

// In-memory cache of current zoom factors.
const currentZoomFactors = {};

// Register IPC handlers for managing overlay zoom.
function registerZoomHandlers(overlays) {
  registerOverlaySetting({
    overlays,
    getChannel: 'get-overlay-zoom',
    setChannel: 'set-overlay-zoom',
    settingKey: 'zoom',
    defaultValue: 1,

    afterGet: ({ overlayName, value }) => {
      const zoom = currentZoomFactors[overlayName] ?? value;
      currentZoomFactors[overlayName] = zoom;
      return zoom;
    },

    afterSet: ({ overlay, overlayName, value, settings }) => {
      currentZoomFactors[overlayName] = value;

      applyOverlaySize(
        overlay,
        overlayName,
        value,
        getTrackType(overlayName, settings),
        true
      );
    },
  });
}

// Apply persisted zoom settings when an overlay finishes loading.
function applySavedZoom(overlay, overlayName) {
  overlay.webContents.on('did-finish-load', () => {
    const settings = loadSettings();
    const zoomFactor =
      currentZoomFactors[overlayName] ?? settings[overlayName]?.zoom ?? 1;

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

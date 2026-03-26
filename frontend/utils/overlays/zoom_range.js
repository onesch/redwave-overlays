const { registerOverlaySetting } = require('./base_handler');
const { loadSettings } = require('./overlay_settings');
const { applyOverlaySize } = require('./overlay_size');
const { getTrackType } = require('./track_type');
const { currentZoomFactors, currentTrackTypes } = require('./zoom_store');

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

      // Resolve the current track type from in-memory cache first so
      // we always use the live value, not a potentially stale disk read.
      const trackType =
        overlayName === 'track-map'
          ? (currentTrackTypes[overlayName] ?? getTrackType(overlayName, settings))
          : undefined;

      applyOverlaySize(overlay, overlayName, value, trackType, true);
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

    // Also prime the track-type cache from disk on first load so that
    // subsequent zoom changes have a valid type to work with.
    if (overlayName === 'track-map' && !currentTrackTypes[overlayName]) {
      currentTrackTypes[overlayName] =
        settings[overlayName]?.TrackType ?? 'linear';
    }

    const trackType = getTrackType(overlayName, settings);
    applyOverlaySize(overlay, overlayName, zoomFactor, trackType, false);
  });
}

// Clear zoom cache (for reset)
function clearZoomCache() {
  for (const key in currentZoomFactors) {
    delete currentZoomFactors[key];
  }
  for (const key in currentTrackTypes) {
    delete currentTrackTypes[key];
  }
}

module.exports = {
  applySavedZoom,
  registerZoomHandlers,
  clearZoomCache,
};

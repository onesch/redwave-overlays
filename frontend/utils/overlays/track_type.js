const { registerOverlaySetting } = require('./base_handler');
const { applyOverlaySize } = require('./overlay_size');
const { currentZoomFactors, currentTrackTypes } = require('./zoom_store');

function getTrackType(overlayName, settings) {
  if (overlayName !== 'track-map') return undefined;

  // Prefer the in-memory value, it is always up to date even before
  // the new type reaches disk via saveSettings.
  return (
    currentTrackTypes[overlayName] ??
    settings[overlayName]?.TrackType ??
    'linear'
  );
}

function registerOverlayTrackTypeHandlers(overlays) {
  registerOverlaySetting({
    overlays,
    getChannel: 'get-track-map-type',
    setChannel: 'set-track-map-type',
    settingKey: 'TrackType',
    defaultValue: 'linear',
    updateEvent: 'update-track-map-type',

    afterSet: ({ overlay, overlayName, value, settings }) => {
      // Keep the in-memory type in sync so zoom handler always sees
      // the correct value without re-reading from disk.
      currentTrackTypes[overlayName] = value;

      const zoomFactor =
        currentZoomFactors[overlayName] ??
        settings[overlayName]?.zoom ??
        1;

      applyOverlaySize(overlay, overlayName, zoomFactor, value, true);
    },
  });
}

module.exports = { registerOverlayTrackTypeHandlers, getTrackType };

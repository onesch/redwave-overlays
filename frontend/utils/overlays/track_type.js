const { registerOverlaySetting } = require('./base_handler');
const { applyOverlaySize } = require('./overlay_size');
const { currentZoomFactors } = require('./zoom_store');

function getTrackType(overlayName, settings) {
  if (overlayName !== 'track-map') return undefined;
  return settings[overlayName]?.TrackType ?? 'linear';
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
      const zoomFactor =
        currentZoomFactors[overlayName] ??
        settings[overlayName]?.zoom ??
        1;

      applyOverlaySize(
        overlay,
        overlayName,
        zoomFactor,
        overlayName === 'track-map' ? value : undefined,
        true
      );
    },
  });
}

module.exports = { registerOverlayTrackTypeHandlers, getTrackType };

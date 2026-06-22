const { registerOverlaySetting } = require('./base_handler');

const currentRadarModes = {};

function getRadarVisibility(overlayName, settings) {
  if (overlayName !== 'radar') return undefined;

  return (
    currentRadarModes[overlayName] ??
    settings[overlayName]?.RadarVisibility ??
    'dim'
  );
}

function registerOverlayRadarVisibilityHandlers(overlays) {
  registerOverlaySetting({
    overlays,
    getChannel: 'get-radar-visibility',
    setChannel: 'set-radar-visibility',
    settingKey: 'RadarVisibility',
    defaultValue: 'dim',
    updateEvent: 'update-radar-visibility',

    afterSet: ({ overlayName, value }) => {
      currentRadarModes[overlayName] = value;
    },
  });
}

module.exports = {
  registerOverlayRadarVisibilityHandlers,
  getRadarVisibility,
};

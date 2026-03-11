const { registerOverlaySetting } = require('./base_handler');

function registerOverlayOpacityHandlers(overlays) {
  registerOverlaySetting({
    overlays,
    getChannel: 'get-card-bg-opacity',
    setChannel: 'set-card-bg-opacity',
    settingKey: 'cardBgOpacity',
    defaultValue: 1,
    updateEvent: 'update-card-opacity',
  });
}

module.exports = { registerOverlayOpacityHandlers };

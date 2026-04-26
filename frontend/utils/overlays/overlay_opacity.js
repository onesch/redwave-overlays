const { registerOverlaySetting } = require('./base_handler');

function registerOverlayOpacityHandlers(overlays) {
  registerOverlaySetting({
    overlays,
    getChannel: 'get-overlay-bg-opacity',
    setChannel: 'set-overlay-bg-opacity',
    settingKey: 'overlayBgOpacity',
    defaultValue: 1,
    updateEvent: 'update-overlay-opacity',
  });
}

module.exports = { registerOverlayOpacityHandlers };

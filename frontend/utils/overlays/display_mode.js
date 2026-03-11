const { registerOverlaySetting } = require('./base_handler');

function registerOverlayDisplayModeHandlers(overlays) {
  registerOverlaySetting({
    overlays,
    getChannel: 'get-display-mode',
    setChannel: 'set-display-mode',
    settingKey: 'DisplayMode',
    defaultValue: 'all_time',
    updateEvent: 'update-display-mode',
  });
}

module.exports = { registerOverlayDisplayModeHandlers };

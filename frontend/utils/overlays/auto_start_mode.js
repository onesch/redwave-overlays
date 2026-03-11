const { registerOverlaySetting } = require('./base_handler');

function registerOverlayAutoStartModeHandlers(overlays) {
  registerOverlaySetting({
    overlays,
    getChannel: 'get-auto-start-mode',
    setChannel: 'set-auto-start-mode',
    settingKey: 'AutoStart',
    defaultValue: 'off',
    updateEvent: 'update-auto-start-mode',
  });
}

module.exports = { registerOverlayAutoStartModeHandlers };

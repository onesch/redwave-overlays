const { ipcMain } = require('electron');
const { resetSettings } = require('../utils/overlay_settings');

function registerSettingsEvents() {
  ipcMain.on('reset-overlay-settings', () => {
    resetSettings();
  });
}

module.exports = registerSettingsEvents;

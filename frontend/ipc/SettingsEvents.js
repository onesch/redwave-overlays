const { ipcMain } = require('electron');
const { resetSettings } = require('../utils/overlay_settings');
const { overlays } = require('../windows/overlayWindow');

function registerSettingsEvents() {
  ipcMain.on('reset-overlay-settings', () => {
    // close all overlays
    for (const overlay of Object.values(overlays)) {
        if (!overlay.isDestroyed()) overlay.destroy();
    }

    // delete settings file
    resetSettings();
  });
}

module.exports = registerSettingsEvents;

const { ipcMain } = require('electron');
const { resetSettings } = require('../utils/overlay_settings');
const { overlays } = require('../windows/overlayWindow');
const { clearZoomCache } = require('../utils/overlay_zoom');

function registerSettingsEvents() {
  ipcMain.on('reset-overlay-settings', () => {
    // Сlose all overlays
    for (const overlay of Object.values(overlays)) {
        if (!overlay.isDestroyed()) overlay.destroy();
    }

    // delete settings file
    resetSettings();
    
    // Clear zoom cache
    clearZoomCache();
  });
}

module.exports = registerSettingsEvents;

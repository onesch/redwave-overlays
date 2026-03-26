const { ipcMain } = require('electron');
const { resetSettings } = require('../utils/overlays/overlay_settings');
const { overlays } = require('../windows/overlayWindow');
const { clearZoomCache } = require('../utils/overlays/zoom_range');

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

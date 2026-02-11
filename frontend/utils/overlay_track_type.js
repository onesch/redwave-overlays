const { ipcMain } = require('electron');
const { loadSettings, saveSettings } = require('./overlay_settings');

function registerOverlayTrackTypeHandlers(overlays) {
  ipcMain.handle('get-track-map-type', (e, overlayName) => {
    const settings = loadSettings();
    const value = settings[overlayName]?.TrackType ?? 'linear';

    console.log(`[DEBUG][GET] ${overlayName} =`, value);
    return value;
  });

  ipcMain.on('set-track-map-type', (e, { overlayName, value }) => {
    const settings = loadSettings();
    settings[overlayName] ||= {};
    settings[overlayName].TrackType = value;

    saveSettings(settings);

    console.log(`[DEBUG][SET] ${overlayName} =`, value);

    const overlay = overlays[overlayName];
    if (overlay && !overlay.isDestroyed()) {
      overlay.webContents.send('update-track-map-type', value);
    }
  });
}

module.exports = { registerOverlayTrackTypeHandlers };

const { ipcMain } = require('electron');
const { loadSettings, saveSettings } = require('./overlay_settings');

function registerOverlayOpacityHandlers(overlays) {
  ipcMain.handle('get-card-bg-opacity', (e, overlayName) => {
    const settings = loadSettings();
    return settings[overlayName]?.cardBgOpacity ?? 1;
  });

  ipcMain.on('set-card-bg-opacity', (e, { overlayName, value }) => {
    const settings = loadSettings();
    settings[overlayName] ||= {};
    settings[overlayName].cardBgOpacity = value;
    saveSettings(settings);

    const overlay = overlays[overlayName];
    if (overlay && !overlay.isDestroyed()) {
      overlay.webContents.send('update-card-opacity', value);
    }
  });
}

module.exports = { registerOverlayOpacityHandlers };

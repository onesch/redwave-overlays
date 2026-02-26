const { ipcMain } = require('electron');
const { loadSettings, saveSettings } = require('./overlay_settings');

function registerOverlayDisplayModeHandlers(overlays) {
  ipcMain.handle('get-display-mode', (e, overlayName) => {
    const settings = loadSettings();
    const value = settings[overlayName]?.DisplayMode ?? 'all_time';
    return value;
  });

  ipcMain.on('set-display-mode', (e, { overlayName, value }) => {

    const settings = loadSettings();
    settings[overlayName] ||= {};
    settings[overlayName].DisplayMode = value;
    saveSettings(settings);

    const overlay = overlays[overlayName];
    if (!overlay || overlay.isDestroyed()) {
      return;
    }

    overlay.webContents.send('update-display-mode', value);
  });
}

module.exports = { registerOverlayDisplayModeHandlers };

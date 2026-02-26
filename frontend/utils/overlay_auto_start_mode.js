const { ipcMain } = require('electron');
const { loadSettings, saveSettings } = require('./overlay_settings');


function registerOverlayAutoStartModeHandlers(overlays) {
  ipcMain.handle('get-auto-start-mode', (e, overlayName) => {
    const settings = loadSettings();
    const value = settings[overlayName]?.AutoStart ?? 'off';
    return value;
  });

  ipcMain.on('set-auto-start-mode', (e, { overlayName, value }) => {

    const settings = loadSettings();
    settings[overlayName] ||= {};
    settings[overlayName].AutoStart = value;
    saveSettings(settings);

    const overlay = overlays[overlayName];
    if (!overlay || overlay.isDestroyed()) {
      return;
    }

    overlay.webContents.send('update-auto-start-mode', value);
  });
}

module.exports = { registerOverlayAutoStartModeHandlers };

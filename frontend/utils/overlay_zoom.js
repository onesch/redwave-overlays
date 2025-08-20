const { ipcMain } = require('electron');
const { loadSettings, saveSettings } = require('../utils/overlay_settings');

// Загружает масштаб и применяет к окну после загрузки
function applySavedZoom(overlay, route) {
  const settings = loadSettings();
  const savedZoom = settings[route]?.zoom ?? 1;
  overlay.webContents.on('did-finish-load', () => {
    overlay.webContents.setZoomFactor(savedZoom);
  });
}

// Регистрирует IPC обработчики для управления масштабом
function registerZoomHandlers(overlays) {
  ipcMain.on('set-overlay-zoom', (event, { overlayName, zoomFactor }) => {
    const settings = loadSettings();
    settings[overlayName] = settings[overlayName] || {};
    settings[overlayName].zoom = zoomFactor;
    saveSettings(settings);

    const win = overlays[overlayName];
    if (win && !win.isDestroyed()) {
      win.webContents.setZoomFactor(zoomFactor);
    }
  });

  ipcMain.handle('get-overlay-zoom', (event, overlayName) => {
    const settings = loadSettings();
    return settings[overlayName]?.zoom ?? 1;
  });
}

module.exports = {
  applySavedZoom,
  registerZoomHandlers,
};

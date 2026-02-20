const { ipcMain } = require('electron');
const { loadSettings, saveSettings } = require('./overlay_settings');
const { applyOverlaySize } = require('./overlay_size');
const { currentZoomFactors } = require('./overlay_zoom');

function registerOverlayTrackTypeHandlers(overlays) {
  ipcMain.handle('get-track-map-type', (e, overlayName) => {
    const settings = loadSettings();
    const value = settings[overlayName]?.TrackType ?? 'linear';

    return value;
  });

  ipcMain.on('set-track-map-type', (e, { overlayName, value }) => {
    const settings = loadSettings();
    settings[overlayName] ||= {};
    settings[overlayName].TrackType = value;
    saveSettings(settings);

    const zoomFactor = currentZoomFactors[overlayName] ?? settings[overlayName]?.zoom ?? 1;

    const overlay = overlays[overlayName];
    if (!overlay || overlay.isDestroyed()) return;

    overlay.webContents.send('update-track-map-type', value);

    applyOverlaySize(
      overlay,
      overlayName,
      zoomFactor,
      overlayName === 'track-map' ? value : undefined,
      true
    );
  });
}

module.exports = { registerOverlayTrackTypeHandlers };

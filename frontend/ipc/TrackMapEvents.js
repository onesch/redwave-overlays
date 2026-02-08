const { ipcMain } = require('electron');
const { createOverlay } = require('../windows/overlayWindow');

function registerTrackMapEvents() {
  ipcMain.on('open-track-map', () => {
    createOverlay('track-map', {
      width: 850,
      height: 200,
    });
  });
}

module.exports = registerTrackMapEvents;

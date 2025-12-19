const { ipcMain } = require('electron');
const { createOverlay } = require('../windows/overlayWindow');

function registerRadarEvents() {
  ipcMain.on('open-radar', () => {
    createOverlay('radar', {
      width: 500,
      height: 500,
    });
  });
}

module.exports = registerRadarEvents;

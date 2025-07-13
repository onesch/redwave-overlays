const { ipcMain } = require('electron');
const { createOverlay } = require('../windows/overlayWindow');

function registerSpeedEvents() {
  ipcMain.on('open-speed', () => {
    createOverlay('speed', {
      width: 400,
      height: 250,
    });
  });
}

module.exports = registerSpeedEvents;

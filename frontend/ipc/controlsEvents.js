const { ipcMain } = require('electron');
const { createOverlay } = require('../windows/overlayWindow');

function registerControlsEvents() {
  ipcMain.on('open-controls', () => {
    createOverlay('controls', {
      width: 450,
      height: 300,
    });
  });
}

module.exports = registerControlsEvents;

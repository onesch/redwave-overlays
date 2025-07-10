const { ipcMain } = require('electron');
const { createLayout } = require('../windows/layoutWindow');

function registerControlsEvents() {
  ipcMain.on('open-controls', () => {
    createLayout('controls', {
      width: 450,
      height: 300,
    });
  });
}

module.exports = registerControlsEvents;

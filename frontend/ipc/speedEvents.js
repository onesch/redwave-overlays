const { ipcMain } = require('electron');
const { createLayout } = require('../windows/layoutWindow');

function registerSpeedEvents() {
  ipcMain.on('open-speed', () => {
    createLayout('speed', {
      width: 400,
      height: 250,
    });
  });
}

module.exports = registerSpeedEvents;

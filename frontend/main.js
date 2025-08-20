const { app } = require('electron');
const { createMainWindow } = require('./windows/mainWindow');
const registerRadarEvents = require('./ipc/radarEvents');
const registerControlsEvents = require('./ipc/controlsEvents');

app.whenReady().then(() => {
  createMainWindow();
  registerRadarEvents();
  registerControlsEvents();
});

app.on('window-all-closed', () => {
  if (process.platform !== 'darwin') app.quit();
});

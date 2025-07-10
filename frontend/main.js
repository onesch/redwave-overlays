const { app, ipcMain } = require('electron');
const { createMainWindow } = require('./windows/mainWindow');
const registerSpeedEvents = require('./ipc/speedEvents');
const registerControlsEvents = require('./ipc/controlsEvents');

app.whenReady().then(() => {
  createMainWindow();
  registerSpeedEvents();
  registerControlsEvents();
});

app.on('window-all-closed', () => {
  if (process.platform !== 'darwin') app.quit();
});

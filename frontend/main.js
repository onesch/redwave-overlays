const { app } = require('electron');
const { createMainWindow } = require('./windows/mainWindow');
const registerRadarEvents = require('./ipc/RadarEvents');
const registerLeaderboardEvents = require('./ipc/leaderboardEvents');

app.whenReady().then(() => {
  createMainWindow();
  registerRadarEvents();
  registerLeaderboardEvents();
});

app.on('window-all-closed', () => {
  if (process.platform !== 'darwin') app.quit();
});

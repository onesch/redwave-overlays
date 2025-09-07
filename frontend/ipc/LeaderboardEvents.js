const { ipcMain } = require('electron');
const { createOverlay } = require('../windows/overlayWindow');

function registerLeaderboardEvents() {
  ipcMain.on('open-leaderboard', () => {
    createOverlay('leaderboard', {
      width: 450,
      height: 300,
    });
  });
}

module.exports = registerLeaderboardEvents;

const { BrowserWindow, ipcMain, shell } = require('electron');

const RELEASES_PAGE_URL =
  'https://github.com/onesch/redwave-overlays/releases/latest';

function broadcastUpdateStatus(status) {
  for (const window of BrowserWindow.getAllWindows()) {
    if (!window.isDestroyed()) {
      window.webContents.send('update-status', status);
    }
  }
}

function registerUpdateEvents(updateService) {
  ipcMain.handle('get-update-status', () => updateService.getStatus());
  ipcMain.handle('download-update', () => updateService.downloadUpdate());
  ipcMain.handle('open-update-release', () =>
    shell.openExternal(updateService.getStatus().releaseUrl ?? RELEASES_PAGE_URL),
  );

  updateService.onStatusChange(broadcastUpdateStatus);
}

module.exports = registerUpdateEvents;

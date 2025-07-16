const { BrowserWindow } = require('electron');
const path = require('path');

let mainWindow = null;

function createMainWindow() {
  mainWindow = new BrowserWindow({
    width: 800,
    height: 600,
    autoHideMenuBar: true,
    webPreferences: {
      contextIsolation: true,
      preload: path.join(__dirname, '../preload.js'),
    },
  });

  mainWindow.loadURL('http://localhost:8000/main');

  mainWindow.on('closed', () => {
    mainWindow = null;
  });

  mainWindow.webContents.on('before-input-event', (event, input) => {
    if (input.type === 'keyDown' && input.key === 'F12') {
      mainWindow.webContents.toggleDevTools();

      const show = !mainWindow.isMenuBarVisible();
      mainWindow.setMenuBarVisibility(show);
      mainWindow.autoHideMenuBar = !show;

      event.preventDefault();
    }
  });

  return mainWindow;
}

module.exports = { createMainWindow };

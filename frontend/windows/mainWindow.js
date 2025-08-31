const { BrowserWindow } = require('electron');
const path = require('path');
const { protectWindowShortcuts, disableZoomShortcuts } = require('../utils/keyboard_protection');
const isDev = process.env.NODE_ENV === "development";

let mainWindow = null;

function createMainWindow() {
  mainWindow = new BrowserWindow({
    width: 800,
    height: 600,
    autoHideMenuBar: true,
    webPreferences: {
      contextIsolation: true,
      preload: path.join(__dirname, '../preload.js'),
      partition: 'persist:main',
    },
  });

  protectWindowShortcuts(mainWindow, { allowDevTools: isDev });
  disableZoomShortcuts(mainWindow);

  mainWindow.loadURL('http://localhost:8000/main');

  mainWindow.on('closed', () => {
    mainWindow = null;
  });

  return mainWindow;
}

module.exports = { createMainWindow };

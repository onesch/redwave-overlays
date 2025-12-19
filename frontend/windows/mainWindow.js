const { BrowserWindow } = require('electron');
const path = require('path');
const { protectWindowShortcuts, disableZoomShortcuts } = require('../utils/keyboard_protection');

const isDev = process.env.NODE_ENV === "development";

function createMainWindow() {
  const win = new BrowserWindow({
    width: 800,
    height: 600,
    autoHideMenuBar: true,
    webPreferences: {
      contextIsolation: true,
      preload: path.join(__dirname, '../preload.js'),
      partition: 'persist:main',
    },
  });

  protectWindowShortcuts(win, { allowDevTools: isDev });
  disableZoomShortcuts(win);

  win.loadURL('http://127.0.0.1:8000/main');

  return win;
}

module.exports = { createMainWindow };

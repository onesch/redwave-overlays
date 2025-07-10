const { BrowserWindow } = require('electron');
const path = require('path');

function createLayout(route, options = {}) {
  const layout = new BrowserWindow({
    width: options.width || 400,
    height: options.height || 300,
    alwaysOnTop: true,
    frame: options.frame ?? false,
    transparent: options.transparent ?? true,
    resizable: options.resizable ?? false,
    webPreferences: {
      contextIsolation: true,
      preload: path.join(__dirname, '../preload.js'),
    },
    ...options.override,
  });

  layout.loadURL(`http://localhost:8000/${route}`);
}

module.exports = { createLayout };

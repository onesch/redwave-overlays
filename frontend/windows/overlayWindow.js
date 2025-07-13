const { BrowserWindow } = require('electron');
const path = require('path');

const overlays = {}; // Кеш окон

function createOverlay(route, options = {}) {
  // Если окно уже существует и не закрыто, просто фокусируем и возвращаем
  if (overlays[route] && !overlays[route].isDestroyed()) {
    overlays[route].focus();
    return overlays[route];
  }

  // Создаём новое окно
  const overlay = new BrowserWindow({
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

  overlay.loadURL(`http://localhost:8000/${route}`);

  // При закрытии окна удаляем ссылку из кеша
  overlay.on('closed', () => {
    delete overlays[route];
  });

  overlays[route] = overlay;

  return overlay;
}

module.exports = { createOverlay };

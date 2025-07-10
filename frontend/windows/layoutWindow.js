const { BrowserWindow } = require('electron');
const path = require('path');

const layouts = {}; // Кеш окон

function createLayout(route, options = {}) {
  // Если окно уже существует и не закрыто, просто фокусируем и возвращаем
  if (layouts[route] && !layouts[route].isDestroyed()) {
    layouts[route].focus();
    return layouts[route];
  }

  // Создаём новое окно
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

  // При закрытии окна удаляем ссылку из кеша
  layout.on('closed', () => {
    delete layouts[route];
  });

  layouts[route] = layout;

  return layout;
}

module.exports = { createLayout };

const { app, BrowserWindow } = require('electron');
const path = require('path');
const { protectWindowShortcuts, disableZoomShortcuts, registerOverlayMoveShortcuts } = require('../utils/keyboard_protection');
const { applySavedZoom, registerZoomHandlers } = require('../utils/overlay_zoom');
const { applySavedPosition, registerPositionHandlers, watchOverlayPosition } = require('../utils/overlay_position');

const overlays = {};
let overlayCount = 0;

// Загружаем обработчики
registerZoomHandlers(overlays);
registerPositionHandlers(overlays);

function createOverlay(route, options = {}) {
  if (overlays[route] && !overlays[route].isDestroyed()) {
    overlays[route].focus();
    return overlays[route];
  }

  overlayCount += 1;

  const overlay = new BrowserWindow({
    width: options.width || 400,
    height: options.height || 300,
    alwaysOnTop: true,
    frame: options.frame ?? false,
    transparent: options.transparent ?? true,
    resizable: true,
    movable: false,
    focusable: true,
    webPreferences: {
      contextIsolation: true,
      preload: path.join(__dirname, '../preload.js'),
      partition: `persist:overlay_${overlayCount}`,
    },
    ...options.override,
  });

  // По умолчанию выключаем клики/перемещение
  overlay.setIgnoreMouseEvents(true);
  overlay.setMovable(false);

  // Отключаем нежелательные сочетания клавиш
  protectWindowShortcuts(overlay, { allowDevTools: true });
  disableZoomShortcuts(overlay);

  overlay.loadURL(`http://localhost:8000/${route}`);

  // Сохраняем пользовательские настройки
  applySavedZoom(overlay, route);
  applySavedPosition(overlay, route);
  watchOverlayPosition(overlay, route);

  overlay.on('closed', () => {
    delete overlays[route];
  });

  overlays[route] = overlay;
  return overlay;
}

app.whenReady().then(() => {
  registerOverlayMoveShortcuts(app, overlays);
});

module.exports = { createOverlay };

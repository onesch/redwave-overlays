const { app, BrowserWindow } = require('electron');
const path = require('path');
const isDev = process.env.NODE_ENV === "development";
const { protectWindowShortcuts, disableZoomShortcuts, registerOverlayMoveShortcuts } = require('../utils/keyboard_protection');
const { applySavedZoom, registerZoomHandlers } = require('../utils/overlay_zoom');
const { applySavedPosition, registerPositionHandlers, watchOverlayPosition } = require('../utils/overlay_position');
const { registerOverlayOpacityHandlers } = require('../utils/overlay_card_opacity');
const { registerOverlayTrackTypeHandlers } = require('../utils/overlay_track_type');
const { registerOverlayDisplayModeHandlers } = require('../utils/overlay_display_mode');
const { registerOverlayAutoStartModeHandlers } = require('../utils/overlay_auto_start_mode');

const overlays = {};
let overlayCount = 0;

// Register handlers
registerZoomHandlers(overlays);
registerPositionHandlers(overlays);
registerOverlayOpacityHandlers(overlays);
registerOverlayTrackTypeHandlers(overlays);
registerOverlayDisplayModeHandlers(overlays);
registerOverlayAutoStartModeHandlers(overlays);

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

  // By default turn off clicks/movements and turn on AlwaysOnTop
  overlay.setIgnoreMouseEvents(true);
  overlay.setMovable(false);
  overlay.setAlwaysOnTop(true, "screen-saver");

  // Disable unwanted keyboard shortcuts
  protectWindowShortcuts(overlay, { allowDevTools: isDev });
  disableZoomShortcuts(overlay);

  overlay.loadURL(`http://127.0.0.1:8000/${route}`);

  // Save user settings
  applySavedZoom(overlay, route);
  applySavedPosition(overlay, route);
  watchOverlayPosition(overlay, route);
  // opacity, track-type, display-mode, auto-start-mode is handled by a separate module

  overlay.on('closed', () => {
    delete overlays[route];
  });

  overlays[route] = overlay;
  return overlay;
}

app.whenReady().then(() => {
  registerOverlayMoveShortcuts(app, overlays);
});

module.exports = { createOverlay, overlays };

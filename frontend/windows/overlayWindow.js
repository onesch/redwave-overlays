const { app, BrowserWindow } = require('electron');
const path = require('path');
const isDev = process.env.NODE_ENV === "development";
const {
  protectWindowShortcuts,
  disableZoomShortcuts,
  registerOverlayMoveShortcuts,
  getOverlayMovementState,
  applyOverlayMovementToWindow,
} = require('../utils/keyboard_protection');
const { applySavedZoom, registerZoomHandlers } = require('../utils/overlays/zoom_range');
const { applySavedPosition, registerPositionHandlers, watchOverlayPosition } = require('../utils/overlays/overlay_position');
const { registerOverlayOpacityHandlers } = require('../utils/overlays/overlay_opacity');
const { registerOverlayTrackTypeHandlers } = require('../utils/overlays/track_type');
const { registerOverlayDisplayModeHandlers } = require('../utils/overlays/display_mode');
const { registerOverlayAutoStartModeHandlers } = require('../utils/overlays/auto_start_mode');
const { registerOverlayMovementHandlers } = require('../utils/overlays/overlay_movement');

const overlays = {};
let overlayCount = 0;

// Register handlers
registerZoomHandlers(overlays);
registerPositionHandlers(overlays);
registerOverlayOpacityHandlers(overlays);
registerOverlayTrackTypeHandlers(overlays);
registerOverlayDisplayModeHandlers(overlays);
registerOverlayAutoStartModeHandlers(overlays);
registerOverlayMovementHandlers(overlays);

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

  // Use the current shared movement state for newly opened overlays
  const isMovementEnabled = getOverlayMovementState();
  applyOverlayMovementToWindow(overlay, isMovementEnabled);
  overlay.setAlwaysOnTop(true, "screen-saver");

  // Disable unwanted keyboard shortcuts
  protectWindowShortcuts(overlay, { allowDevTools: isDev });
  disableZoomShortcuts(overlay);

  overlay.loadURL(`http://127.0.0.1:8000/${route}`);

  // Save user settings
  applySavedZoom(overlay, route);
  applySavedPosition(overlay, route);
  watchOverlayPosition(overlay, route);
  // opacity, track-type, display-mode, auto-start-mode ... is handled by a separate module

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

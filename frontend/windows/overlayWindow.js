const { app, BrowserWindow } = require('electron');
const path = require('path');
const isDev = process.env.NODE_ENV === "development";
const { getOverlayMovementState, applyOverlayMovementToWindow } = require('../utils/overlays/overlay_movement');
const { protectWindowShortcuts, disableZoomShortcuts, registerOverlayMoveShortcuts } = require('../utils/keyboard_protection');
const { applySavedZoom, registerZoomHandlers } = require('../utils/overlays/features/shared/zoom_range');
const { applySavedPosition, registerPositionHandlers, watchOverlayPosition } = require('../utils/overlays/overlay_position');
const { registerOverlayOpacityHandlers } = require('../utils/overlays/features/shared/overlay_opacity');
const { registerOverlayTrackTypeHandlers } = require('../utils/overlays/features/track-map/track_type');
const { registerOverlayDisplayModeHandlers } = require('../utils/overlays/features/shared/display_mode');
const { registerOverlayAutoStartModeHandlers } = require('../utils/overlays/features/shared/auto_start_mode');
const { registerOverlayMovementHandlers } = require('../utils/overlays/overlay_movement');
const { registerOverlayRadarVisibilityHandlers } = require('../utils/overlays/features/radar/radar_visibility_mode');
const { registerLastLapFormatHandlers } = require('../utils/overlays/features/leaderboard/last_lap_format');
const { registerSpeedUnitHandlers } = require('../utils/overlays/features/telemetry/speed_unit');

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
registerOverlayRadarVisibilityHandlers(overlays);
registerLastLapFormatHandlers(overlays);
registerSpeedUnitHandlers(overlays);

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
    resizable: isDev,
    movable: false,
    focusable: true,
    hasShadow: false,
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

// Close every open overlay, e.g. when the main window goes away.
// Overlays save their position on close, so this must use close(), not destroy().
function closeAllOverlays() {
  Object.values(overlays).forEach((overlay) => {
    if (!overlay.isDestroyed()) {
      overlay.close();
    }
  });
}

app.whenReady().then(() => {
  registerOverlayMoveShortcuts(app, overlays);
});

module.exports = { createOverlay, closeAllOverlays, overlays };

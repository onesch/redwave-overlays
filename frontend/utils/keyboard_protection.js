const { loadSettings, saveSettings } = require('./overlays/overlay_settings');

// Settings key used to persist overlay movement mode
// (false = locked, true = movable)
const overlayMovementEnabledSettingKey =
  'isOverlayMovementEnabled';
// Shared movement state for all overlay windows
let overlayMovementEnabled = false;
// Prevent repeated settings reads after first initialization
let overlayMovementStateLoaded = false;


function protectWindowShortcuts(win, { allowDevTools = false } = {}) {
  win.webContents.on('before-input-event', (event, input) => {
    // F12 (devtools)
    if (input.type === 'keyDown' && input.key === 'F12') {
      if (allowDevTools) {
        win.webContents.toggleDevTools();
        const show = !win.isMenuBarVisible();
        win.setMenuBarVisibility(show);
        win.autoHideMenuBar = !show;
      }
      event.preventDefault();
      return;
    }

    // F11 (fullscreen)
    if (input.type === 'keyDown' && input.key === 'F11') {
      event.preventDefault();
      return;
    }

    // Ctrl+Shift+I (devtools)
    if (input.control && input.shift && input.key.toUpperCase() === 'I') {
      event.preventDefault();
      return;
    }
  });
}

function disableZoomShortcuts(win) {
  win.webContents.on('before-input-event', (event, input) => {
    // Block Ctrl++ / Ctrl+=, Ctrl+- and Ctrl+0
    if (input.control || input.meta) {
      const blockedKeys = ['+', '=', '-', '0'];
      if (blockedKeys.includes(input.key)) {
        event.preventDefault();
      }
    }
  });
}

function registerOverlayMoveShortcuts(app, overlays) {
  const { globalShortcut } = require('electron');
  // Global shortcut to quickly switch all overlays between locked and movable states
  globalShortcut.register('Control+Shift+P', () => {
    toggleOverlayMovement(overlays);
  });
}

function ensureOverlayMovementStateLoaded() {
  // retrieves the state from the file once
  if (overlayMovementStateLoaded) return;

  const settings = loadSettings();
  overlayMovementEnabled = Boolean(settings[overlayMovementEnabledSettingKey]);
  overlayMovementStateLoaded = true;
}

function persistOverlayMovementState() {
  // Save value to settings after each toggleOverlayMovement
  const settings = loadSettings();
  settings[overlayMovementEnabledSettingKey] = overlayMovementEnabled;
  saveSettings(settings);
}

function applyOverlayMovement(overlays, isMovable) {
  // Apply the requested movement mode to every currently opened overlay window
  Object.values(overlays).forEach((win) => {
    if (!win.isDestroyed()) {
      // If movable, allow mouse clicks
      win.setIgnoreMouseEvents(!isMovable);
      win.setMovable(isMovable);
    }
  });
}

function toggleOverlayMovement(overlays) {
  // Flip current mode and immediately propagate it to all active overlays
  const { BrowserWindow } = require('electron');
  ensureOverlayMovementStateLoaded();
  overlayMovementEnabled = !overlayMovementEnabled;
  persistOverlayMovementState();
  applyOverlayMovement(overlays, overlayMovementEnabled);

  BrowserWindow.getAllWindows().forEach((win) => {
    if (!win.isDestroyed()) {
      win.webContents.send('overlay-movement-state-updated', overlayMovementEnabled);
    }
  });
  return overlayMovementEnabled;
}

function getOverlayMovementState() {
  // Read current global movement mode for UI and IPC consumers
  ensureOverlayMovementStateLoaded();
  return overlayMovementEnabled;
}

module.exports = {
  protectWindowShortcuts,
  disableZoomShortcuts,
  registerOverlayMoveShortcuts,
  toggleOverlayMovement,
  getOverlayMovementState,
};

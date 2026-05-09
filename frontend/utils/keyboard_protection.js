const { BrowserWindow } = require('electron');
const { loadSettings, saveSettings } = require('./overlays/overlay_settings');

// Settings key (persistent storage)
const OVERLAY_MOVEMENT_KEY = '__isOverlayMovementEnabled';

// In-memory state (cached)
let overlayMovementEnabled = false;
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

// Retrieves the state from the settings file once
function loadOverlayMovementStateOnce() {
  if (overlayMovementStateLoaded) return;

  const settings = loadSettings();
  overlayMovementEnabled = Boolean(settings[OVERLAY_MOVEMENT_KEY]);
  overlayMovementStateLoaded = true;
}

// Save value to settings file
function saveOverlayMovementState() {
  const settings = loadSettings();
  settings[OVERLAY_MOVEMENT_KEY] = overlayMovementEnabled;
  saveSettings(settings);
}

// Get current global movement state for UI and IPC consumers
function getOverlayMovementState() {
  loadOverlayMovementStateOnce();
  return overlayMovementEnabled;
}

function applyOverlayMovement(overlays, isMovable) {  // ! needs improvement
  // Apply the requested movement mode to every currently opened overlay window
  Object.values(overlays).forEach((win) => {
    if (!win.isDestroyed()) {
      // If movable, allow mouse clicks
      win.setIgnoreMouseEvents(!isMovable);
      win.setMovable(isMovable);
    }
  });
}

function toggleOverlayMovement(overlays) {  // ! needs improvement
  // Flip current mode and immediately propagate it to all active overlays
  loadOverlayMovementStateOnce();
  overlayMovementEnabled = !overlayMovementEnabled;
  saveOverlayMovementState();
  applyOverlayMovement(overlays, overlayMovementEnabled);

  BrowserWindow.getAllWindows().forEach((win) => {
    if (!win.isDestroyed()) {
      win.webContents.send('overlay-movement-state-updated', overlayMovementEnabled);
    }
  });
  return overlayMovementEnabled;
}

module.exports = {
  protectWindowShortcuts,
  disableZoomShortcuts,
  registerOverlayMoveShortcuts,
  toggleOverlayMovement,
  getOverlayMovementState,
};

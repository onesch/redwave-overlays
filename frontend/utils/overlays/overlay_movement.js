const { ipcMain } = require('electron');
const { BrowserWindow } = require('electron');
const { loadSettings, saveSettings } = require('./overlay_settings');

// Settings key (persistent storage)
const OVERLAY_MOVEMENT_KEY = '__isOverlayMovementEnabled';
// In-memory state (cached)
let overlayMovementEnabled = false;
let overlayMovementStateLoaded = false;

// Register IPC handlers for managing overlay movement.
function registerOverlayMovementHandlers(overlays) {
  ipcMain.handle('update-overlay-movement-state', () => updateOverlayMovementState(overlays));
  ipcMain.handle('get-overlay-movement-state', () => getOverlayMovementState());
}

// Load the state from the settings file once
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

// Apply the requested movement mode to every currently opened overlay window
function applyOverlayMovementState(overlays, isMovementEnabled) {
  Object.values(overlays).forEach((win) => {
    if (!win.isDestroyed()) {
      // If movable, allow mouse clicks
      win.setIgnoreMouseEvents(!isMovementEnabled);
      win.setMovable(isMovementEnabled);
    }
  });
}

// Update (flip) current mode and apply it to all active overlays
function updateOverlayMovementState(overlays) {
  loadOverlayMovementStateOnce();
  overlayMovementEnabled = !overlayMovementEnabled;
  saveOverlayMovementState();
  applyOverlayMovementState(overlays, overlayMovementEnabled);

  BrowserWindow.getAllWindows().forEach((win) => {
    if (!win.isDestroyed()) {
      // Broadcast updated movement state to all renderer windows
      // Used by OverlayBase.applyOverlayMovementState in base_detail.js
      // (its needed to visually update the icons in the UI).
      win.webContents.send('overlay-movement-state-updated', overlayMovementEnabled);
    }
  });
  return overlayMovementEnabled;
}

// Helper apply-function for single window
function applyOverlayMovementToWindow(win, isMovementEnabled) {
  win.setIgnoreMouseEvents(!isMovementEnabled);
  win.setMovable(isMovementEnabled);
}

module.exports = { 
  registerOverlayMovementHandlers,
  updateOverlayMovementState,
  getOverlayMovementState,
  applyOverlayMovementToWindow,
};

const { ipcMain } = require('electron');
const { toggleOverlayMovement, getOverlayMovementState } = require('../keyboard_protection');

// Register IPC handlers for managing overlay movement.
function registerOverlayMovementHandlers(overlays) {
  ipcMain.handle('toggle-overlay-movement', () => toggleOverlayMovement(overlays));
  ipcMain.handle('get-overlay-movement-state', () => getOverlayMovementState());
}

module.exports = { registerOverlayMovementHandlers };

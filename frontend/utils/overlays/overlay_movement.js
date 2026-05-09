const { ipcMain } = require('electron');
const { updateOverlayMovementState, getOverlayMovementState } = require('../keyboard_protection');

// Register IPC handlers for managing overlay movement.
function registerOverlayMovementHandlers(overlays) {
  ipcMain.handle('update-overlay-movement-state', () => updateOverlayMovementState(overlays));
  ipcMain.handle('get-overlay-movement-state', () => getOverlayMovementState());
}

module.exports = { registerOverlayMovementHandlers };

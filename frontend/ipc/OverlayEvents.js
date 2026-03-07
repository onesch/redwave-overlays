const { ipcMain } = require('electron');
const { createOverlay } = require('../windows/overlayWindow');
const overlayConfig = require('../windows/overlays_config');

// Registers IPC event for a given overlay name
function registerOverlayEvent(overlayName) {
  ipcMain.on(`open-${overlayName}`, () => {
    const { baseSize } = overlayConfig[overlayName];

    createOverlay(overlayName, {
      width: baseSize.width,
      height: baseSize.height,
    });
  });
}

// Registers IPC events for all overlays defined in overlays_config
function registerAllOverlayEvents() {
  Object.keys(overlayConfig).forEach(registerOverlayEvent);
}

module.exports = { registerOverlayEvent, registerAllOverlayEvents };

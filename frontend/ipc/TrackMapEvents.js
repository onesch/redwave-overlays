const { ipcMain } = require('electron');
const { createOverlay } = require('../windows/overlayWindow');
const overlayConfig = require('../windows/overlays_config');

const OVERLAY_NAME = 'track-map';

function registerTrackMapEvents() {
  ipcMain.on(`open-${OVERLAY_NAME}`, () => {
    const { baseSize } = overlayConfig[OVERLAY_NAME];

    createOverlay(OVERLAY_NAME, {
      width: baseSize.width,
      height: baseSize.height,
    });
  });
}

module.exports = registerTrackMapEvents;

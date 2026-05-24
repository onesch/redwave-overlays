const { ipcMain } = require('electron');
const { app } = require('electron');
const path = require('path');
const fs = require('fs');
const { execFile } = require('child_process');
const { resetSettings } = require('../utils/overlays/overlay_settings');
const { overlays } = require('../windows/overlayWindow');
const { clearZoomCache } = require('../utils/overlays/zoom_range');

function registerSettingsEvents() {
  ipcMain.on('reset-overlay-settings', () => {
    // Сlose all overlays
    for (const overlay of Object.values(overlays)) {
        if (!overlay.isDestroyed()) overlay.destroy();
    }

    // delete settings file
    resetSettings();
    
    // Clear zoom cache
    clearZoomCache();
  });

  ipcMain.on('uninstall-app', () => {
    const appExePath = app.getPath('exe');
    const appDirPath = path.dirname(appExePath);

    // Build the path to the uninstaller executable
    const uninstallPath = path.join(
      appDirPath,
      'Uninstall RedWave overlays.exe'
    );

    // Check if the uninstaller exists
    if (!fs.existsSync(uninstallPath)) {
      console.error(`Uninstaller not found: ${uninstallPath}`);
      return;
    }

    // Launch the uninstaller process
    execFile(uninstallPath, (error) => {
      if (error) {
        console.error(`Failed to start uninstaller: ${error.message}`);
        return;
      }

      // Quit the app after starting the uninstaller
      app.quit();
    });
  });
}

module.exports = registerSettingsEvents;

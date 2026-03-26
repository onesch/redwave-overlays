const { ipcMain } = require('electron');
const { loadSettings, saveSettings } = require('./overlay_settings');

// Registers IPC handlers for overlay setting.
function registerOverlaySetting({
  overlays,
  getChannel,
  setChannel,
  settingKey,
  defaultValue,
  updateEvent,
  afterSet,
  afterGet,
}) {
  // Handle request to get a setting value for an overlay.
  ipcMain.handle(getChannel, (e, overlayName) => {
    const settings = loadSettings();

    // Load value from settings or fallback to default.
    let value = settings[overlayName]?.[settingKey] ?? defaultValue;

    // Optional hook to modify value before returning it.
    if (afterGet) {
      value = afterGet({ overlayName, value, settings });
    }

    return value;
  });

  // Handle request to update a setting value.
  ipcMain.on(setChannel, (e, { overlayName, value }) => {
    const settings = loadSettings();

    // Ensure overlay settings object exists.
    settings[overlayName] ||= {};
    settings[overlayName][settingKey] = value;

    // Persist updated settings to disk.
    saveSettings(settings);

    // Optional hook for additional side effects after setting update.
    // Run afterSet before overlay check so in-memory state (e.g. cache)
    if (afterSet) {
      afterSet({ overlay: overlays[overlayName], overlayName, value, settings });
    }

    const overlay = overlays[overlayName];
    if (!overlay || overlay.isDestroyed()) return;

    // Notify renderer about the updated value if needed.
    if (updateEvent) {
      overlay.webContents.send(updateEvent, value);
    }
  });
}

module.exports = { registerOverlaySetting };

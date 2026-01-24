const { app } = require('electron');
const fs = require('fs');
const path = require('path');

const SETTINGS_PATH = path.join(
  app.getPath('userData'),
  'overlays_settings.json'
);

function loadSettings() {
  try {
    if (fs.existsSync(SETTINGS_PATH)) {
      const data = fs.readFileSync(SETTINGS_PATH, 'utf-8');
      return JSON.parse(data);
    }
  } catch (err) {
    console.error('[settings] Failed to load settings:', err);
  }
  return {};
}

function saveSettings(settings) {
  try {
    fs.writeFileSync(SETTINGS_PATH, JSON.stringify(settings, null, 2), 'utf-8');
  } catch (err) {
    console.error('[settings] Failed to save settings:', err);
  }
}

function resetSettings() {
  try {
    if (fs.existsSync(SETTINGS_PATH)) {
      fs.unlinkSync(SETTINGS_PATH);
    }
  } catch (err) {
    console.error('[settings] Failed to reset settings:', err);
  }
}

module.exports = { loadSettings, saveSettings, resetSettings };

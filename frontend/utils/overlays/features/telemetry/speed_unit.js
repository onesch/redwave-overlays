const { registerOverlaySetting } = require('../../base_handler');

const DEFAULT_SPEED_UNIT = 'kmh';
const SPEED_UNITS = new Set([DEFAULT_SPEED_UNIT, 'mph']);

function normalizeSpeedUnit(value) {
  return SPEED_UNITS.has(value) ? value : DEFAULT_SPEED_UNIT;
}

function registerSpeedUnitHandlers(overlays) {
  registerOverlaySetting({
    overlays,
    getChannel: 'get-speed-unit',
    setChannel: 'set-speed-unit',
    settingKey: 'SpeedUnit',
    defaultValue: DEFAULT_SPEED_UNIT,
    updateEvent: 'update-speed-unit',
    afterGet: ({ value }) => normalizeSpeedUnit(value),
    normalizeValue: normalizeSpeedUnit,
  });
}

module.exports = {
  DEFAULT_SPEED_UNIT,
  SPEED_UNITS,
  normalizeSpeedUnit,
  registerSpeedUnitHandlers,
};

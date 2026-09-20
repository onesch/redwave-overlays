const { registerOverlaySetting } = require('./base_handler');

const DEFAULT_LAST_LAP_FORMAT = 'MM:SS.sss';
const LAST_LAP_FORMATS = new Set([
  DEFAULT_LAST_LAP_FORMAT,
  'MM:SS.ss',
  'SS.sss',
  'SS.ss',
]);

function normalizeLastLapFormat(value) {
  return LAST_LAP_FORMATS.has(value) ? value : DEFAULT_LAST_LAP_FORMAT;
}

function registerLastLapFormatHandlers(overlays) {
  registerOverlaySetting({
    overlays,
    getChannel: 'get-last-lap-format',
    setChannel: 'set-last-lap-format',
    settingKey: 'LastLapFormat',
    defaultValue: DEFAULT_LAST_LAP_FORMAT,
    updateEvent: 'update-last-lap-format',
    afterGet: ({ value }) => normalizeLastLapFormat(value),
    normalizeValue: normalizeLastLapFormat,
  });
}

module.exports = {
  DEFAULT_LAST_LAP_FORMAT,
  LAST_LAP_FORMATS,
  normalizeLastLapFormat,
  registerLastLapFormatHandlers,
};
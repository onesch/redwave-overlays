// Public surface of the overlay detail pages. Templates import from
// here and stay declarative: pick the overlay name and its extra settings.
export { mountOverlaySettings } from './mountOverlaySettings.js';
export { createSettingsApi } from './electronApiAdapter.js';
export { createLastLapFormatSetting } from './features/leaderboard/lastLapFormatSetting.js';
export { createRadarVisibilitySetting } from './features/radar/radarVisibilitySetting.js';
export { createTrackTypeSetting } from './features/track-map/trackTypeSetting.js';
export { createSpeedUnitSetting } from './features/telemetry/speedUnitSetting.js';

export { createSettingsScroll } from './settingsScroll.js';

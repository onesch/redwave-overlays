import { createSettingsApi } from './electronApiAdapter.js';
import { createOpenOverlayControl, createMovementToggle } from './overlayWindowControls.js';
import { createZoomSetting } from './features/shared/zoomSetting.js';
import { createBackgroundOpacitySetting } from './features/shared/backgroundOpacitySetting.js';
import { createDisplayModeSetting } from './features/shared/displayModeSetting.js';
import { createAutoStartSetting } from './features/shared/autoStartSetting.js';
import { createSettingsScroll } from './settingsScroll.js';

export { createSettingsScroll };

// Settings shared by every overlay detail page.
const SHARED_SETTINGS = [
  createZoomSetting,
  createBackgroundOpacitySetting,
  createDisplayModeSetting,
  createAutoStartSetting,
];

// Compose the settings in detail page for one overlay: shared settings, the
// page-specific settings it declares, and the global overlay controls.
// Returns a promise that settles once every feature has loaded; loading
// failures are logged and never break the rest of the page.
export async function mountOverlaySettings({
  overlayName,
  settings = [],
  document = globalThis.document,
  window = globalThis.window,
  api = createSettingsApi(),
} = {}) {
  const context = { api, overlayName, document, window };
  const features = [
    ...SHARED_SETTINGS.map((createSetting) => createSetting(context)),
    ...settings.map((createSetting) => createSetting(context)),
    createOpenOverlayControl(context),
    createMovementToggle(context),
    createSettingsScroll(context),
  ];

  const results = await Promise.allSettled(
    features.map((feature) => feature.mount()),
  );

  for (const result of results) {
    if (result.status === 'rejected') {
      console.error('Unable to load setting:', result.reason);
    }
  }
}

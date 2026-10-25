import { createButtonGroup } from '../../settingWidgets.js';

// Telemetry-specific setting: speed unit used by every speed readout.
export function createSpeedUnitSetting({ api, overlayName, document }) {
  return {
    async mount() {
      const group = createButtonGroup({
        buttons: {
          kmh: document.getElementById('kmhBtn'),
          mph: document.getElementById('mphBtn'),
        },
      });

      group.onSelect((unit) => {
        api.setSpeedUnit(overlayName, unit);
        group.select(unit);
      });

      // Keep the HTML default (km/h) when the value is unavailable.
      const unit = await api.getSpeedUnit(overlayName);
      if (unit) group.setFromLoad(unit);
    },
  };
}

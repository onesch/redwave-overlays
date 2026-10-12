import { createButtonGroup } from '../../settingWidgets.js';

// Radar-specific setting: visibility mode when no cars are nearby.
export function createRadarVisibilitySetting({ api, overlayName, document }) {
  return {
    async mount() {
      const group = createButtonGroup({
        buttons: {
          hide: document.getElementById('hideBtn'),
          dim: document.getElementById('dimBtn'),
          show: document.getElementById('showBtn'),
        },
      });

      group.onSelect((mode) => {
        api.setRadarVisibility(overlayName, mode);
        group.select(mode);
      });

      group.setFromLoad(await api.getRadarVisibility(overlayName));
    },
  };
}

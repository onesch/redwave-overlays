import { createButtonGroup } from '../../settingWidgets.js';

// Track-map-specific setting: track type selector that also swaps the
// preview image (Linear / Circle / Track).
export function createTrackTypeSetting({ api, overlayName, document }) {
  return {
    async mount() {
      const group = createButtonGroup({
        buttons: {
          linear: document.getElementById('linearBtn'),
          circle: document.getElementById('circleBtn'),
          track: document.getElementById('trackBtn'),
        },
      });
      const preview = document.getElementById('trackImage');

      const applyPreview = (type) => {
        const image = preview?.dataset?.[type];
        if (image) preview.src = image;
      };

      group.onSelect((type) => {
        api.setTrackType(overlayName, type);
        group.select(type);
        applyPreview(type);
      });

      const type = await api.getTrackType(overlayName);
      if (group.setFromLoad(type)) applyPreview(type);
    },
  };
}

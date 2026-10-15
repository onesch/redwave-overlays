import { createSliderField } from '../../settingWidgets.js';

// Per-overlay zoom slider shared by every overlay settings page.
export function createZoomSetting({ api, overlayName, document }) {
  return {
    async mount() {
      const field = createSliderField({
        input: document.getElementById('zoomRange'),
        label: document.getElementById('zoomValue'),
        format: (percent) => `${percent}%`,
      });

      field.onInput((percent) => {
        api.setZoom(overlayName, percent / 100);
      });

      const zoomFactor = await api.getZoom(overlayName);
      const percent = Math.round(zoomFactor * 100);

      // Ignore unusable values (e.g. a missing IPC channel) and
      // keep the HTML defaults instead of rendering "NaN%".
      if (Number.isFinite(percent)) field.setFromLoad(percent);
    },
  };
}

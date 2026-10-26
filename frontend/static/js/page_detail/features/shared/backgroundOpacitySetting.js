import { createSliderField } from '../../settingWidgets.js';

// Per-overlay background opacity slider. Only some pages render the
// control (e.g. leaderboard and telemetry do, radar and track-map do not),
// so mounting is a no-op when neither DOM element exists.
export function createBackgroundOpacitySetting({ api, overlayName, document }) {
  return {
    async mount() {
      const input = document.getElementById('opacityRange');
      const label = document.getElementById('opacityValue');
      if (!input && !label) return;

      const field = createSliderField({
        input,
        label,
        format: (value) => Number(value).toFixed(2),
      });

      field.onInput((value) => {
        api.setBackgroundOpacity(overlayName, parseFloat(value));
      });

      const opacity = await api.getBackgroundOpacity(overlayName);
      if (opacity != null) field.setFromLoad(opacity);
    },
  };
}

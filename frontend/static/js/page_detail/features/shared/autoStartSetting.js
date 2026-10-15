import { createButtonGroup } from '../../settingWidgets.js';

// Per-overlay auto-start mode (On / Off) shared by every overlay
// settings page.
export function createAutoStartSetting({ api, overlayName, document }) {
  return {
    async mount() {
      const group = createButtonGroup({
        buttons: {
          on: document.getElementById('AutoStartOnBtn'),
          off: document.getElementById('AutoStartOffBtn'),
        },
    });

    group.onSelect((value) => {
      api.setAutoStartMode(overlayName, value);
        group.select(value);
      });

    const value = await api.getAutoStartMode(overlayName);
      group.setFromLoad(value ?? 'off');
    },
  };
}

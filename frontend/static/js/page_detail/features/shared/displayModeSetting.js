import { createButtonGroup } from '../../settingWidgets.js';

// Per-overlay display mode (All Time / Track / Garage) shared by every
// overlay settings page.
export function createDisplayModeSetting({ api, overlayName, document }) {
  return {
    async mount() {
      const group = createButtonGroup({
        buttons: {
          all_time: document.getElementById('DisplayAllTimeBtn'),
          track: document.getElementById('DisplayTrackBtn'),
          garage: document.getElementById('DisplayGarageBtn'),
        },
      });

      group.onSelect((mode) => {
        api.setDisplayMode(overlayName, mode);
        group.select(mode);
      });

      const mode = await api.getDisplayMode(overlayName);
        group.setFromLoad(mode ?? 'all_time');
    },
  };
}

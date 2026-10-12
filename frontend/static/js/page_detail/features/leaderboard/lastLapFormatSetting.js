// Leaderboard-specific setting: Last Lap time format select.
export function createLastLapFormatSetting({ api, overlayName, document }) {
  return {
    async mount() {
      const select = document.getElementById('lastLapFormat');
      if (!select) return;

      // The select is a one-off control without a shared helper,
      // so it guards the late load reply with an explicit flag.
      let interacted = false;
      select.addEventListener('change', () => {
        interacted = true;
        api.setLastLapFormat(overlayName, select.value);
      });

      const format = await api.getLastLapFormat(overlayName);
      if (!interacted && format != null) select.value = format;
    },
  };
}

// Global overlay controls: actions shared by every detail page that
// affect overlay windows rather than a single overlay's settings.

// The Open button launches the overlay window for the current page.
export function createOpenOverlayControl({ api, overlayName, document }) {
  return {
    mount() {
      document
        .getElementById('OpenBtn')
        ?.addEventListener('click', () => api.openOverlay(overlayName));
    },
  };
}

// Movement lock toggle: flips the global "overlay movement" mode and
// mirrors the current state (icon + highlight) on the button.
export function createMovementToggle({ api, document }) {
  return {
    async mount() {
      const button = document.getElementById('ToggleMovementBtn');

      const render = (isMovementEnabled) => {
        if (!button) return;

        // Treat a missing state (e.g. an absent IPC channel) as
        // "disabled": classList.toggle(name, undefined) would
        // flip the highlight instead of clearing it.
        const enabled = Boolean(isMovementEnabled);

        button.innerHTML = `
          <span class="material-symbols-outlined">
            ${enabled ? 'lock_open_right' : 'lock'}
          </span>
        `;
        button.classList.toggle('primary-btn', enabled);
      };

      // Keep the button in sync when the mode changes elsewhere
      // (e.g. the ctrl+shift+P hotkey or another settings page).
      api.onMovementStateChange(render);

      if (!button) return;

      button.addEventListener('click', async () => {
        render(await api.toggleMovementState());
      });
      render(await api.getMovementState());
    },
  };
}

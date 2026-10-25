// Single access point for the Electron IPC channels used by the
// overlay settings in detail pages. Everything else works against this facade,
// so the preload surface is only referenced in one place and can be
// faked in tests.
export function createSettingsApi(
  electronAPI = globalThis.window?.electronAPI,
) {
  if (!electronAPI) {
    // Page opened outside Electron (or preload failed): the page
    // still renders its HTML defaults, but nothing can be loaded
    // or persisted. Surface the misconfiguration once.
    console.warn(
      'window.electronAPI is unavailable; '
      + 'overlay settings will not be loaded or saved',
    );
    electronAPI = {};
  }

  return {
    // Overlay window control.
    openOverlay: (overlayName) =>
      electronAPI.openOverlay?.(overlayName),

    // Per-overlay zoom.
    getZoom: (overlayName) => 
      electronAPI.getOverlayZoom?.(overlayName),
    setZoom: (overlayName, zoomFactor) =>
      electronAPI.setOverlayZoom?.(overlayName, zoomFactor),

    // Per-overlay background opacity.
    getBackgroundOpacity: (overlayName) =>
      electronAPI.getOverlayBgOpacity?.(overlayName),
    setBackgroundOpacity: (overlayName, value) =>
      electronAPI.setOverlayBgOpacity?.(overlayName, value),

    // Per-overlay display mode (all_time / track / garage).
    getDisplayMode: (overlayName) =>
      electronAPI.getDisplayMode?.(overlayName),
    setDisplayMode: (overlayName, value) =>
      electronAPI.setDisplayMode?.(overlayName, value),

    // Per-overlay auto-start mode (on / off).
    getAutoStartMode: (overlayName) =>
      electronAPI.getAutoStartMode?.(overlayName),
    setAutoStartMode: (overlayName, value) =>
      electronAPI.setAutoStartMode?.(overlayName, value),

    // Global overlay movement state (shared by every overlay window).
    getMovementState: () =>
      electronAPI.getOverlayMovementState?.(),
    toggleMovementState: () =>
      electronAPI.updateOverlayMovementState?.(),
    onMovementStateChange: (listener) =>
      electronAPI.onOverlayMovementStateUpdate?.(listener),

    // Leaderboard Last Lap time format.
    getLastLapFormat: (overlayName) =>
      electronAPI.getLastLapFormat?.(overlayName),
    setLastLapFormat: (overlayName, value) =>
      electronAPI.setLastLapFormat?.(overlayName, value),

    // Radar visibility mode (dim / show / hide).
    getRadarVisibility: (overlayName) =>
      electronAPI.getRadarVisibility?.(overlayName),
    setRadarVisibility: (overlayName, value) =>
      electronAPI.setRadarVisibility?.(overlayName, value),

    // Telemetry speed unit (kmh / mph).
    getSpeedUnit: (overlayName) =>
      electronAPI.getSpeedUnit?.(overlayName),
    setSpeedUnit: (overlayName, value) =>
      electronAPI.setSpeedUnit?.(overlayName, value),

    // Track-map track type (linear / circle / track).
    getTrackType: (overlayName) =>
      electronAPI.getTrackType?.(overlayName),
    setTrackType: (overlayName, value) =>
      electronAPI.setTrackType?.(overlayName, value),
  };
}

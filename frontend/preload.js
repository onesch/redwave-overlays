const { contextBridge, ipcRenderer } = require('electron');

contextBridge.exposeInMainWorld('electronAPI', {
  // Overlays
  openRadar: () => ipcRenderer.send('open-radar'),
  openLeaderboard: () => ipcRenderer.send('open-leaderboard'),
  openTrackMap: () => ipcRenderer.send('open-track-map'),

  // Zoom
  setOverlayZoom: (overlayName, zoomFactor) =>
    ipcRenderer.send('set-overlay-zoom', { overlayName, value: zoomFactor }),
  getOverlayZoom: (overlayName) =>
    ipcRenderer.invoke('get-overlay-zoom', overlayName),

  // Position
  setOverlayPosition: (overlayName, x, y) =>
    ipcRenderer.send('set-overlay-position', { overlayName, x, y }),
  getOverlayPosition: (overlayName) =>
    ipcRenderer.invoke('get-overlay-position', overlayName),

  // Opacity
  setCardBgOpacity: (overlayName, value) =>
      ipcRenderer.send('set-card-bg-opacity', { overlayName, value }),
  getCardBgOpacity: (overlayName) =>
      ipcRenderer.invoke('get-card-bg-opacity', overlayName),
  onCardBgOpacityUpdate: (callback) =>
    ipcRenderer.on('update-card-opacity', (_, value) => callback(value)),

  // Track type
  setTrackType: (overlayName, value) =>
    ipcRenderer.send('set-track-map-type', { overlayName, value }),
  getTrackType: (overlayName) =>
    ipcRenderer.invoke('get-track-map-type', overlayName),
  onTrackTypeUpdate: (callback) =>
    ipcRenderer.on('update-track-map-type', (_, type) => callback(type)),

  // Display mode
  setDisplayMode: (overlayName, value) =>
    ipcRenderer.send('set-display-mode', { overlayName, value }),
  getDisplayMode: (overlayName) =>
    ipcRenderer.invoke('get-display-mode', overlayName),
  onDisplayModeUpdate: (callback) =>
    ipcRenderer.on('update-display-mode', (_, value) => callback(value)),

  // Auto-Start mode
  setAutoStartMode: (overlayName, value) =>
    ipcRenderer.send('set-auto-start-mode', { overlayName, value }),
  getAutoStartMode: (overlayName) =>
    ipcRenderer.invoke('get-auto-start-mode', overlayName),
  onAutoStartModeUpdate: (callback) =>
    ipcRenderer.on('update-auto-start-mode', (_, value) => callback(value)),

  // Reset overlay settings
  resetOverlaySettings: () =>
    ipcRenderer.send('reset-overlay-settings')
});

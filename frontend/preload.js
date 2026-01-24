const { contextBridge, ipcRenderer } = require('electron');

contextBridge.exposeInMainWorld('electronAPI', {
  openRadar: () => ipcRenderer.send('open-radar'),
  openLeaderboard: () => ipcRenderer.send('open-leaderboard'),

  // Zoom
  setOverlayZoom: (overlayName, zoomFactor) =>
    ipcRenderer.send('set-overlay-zoom', { overlayName, zoomFactor }),
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

  // Reset overlay settings
  resetOverlaySettings: () =>
    ipcRenderer.send('reset-overlay-settings')
});

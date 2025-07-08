const { contextBridge, ipcRenderer } = require('electron');

contextBridge.exposeInMainWorld('electronAPI', {
  openSpeed: () => ipcRenderer.send('open-speed'),
  openControls: () => ipcRenderer.send('open-controls')
});

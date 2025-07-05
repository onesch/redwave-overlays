const { app, BrowserWindow } = require('electron');
const path = require('path');

function createWindow() {
  const win = new BrowserWindow({
    width: 800,
    height: 600,
    webPreferences: {
      // если нужен preload — укажи здесь
      // preload: path.join(__dirname, 'preload.js'),
      nodeIntegration: false,
      contextIsolation: true,
    },
  });

  // Загружаем фронтенд из локального файла
  win.loadFile('frontend/index.html');

  win.on('closed', () => {
    // Здесь можно добавить очистку ресурсов, если надо
  });
}

app.whenReady().then(() => {
  createWindow();

  app.on('activate', () => {
    // На macOS принято заново создавать окно, если все закрыты
    if (BrowserWindow.getAllWindows().length === 0) createWindow();
  });
});

app.on('window-all-closed', () => {
  // Закрываем приложение, кроме macOS
  if (process.platform !== 'darwin') {
    app.quit();
  }
});

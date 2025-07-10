const { app, BrowserWindow, ipcMain } = require('electron');
const path = require('path');
const isDev = !app.isPackaged;

let mainWindow = null;

/**
 * Универсальная функция создания нового окна
 * @param {string} route - путь к FastAPI-роуту
 * @param {object} options - дополнительные параметры окна
 */
function createWindow(route, options = {}) {
  const win = new BrowserWindow({
    width: options.width || 400,
    height: options.height || 300,
    transparent: options.transparent ?? true,
    frame: options.frame ?? false,
    resizable: options.resizable ?? false,
    alwaysOnTop: true,
    webPreferences: {
      contextIsolation: true,
      preload: path.join(__dirname, 'preload.js'),
    },
    ...options.override,
  });

  win.loadURL(`http://localhost:8000/${route}`);
}


// Главное окно
function createMainWindow() {
  mainWindow = new BrowserWindow({
    width: 800,
    height: 600,
    title: "Main",
    webPreferences: {
      contextIsolation: true,
      preload: path.join(__dirname, 'preload.js'),
    },
  });

  if (!isDev) {
    mainWindow.setMenu(null);
  }


  // Открыть DevTools по умолчанию (опционально)
  // mainWindow.webContents.openDevTools();

  // Добавляем глобальный слушатель клавиши F12
  mainWindow.webContents.on('before-input-event', (event, input) => {
    if (input.type === 'keyDown' && input.key === 'F12') {
      mainWindow.webContents.toggleDevTools();
    }
  });

  mainWindow.loadURL('http://localhost:8000/main_window');

  mainWindow.on('closed', () => {
    mainWindow = null;
  });
}


// 📡 IPC: слушатели
ipcMain.on('open-speed', () =>
  createWindow('speed', {
    width: 400,
    height: 250,
    resizable: false,
    transparent: true,
    frame: false,
  })
);

ipcMain.on('open-controls', () =>
  createWindow('controls', {
    width: 450,
    height: 300,
    resizable: false,
    transparent: true,
    frame: false,
  }
)
);


// Запуск
app.whenReady().then(() => {
  createMainWindow();
});

app.on('window-all-closed', () => {
  if (process.platform !== 'darwin') app.quit();
});

const { ipcMain, screen } = require('electron');

// Registers IPC events for the custom title bar of the main window
function registerWindowEvents(getWindow) {
  let dragOffset = null;

  // The window is created once and recreated when the app is reactivated,
  // so it is resolved lazily and treated as gone once destroyed.
  function resolveWindow() {
    const win = typeof getWindow === 'function' ? getWindow() : getWindow;
    return win && !win.isDestroyed() ? win : null;
  }

  ipcMain.on('window-minimize', () => {
    const win = resolveWindow();
    if (win) win.minimize();
  });

  ipcMain.on('window-close', () => {
    const win = resolveWindow();
    if (win) win.close();
  });

  // Remember where inside the window the drag started, so the window keeps
  // that offset under the cursor instead of jumping to it.
  ipcMain.on('window-drag-start', () => {
    const win = resolveWindow();
    if (!win) return;

    const cursor = screen.getCursorScreenPoint();
    const [x, y] = win.getPosition();

    dragOffset = { x: cursor.x - x, y: cursor.y - y };
  });

  ipcMain.on('window-drag-move', () => {
    const win = resolveWindow();
    if (!dragOffset || !win) return;

    const cursor = screen.getCursorScreenPoint();
    win.setPosition(cursor.x - dragOffset.x, cursor.y - dragOffset.y);
  });

  ipcMain.on('window-drag-end', () => {
    dragOffset = null;
  });
}

module.exports = { registerWindowEvents };

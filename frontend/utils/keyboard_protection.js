function protectWindowShortcuts(win, { allowDevTools = false } = {}) {
  win.webContents.on('before-input-event', (event, input) => {
    // F12
    if (input.type === 'keyDown' && input.key === 'F12') {
      if (allowDevTools) {
        win.webContents.toggleDevTools();
        const show = !win.isMenuBarVisible();
        win.setMenuBarVisibility(show);
        win.autoHideMenuBar = !show;
      }
      event.preventDefault();
      return;
    }

    // F11 (полный экран)
    if (input.type === 'keyDown' && input.key === 'F11') {
      event.preventDefault();
      return;
    }

    // Ctrl+Shift+I
    if (input.control && input.shift && input.key.toUpperCase() === 'I') {
      event.preventDefault();
      return;
    }
  });
}

function disableZoomShortcuts(win) {
  win.webContents.on('before-input-event', (event, input) => {
    // Блокируем Ctrl++ / Ctrl+=, Ctrl+-, Ctrl+0
    if (input.control || input.meta) {
      const blockedKeys = ['+', '=', '-', '0'];
      if (blockedKeys.includes(input.key)) {
        event.preventDefault();
      }
    }
  });
}

function registerOverlayMoveShortcuts(app, overlays) {
  const { globalShortcut } = require('electron');
  let isMovable = false;

  globalShortcut.register('Control+Shift+P', () => {
    isMovable = !isMovable;

    Object.values(overlays).forEach((win) => {
      if (!win.isDestroyed()) {
        // если можно перемещать — клики разрешены
        win.setIgnoreMouseEvents(!isMovable);
        win.setMovable(isMovable);
      }
    });
  });
}

module.exports = {
  protectWindowShortcuts,
  disableZoomShortcuts,
  registerOverlayMoveShortcuts,
};

const TITLE_BAR_ID = 'title-bar';
const MINIMIZE_BUTTON_ID = 'title-bar-minimize';
const CLOSE_BUTTON_ID = 'title-bar-close';

// Single access point for the window-control channels of the preload API.
export function createWindowControls(electronAPI = globalThis.window?.electronAPI) {
  if (!electronAPI) {
    // Page opened outside Electron (or preload failed): the title bar still
    // renders, but the buttons and the drag cannot reach the main process.
    console.warn(
      'window.electronAPI is unavailable; '
      + 'custom title bar window controls will not work',
    );
    electronAPI = {};
  }

  return {
    minimize: () => electronAPI.minimizeWindow?.(),
    close: () => electronAPI.closeWindow?.(),
    startDrag: () => electronAPI.startWindowDrag?.(),
    drag: () => electronAPI.dragWindow?.(),
    endDrag: () => electronAPI.endWindowDrag?.(),
  };
}

// Wires the title bar of the current page; safe to call on pages without one.
export function mountTitleBar({
  document: doc = globalThis.document,
  window: win = globalThis.window,
  electronAPI,
} = {}) {
  const titleBar = doc?.getElementById?.(TITLE_BAR_ID);
  if (!titleBar) return null;

  const controls = createWindowControls(electronAPI);
  let dragging = false;

  function stopDrag() {
    if (!dragging) return;

    dragging = false;
    controls.endDrag();
  }

  doc.getElementById(MINIMIZE_BUTTON_ID)?.addEventListener('click', controls.minimize);
  doc.getElementById(CLOSE_BUTTON_ID)?.addEventListener('click', controls.close);

  return controls;
}

// Mount on the pages that render a title bar. Importing the module elsewhere
// (tests, scripts) leaves the behaviour untouched because there is no bar.
if (globalThis.document?.getElementById?.(TITLE_BAR_ID)) {
  mountTitleBar();
}

// Fake `electron` module, installed for a test file with `useElectronMock()`: `electron.ipcMain`,
// `electron.screen`, `electron.readSettings()` and `createOverlayWindow()` drive the modules under test.

const fs = require('node:fs');
const Module = require('node:module');
const os = require('node:os');
const path = require('node:path');

const { purgeFrontendModules } = require('./modules');

const originalLoad = Module._load;
let currentMock = null;

function createEmitter() {
  const listeners = new Map();

  return {
    listeners,
    on(type, handler) {
      listeners.set(type, [...(listeners.get(type) ?? []), handler]);
    },
    emit(type, ...args) {
      (listeners.get(type) ?? []).forEach((handler) => handler(...args));
    },
  };
}

// Stand-in for a BrowserWindow; records everything the utilities do to it.
class FakeOverlayWindow {
  constructor({ destroyed = false, bounds = { x: 0, y: 0, width: 400, height: 300 } } = {}) {
    this.destroyed = destroyed;
    this.bounds = { ...bounds };
    this.zoomFactor = 1;
    this.ignoreMouseEvents = null;
    this.movable = null;
    this.animate = null;
    this.menuBarVisible = false;
    this.autoHideMenuBar = true;
    this.minimized = false;
    this.closed = false;
    this.sent = []; // IPC messages pushed to the renderer

    const windowEvents = createEmitter();
    const webContentsEvents = createEmitter();

    this.on = windowEvents.on;
    this.emit = windowEvents.emit;
    this.webContents = {
      sent: this.sent,
      on: webContentsEvents.on,
      emit: webContentsEvents.emit,
      send: (channel, ...args) => this.sent.push({ channel, args }),
      setZoomFactor: (factor) => { this.zoomFactor = factor; },
      toggleDevTools: () => { this.webContents.devtoolsToggles += 1; },
      devtoolsToggles: 0,
    };
  }

  isDestroyed() { return this.destroyed; }
  destroy() { this.destroyed = true; }

  minimize() { this.minimized = true; }
  close() { this.closed = true; }
  getPosition() { return [this.bounds.x, this.bounds.y]; }
  setPosition(x, y) { this.bounds = { ...this.bounds, x, y }; }

  setIgnoreMouseEvents(value) { this.ignoreMouseEvents = value; }
  setMovable(value) { this.movable = value; }
  getBounds() { return { ...this.bounds }; }
  setBounds(bounds, animate = false) {
    this.bounds = { ...this.bounds, ...bounds };
    this.animate = animate;
  }

  isMenuBarVisible() { return this.menuBarVisible; }
  setMenuBarVisibility(visible) { this.menuBarVisible = visible; }

  // Feed a keyboard event through the renderer, like Electron would, and
  // report whether the handler prevented the default behavior.
  pressKey(input) {
    let prevented = false;
    this.webContents.emit(
      'before-input-event',
      { preventDefault: () => { prevented = true; } },
      input,
    );
    return prevented;
  }
}

// Fake overlay/settings windows; registered with the mock when installed.
function createOverlayWindow(options = {}) {
  const BrowserWindow = currentMock?.BrowserWindow ?? FakeOverlayWindow;
  return new BrowserWindow(options);
}

function installElectronMock() {
  const windows = [];
  const handlers = new Map(); // ipcMain.handle channels
  const listeners = new Map(); // ipcMain.on channels
  const shortcuts = new Map(); // globalShortcut accelerators
  const userDataDir = fs.mkdtempSync(path.join(os.tmpdir(), 'redwave-test-'));
  const settingsFile = path.join(userDataDir, 'overlays_settings.json');

  class FakeBrowserWindow extends FakeOverlayWindow {
    constructor(options = {}) {
      super(options);
      windows.push(this);
    }

    static getAllWindows() { return windows; }
  }

  const mock = {
    windows,
    userDataDir,
    settingsFile,
    BrowserWindow: FakeBrowserWindow,

    ipcMain: {
      handlers,
      listeners,
      handle: (channel, handler) => handlers.set(channel, handler),
      on: (channel, handler) => listeners.set(channel, handler),
      removeHandler: (channel) => handlers.delete(channel),
      // Call a registered handler / listener the way the renderer would.
      invoke: (channel, ...args) => {
        const handler = handlers.get(channel);
        if (!handler) throw new Error(`No ipcMain handler registered for ${channel}`);
        return handler({}, ...args);
      },
      emit: (channel, ...args) => {
        const listener = listeners.get(channel);
        if (!listener) throw new Error(`No ipcMain listener registered for ${channel}`);
        listener({}, ...args);
      },
    },

    // The app object is used by the main process to get the userData path and quit the app.
    app: {
      getPath: (name) => (name === 'userData' ? userDataDir : path.join(userDataDir, name)),
      whenReady: () => Promise.resolve(),
      quit: () => { mock.app.quitCalled = true; },
    },

    // Cursor position, moved by tests that drag a window.
    screen: {
      cursor: { x: 0, y: 0 },
      getCursorScreenPoint() { return { ...this.cursor }; },
    },

    // Renderer side of the preload bridge: `sent` records `send()` calls,
    // and `exposedApi` is what `preload.js` passes to `exposeInMainWorld`.
    ipcRenderer: {
      sent: [],
      send(channel, ...args) { this.sent.push({ channel, args }); },
      invoke: () => Promise.resolve(),
      on: () => {},
    },

    contextBridge: {
      exposedApi: null,
      exposeInMainWorld: (name, api) => { mock.contextBridge.exposedApi = api; },
    },

    globalShortcut: {
      registered: shortcuts,
      register: (accelerator, callback) => shortcuts.set(accelerator, callback),
      trigger: (accelerator) => shortcuts.get(accelerator)?.(),
    },

    // Settings file access, so tests can seed and inspect persisted state.
    readSettings: () => JSON.parse(fs.readFileSync(settingsFile, 'utf-8')),
    writeSettings: (settings) => fs.writeFileSync(settingsFile, JSON.stringify(settings)),

    // Drop everything a single test registered.
    reset() {
      handlers.clear();
      listeners.clear();
      shortcuts.clear();
      windows.length = 0;
      mock.app.quitCalled = false;
      mock.screen.cursor = { x: 0, y: 0 };
      mock.ipcRenderer.sent.length = 0;
      mock.contextBridge.exposedApi = null;
      fs.rmSync(settingsFile, { force: true });
    },
  };

  Module._load = function loadWithElectronMock(request, parent, isMain) {
    if (request === 'electron') return mock;
    return originalLoad.call(this, request, parent, isMain);
  };

  currentMock = mock;
  return mock;
}

function uninstallElectronMock(mock) {
  Module._load = originalLoad;
  currentMock = null;
  if (mock?.userDataDir) fs.rmSync(mock.userDataDir, { recursive: true, force: true });
}

// Installs the mock for the whole test file and gives every test a clean
// slate: fresh ipc registrations, no windows, no settings file, no module
// state left over from the previous test.
function useElectronMock() {
  const { before, beforeEach, after } = require('node:test');
  const mock = installElectronMock();

  before(() => purgeFrontendModules());
  beforeEach(() => {
    mock.reset();
    purgeFrontendModules();
  });
  after(() => uninstallElectronMock(mock));

  return mock;
}

module.exports = { createOverlayWindow, useElectronMock };

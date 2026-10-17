const test = require('node:test');
const assert = require('node:assert/strict');
const Module = require('node:module');

const { loadFrontendModule, purgeFrontendModules } = require('../helpers/modules');

const UPDATER = 'utils/app_updater/updater';
const { version: currentVersion } = require('../../../package.json');

// The update service pulls in `electron-updater` and `builder-util-runtime`
// when it is created, so both are swapped for fakes before every test.
const originalLoad = Module._load;
const realFetch = globalThis.fetch;
let fakes;

function installUpdaterFakes() {
  const listeners = new Map();
  const quitAndInstallCalls = [];
  const downloadTokens = [];

  class FakeCancellationToken {
    constructor() { this.cancelled = false; }
    cancel() { this.cancelled = true; }
  }

  class FakeCancellationError extends Error {
    constructor(message = 'The operation was canceled') {
      super(message);
      this.name = 'CancellationError';
    }
  }

  const autoUpdater = {
    // The real updater ships with both flags on; the service must turn them
    // off so nothing downloads or installs without the user asking.
    autoDownload: true,
    autoInstallOnAppQuit: true,
    on(event, handler) {
      listeners.set(event, [...(listeners.get(event) ?? []), handler]);
    },
    emit(event, ...args) {
      (listeners.get(event) ?? []).forEach((handler) => handler(...args));
    },
    // The manifest lookup the download flow runs after the user opts in.
    checkForUpdates: async () => ({ updateInfo: { version: '9999.0.0' } }),
    downloadUpdate: async (token) => { downloadTokens.push(token); },
    quitAndInstall: (...args) => { quitAndInstallCalls.push(args); },
  };

  Module._load = function loadWithUpdaterFakes(request, parent, isMain) {
    if (request === 'electron-updater') return { autoUpdater };
    if (request === 'builder-util-runtime') {
      return {
        CancellationError: FakeCancellationError,
        CancellationToken: FakeCancellationToken,
      };
    }
    return originalLoad.call(this, request, parent, isMain);
  };

  return { autoUpdater, quitAndInstallCalls, downloadTokens };
}

function createService({ isPackaged = true } = {}) {
  return loadFrontendModule(UPDATER).createUpdateService({ isPackaged });
}

const RELEASE_URL = 'https://github.com/onesch/redwave-overlays/releases/tag/v9999.0.0';

// Stands in for the fetch the update check makes to the GitHub Releases API.
function stubFetch(responder) {
  const calls = [];
  globalThis.fetch = async (url, options = {}) => {
    calls.push({ url, options });
    return responder();
  };
  return calls;
}

function stubReleaseApi(tagName, { ok = true, status = 200, htmlUrl = RELEASE_URL } = {}) {
  return stubFetch(async () => ({
    ok,
    status,
    json: async () => ({ tag_name: tagName, html_url: htmlUrl }),
  }));
}

function silenceConsoleError(t) {
  const logged = [];
  const original = console.error;
  console.error = (...args) => logged.push(args);
  t.after(() => { console.error = original; });
  return logged;
}

test.beforeEach(() => {
  purgeFrontendModules();
  fakes = installUpdaterFakes();
});

test.afterEach(() => {
  Module._load = originalLoad;
  globalThis.fetch = realFetch;
});

test('isNewerVersion treats only strictly newer release tags as an update', () => {
  const { isNewerVersion } = loadFrontendModule(UPDATER);

  assert.equal(isNewerVersion('3.5.0', '3.4.1'), true);
  assert.equal(isNewerVersion('3.4.1', '3.4.1'), false);
  assert.equal(isNewerVersion('3.4.0', '3.4.1'), false);

  // Release tags may carry a `v`, and segments compare as numbers, not text.
  assert.equal(isNewerVersion('v3.5.0', '3.4.1'), true);
  assert.equal(isNewerVersion('10.0.0', '9.9.9'), true);

  // Missing segments count as zero, suffixes are dropped before comparing.
  assert.equal(isNewerVersion('3.5', '3.4.1'), true);
  assert.equal(isNewerVersion('3.4.1-beta.2', '3.4.1'), false);
  assert.equal(isNewerVersion('3.4.2+build.7', '3.4.1'), true);

  // Tags that are not plain versions never count as an update.
  assert.equal(isNewerVersion('latest', '3.4.1'), false);
  assert.equal(isNewerVersion('3.5.0', 'not-a-version'), false);
  assert.equal(isNewerVersion(undefined, '3.4.1'), false);
});

test('A new update service is idle and keeps downloads user-driven', () => {
  const service = createService();

  assert.deepEqual(service.getStatus(), {
    state: 'idle',
    currentVersion,
    latestVersion: null,
    releaseUrl: null,
    progress: 0,
    message: null,
    canDownload: false,
  });
  assert.equal(fakes.autoUpdater.autoDownload, false);
  assert.equal(fakes.autoUpdater.autoInstallOnAppQuit, false);
});

test('checkForUpdates reports no update when the installed version is the latest release', async () => {
  const { RELEASES_API_URL } = loadFrontendModule(UPDATER);
  const service = createService();
  const calls = stubReleaseApi(`v${currentVersion}`);

  await service.checkForUpdates();

  assert.equal(calls.length, 1);
  assert.equal(calls[0].url, RELEASES_API_URL);
  assert.equal(calls[0].options.headers.Accept, 'application/vnd.github+json');
  assert.deepEqual(service.getStatus(), {
    state: 'not-available',
    currentVersion,
    latestVersion: `v${currentVersion}`,
    releaseUrl: RELEASE_URL,
    progress: 0,
    message: null,
    canDownload: false,
  });
});

test('checkForUpdates offers a newer release and allows downloading in a packaged app', async () => {
  const service = createService({ isPackaged: true });
  stubReleaseApi('v9999.0.0');

  const seen = [];
  service.onStatusChange((status) => seen.push(status.state));

  await service.checkForUpdates();

  assert.equal(service.getStatus().state, 'available');
  assert.equal(service.getStatus().latestVersion, 'v9999.0.0');
  assert.equal(service.getStatus().releaseUrl, RELEASE_URL);
  assert.equal(service.getStatus().canDownload, true);
  // Listeners see every transition so the Settings page can follow along.
  assert.deepEqual(seen, ['checking', 'available']);
});

test('downloadUpdate refuses to start without a downloadable update', async () => {
  const service = createService({ isPackaged: false });

  assert.deepEqual(await service.downloadUpdate(), {
    ok: false,
    message: 'No downloadable update is available.',
  });

  stubReleaseApi('v9999.0.0');
  await service.checkForUpdates();
  // An update exists, but a development build cannot run the installer.
  assert.equal(service.getStatus().canDownload, false);
  assert.deepEqual(await service.downloadUpdate(), {
    ok: false,
    message: 'No downloadable update is available.',
  });
  assert.equal(fakes.downloadTokens.length, 0);
});

test('checkForUpdates reports an error state when GitHub returns no usable release', async (t) => {
  silenceConsoleError(t);
  const service = createService();

  stubReleaseApi('v9999.0.0', { ok: false, status: 503 });
  await service.checkForUpdates();
  assert.equal(service.getStatus().state, 'error');
  assert.equal(
    service.getStatus().message,
    'Unable to check for updates. Please try again later.',
  );

  // A release without a plain version tag is just as unusable.
  stubReleaseApi('latest');
  await service.checkForUpdates();
  assert.equal(service.getStatus().state, 'error');
});

test('Concurrent checkForUpdates calls share a single request', async () => {
  const service = createService();
  const calls = stubReleaseApi(`v${currentVersion}`);

  const first = service.checkForUpdates();
  const second = service.checkForUpdates();

  const [fromFirst, fromSecond] = await Promise.all([first, second]);
  // Both callers are answered by the same lookup and the same result.
  assert.equal(calls.length, 1);
  assert.equal(fromFirst, fromSecond);
  assert.equal(service.getStatus().state, 'not-available');
});

test('downloadUpdate reports progress and installs the update when it finishes', async () => {
  const service = createService({ isPackaged: true });
  stubReleaseApi('v9999.0.0');
  await service.checkForUpdates();

  fakes.autoUpdater.downloadUpdate = async () => {
    // electron-updater reports progress, then that the installer is on disk.
    fakes.autoUpdater.emit('download-progress', { percent: 42.6 });
    fakes.autoUpdater.emit('update-downloaded', { version: '9999.0.0' });
  };

  const seen = [];
  service.onStatusChange((status) => seen.push({ state: status.state, progress: status.progress }));

  assert.deepEqual(await service.downloadUpdate(), { ok: true });

  assert.deepEqual(seen, [
    { state: 'downloading', progress: 0 },
    { state: 'downloading', progress: 43 },
    { state: 'downloaded', progress: 100 },
  ]);
  const status = service.getStatus();
  assert.equal(status.state, 'downloaded');
  assert.equal(status.latestVersion, '9999.0.0');
  assert.equal(status.message, 'Update downloaded. Restarting to install it…');
  assert.equal(status.canDownload, false);
  // The user already chose Download, so the update is installed right away.
  assert.deepEqual(fakes.quitAndInstallCalls, [[false, true]]);
});

test('cancelDownload stops the transfer and restores the available state', async () => {
  const service = createService({ isPackaged: true });
  stubReleaseApi('v9999.0.0');
  await service.checkForUpdates();

  let finishDownload;
  let downloadToken;
  fakes.autoUpdater.downloadUpdate = (token) => {
    downloadToken = token;
    return new Promise((resolve) => { finishDownload = resolve; });
  };

  const pending = service.downloadUpdate();
  assert.equal(service.getStatus().state, 'downloading');
  // Let the manifest lookup finish so the transfer is actually in flight.
  await new Promise((resolve) => setImmediate(resolve));
  assert.ok(downloadToken, 'the transfer never started');

  assert.deepEqual(service.cancelDownload(), { ok: true });
  assert.equal(downloadToken.cancelled, true);
  assert.deepEqual(service.getStatus(), {
    state: 'available',
    currentVersion,
    latestVersion: 'v9999.0.0',
    releaseUrl: RELEASE_URL,
    progress: 0,
    message: null,
    canDownload: true,
  });

  // The unwinding transfer resolves as cancelled and nothing is installed.
  finishDownload();
  assert.deepEqual(await pending, { ok: false, cancelled: true });
  assert.deepEqual(fakes.quitAndInstallCalls, []);
  assert.deepEqual(service.cancelDownload(), {
    ok: false,
    message: 'No update download is in progress.',
  });
});

test('downloadUpdate refuses a manifest that does not contain a newer version', async (t) => {
  silenceConsoleError(t);
  const service = createService({ isPackaged: true });
  stubReleaseApi('v9999.0.0');
  await service.checkForUpdates();

  // The manifest published with the release disagrees with the release tag.
  fakes.autoUpdater.checkForUpdates = async () => ({ updateInfo: { version: currentVersion } });

  assert.deepEqual(await service.downloadUpdate(), {
    ok: false,
    message: 'The update could not be downloaded. Please try again.',
  });
  assert.equal(service.getStatus().state, 'available');
  assert.deepEqual(fakes.quitAndInstallCalls, []);
});

test('A failed download restores the available state with a retry message', async (t) => {
  silenceConsoleError(t);
  const service = createService({ isPackaged: true });
  stubReleaseApi('v9999.0.0');
  await service.checkForUpdates();

  fakes.autoUpdater.downloadUpdate = async () => { throw new Error('disk full'); };

  assert.deepEqual(await service.downloadUpdate(), {
    ok: false,
    message: 'The update could not be downloaded. Please try again.',
  });
  const status = service.getStatus();
  assert.equal(status.state, 'available');
  assert.equal(status.message, 'The update could not be downloaded. Please try again.');
  assert.equal(status.progress, 0);
  assert.equal(status.canDownload, true);
  assert.deepEqual(fakes.quitAndInstallCalls, []);
});

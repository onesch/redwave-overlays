const test = require('node:test');
const assert = require('node:assert/strict');
const path = require('node:path');
const { pathToFileURL } = require('node:url');

const { FakeDocument, FakeWindow } = require('../helpers/dom');
const { FRONTEND_DIR } = require('../helpers/modules');

const SETTINGS_PAGE = 'static/js/setting_page/index.js';
const UPDATE_STATES = ['checking', 'available', 'downloading', 'downloaded', 'not-available', 'error'];

// Let the handlers and the initial status load finish their promises.
const settle = () => new Promise((resolve) => setImmediate(resolve));

// Markup of the settings page (frontend/templates/pages/settings.html).
function createSettingsDocument() {
  return new FakeDocument({
    'update-status': 'setting-desc',
    'download-update': 'button primary-btn',
    'cancel-update': 'button primary-btn',
    'open-update-release': 'button primary-btn',
    'reset-overlay-settings': 'button primary-btn',
    'open-install-dir': 'button primary-btn',
    'uninstall-app': 'button primary-btn',
  });
}

// Counter for the cache-busting query in `loadSettingsPage`.
let loadCount = 0;

// The page wires itself up while it loads, so every test loads it against a
// fresh document and a recording stub of the preload api. `pushStatus` is a
// status update from the main process; `downloadResult` / `cancelResult` are
// the replies the Download and Cancel buttons get.
async function loadSettingsPage({ status = { state: 'idle' } } = {}) {
  const document = createSettingsDocument();
  const api = {
    status,
    statusListeners: [],
    downloadResult: { ok: true },
    cancelResult: { ok: true },
    getUpdateStatus: async () => api.status,
    downloadUpdate: async () => api.downloadResult,
    cancelUpdateDownload: async () => api.cancelResult,
    onUpdateStatus: (listener) => api.statusListeners.push(listener),
  };

  const window = new FakeWindow();
  window.electronAPI = api;
  global.document = document;
  global.window = window;

  // The page is an ES module with load-time side effects, and modules are
  // cached by URL: the query gives every test its own evaluation of it.
  loadCount += 1;
  const pageUrl = pathToFileURL(path.join(FRONTEND_DIR, SETTINGS_PAGE));
  await import(`${pageUrl}?load=${loadCount}`);
  await settle(); // the page renders the status it loads at startup

  return {
    document,
    api,
    pushStatus: (next) => api.statusListeners.forEach((listener) => listener(next)),
  };
}

function silenceConsoleError(t) {
  const logged = [];
  const original = console.error;
  console.error = (...args) => logged.push(args);
  t.after(() => { console.error = original; });
  return logged;
}

test('Update status shows Cancel only while the update is downloading', async () => {
  const { document, pushStatus } = await loadSettingsPage();
  const cancel = document.getElementById('cancel-update');

  for (const state of UPDATE_STATES) {
    pushStatus({ state, latestVersion: 'v9.9.9', canDownload: true, progress: 42 });
    assert.equal(cancel.style.display, state === 'downloading' ? 'flex' : 'none', state);
  }

  // A status that replaces the download also re-arms the Cancel button.
  pushStatus({ state: 'downloading', progress: 10 });
  cancel.disabled = true;
  pushStatus({ state: 'available', latestVersion: 'v9.9.9', canDownload: true });

  assert.equal(cancel.disabled, false);
  assert.equal(cancel.style.display, 'none');
});

test('Update status offers Download only for an update that can be downloaded', async () => {
  const { document, pushStatus } = await loadSettingsPage({
    status: { state: 'available', latestVersion: 'v9.9.9', canDownload: true },
  });
  const status = document.getElementById('update-status');
  const download = document.getElementById('download-update');

  // The status loaded at startup is rendered right away.
  assert.equal(download.style.display, 'flex');
  assert.match(status.innerHTML, /update-info available/);
  assert.match(status.innerHTML, /Version v9\.9\.9 is available\./);

  // A development build reports the update but cannot run the installer.
  pushStatus({ state: 'available', latestVersion: 'v9.9.9', canDownload: false });
  assert.equal(download.style.display, 'none');

  // A failed download stays available with the failure message.
  pushStatus({
    state: 'available',
    canDownload: true,
    message: 'The update could not be downloaded. Please try again.',
  });
  assert.equal(download.style.display, 'flex');
  assert.match(status.innerHTML, /could not be downloaded/);

  pushStatus({ state: 'not-available', latestVersion: 'v3.4.1' });
  assert.equal(download.style.display, 'none');
  assert.match(status.innerHTML, /update-info success/);
  assert.match(status.innerHTML, /You’re all up to date!/);
});

test('Update status describes the remaining update states', async () => {
  const { document, pushStatus } = await loadSettingsPage();
  const status = document.getElementById('update-status');

  pushStatus({ state: 'checking' });
  assert.equal(status.textContent, 'Checking for updates…');

  pushStatus({ state: 'downloading', latestVersion: 'v9.9.9', progress: 42 });
  assert.match(status.innerHTML, /update-info downloading/);
  assert.match(status.innerHTML, /Downloading update v9\.9\.9… 42%/);

  pushStatus({ state: 'downloaded', latestVersion: '9.9.9' });
  assert.match(status.innerHTML, /update-info success/);
  assert.match(status.innerHTML, /Version 9\.9\.9 is restarting to install the update…/);

  pushStatus({ state: 'error', message: 'Unable to check for updates. Please try again later.' });
  assert.match(status.innerHTML, /update-info error/);
  assert.match(status.innerHTML, /Unable to check for updates\./);

  // A state the page does not know yet falls back to the default message.
  pushStatus({ state: 'idle' });
  assert.equal(status.textContent, 'Updates are checked automatically at startup.');
});

test('Download button reports a failed download and ignores a cancelled one', async () => {
  const { document, api } = await loadSettingsPage({
    status: { state: 'available', latestVersion: 'v9.9.9', canDownload: true },
  });
  const status = document.getElementById('update-status');
  const download = document.getElementById('download-update');

  // A download that starts is left to the updater to report on.
  status.textContent = '';
  download.click();
  await settle();
  assert.equal(status.textContent, '');

  api.downloadResult = { ok: false, message: 'The update could not be downloaded. Please try again.' };
  download.click();
  await settle();
  assert.equal(status.textContent, 'The update could not be downloaded. Please try again.');

  status.textContent = '';
  api.downloadResult = { ok: false, cancelled: true };
  download.click();
  await settle();
  assert.equal(status.textContent, '');
});

test('Cancel button reports a failure and is usable again afterwards', async (t) => {
  const logged = silenceConsoleError(t);
  const { document, api, pushStatus } = await loadSettingsPage();
  const status = document.getElementById('update-status');
  const cancel = document.getElementById('cancel-update');

  pushStatus({ state: 'downloading', latestVersion: 'v9.9.9', progress: 42 });
  assert.equal(cancel.style.display, 'flex');

  // A successful cancellation is reported by the updater itself.
  status.textContent = '';
  cancel.click();
  await settle();
  assert.equal(status.textContent, '');
  assert.equal(cancel.disabled, false);

  api.cancelResult = { ok: false, message: 'No update download is in progress.' };
  cancel.click();
  await settle();
  assert.equal(status.textContent, 'No update download is in progress.');
  assert.equal(cancel.disabled, false);

  api.cancelUpdateDownload = async () => { throw new Error('ipc failed'); };
  cancel.click();
  await settle();
  assert.equal(status.textContent, 'Failed to cancel the update download.');
  assert.equal(cancel.disabled, false);
  assert.equal(logged.length, 1);
  assert.equal(logged[0][0], 'Failed to cancel update download:');
  assert.equal(logged[0][1].message, 'ipc failed');
});

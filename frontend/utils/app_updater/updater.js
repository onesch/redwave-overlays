const { version: currentVersion } = require('../../../package.json');

const RELEASES_API_URL =
  'https://api.github.com/repos/onesch/redwave-overlays/releases/latest';
const RELEASES_PAGE_URL =
  'https://github.com/onesch/redwave-overlays/releases/latest';

function versionParts(version) {
  const normalized = String(version ?? '')
    .trim()
    .replace(/^v/i, '')
    .split(/[+-]/, 1)[0];

  if (!/^\d+(\.\d+)*$/.test(normalized)) return null;
  return normalized.split('.').map(Number);
}

function isNewerVersion(candidate, installed) {
  const candidateParts = versionParts(candidate);
  const installedParts = versionParts(installed);

  if (!candidateParts || !installedParts) return false;

  const length = Math.max(candidateParts.length, installedParts.length);
  for (let index = 0; index < length; index += 1) {
    const difference = (candidateParts[index] ?? 0) - (installedParts[index] ?? 0);
    if (difference !== 0) return difference > 0;
  }

  return false;
}

function createUpdateService(app) {
  const { autoUpdater } = require('electron-updater');
  const {
    CancellationError, CancellationToken,
  } = require('builder-util-runtime');

  let status = {
    state: 'idle',
    currentVersion,
    latestVersion: null,
    releaseUrl: null,
    progress: 0,
    message: null,
    canDownload: false,
  };
  let checkPromise = null;
  let activeDownload = null;
  const listeners = new Set();

  // The `publish` function updates the current status and notifies all registered listeners of the change. It merges the new status with the existing one and returns the updated status.
  const publish = (nextStatus) => {
    status = { ...status, ...nextStatus };
    for (const listener of listeners) listener(status);
    return status;
  };

  const updateUnavailable = (message) => {
    publish({
      state: 'available',
      progress: 0,
      message,
      canDownload: app.isPackaged,
    });
  };

  const isCancelled = (download) =>
    Boolean(download?.cancelled || download?.token?.cancelled);

  const isCancellationError = (error) =>
    error instanceof CancellationError || error?.name === 'CancellationError';

  // Downloads are always initiated from the Settings page, never silently.
  autoUpdater.autoDownload = false;
  autoUpdater.autoInstallOnAppQuit = false;

  autoUpdater.on('download-progress', (progress) => {
    // A cancelled download can still emit progress while it unwinds.
    if (!activeDownload || isCancelled(activeDownload)) return;

    publish({
      state: 'downloading',
      progress: Math.round(progress.percent ?? 0),
      message: null,
      canDownload: false,
    });
  });

  autoUpdater.on('update-downloaded', (info) => {
    // The user cancelled after the file was already written; keep the update
    // available for a later attempt instead of restarting the application.
    if (!activeDownload || isCancelled(activeDownload)) return;

    publish({
      state: 'downloaded',
      latestVersion: info.version ?? status.latestVersion,
      progress: 100,
      message: 'Update downloaded. Restarting to install it…',
      canDownload: false,
    });

    // The user already chose Download, so finish the update immediately.
    autoUpdater.quitAndInstall(false, true);
  });

  autoUpdater.on('error', (error) => {
    console.error('Updater error:', error);
    if (isCancelled(activeDownload) || isCancellationError(error)) return;
    if (status.state === 'downloading') {
      updateUnavailable('The update could not be downloaded. Please try again.');
    }
  });

  async function checkForUpdates() {
    if (checkPromise) return checkPromise;

    checkPromise = (async () => {
      publish({
        state: 'checking',
        progress: 0,
        message: null,
        canDownload: false,
      });

      try {
        const response = await fetch(RELEASES_API_URL, {
          headers: { Accept: 'application/vnd.github+json' },
        });

        if (!response.ok) {
          throw new Error(`GitHub Releases API returned ${response.status}`);
        }

        const release = await response.json();
        const latestVersion = release?.tag_name;
        if (!versionParts(latestVersion)) {
          throw new Error('GitHub Releases API did not return a valid release tag');
        }

        if (!isNewerVersion(latestVersion, currentVersion)) {
          return publish({
            state: 'not-available',
            latestVersion,
            releaseUrl: release.html_url ?? RELEASES_PAGE_URL,
            progress: 0,
            message: null,
            canDownload: false,
          });
        }

        return publish({
          state: 'available',
          latestVersion,
          releaseUrl: release.html_url ?? RELEASES_PAGE_URL,
          progress: 0,
          message: null,
          canDownload: app.isPackaged,
        });
      } catch (error) {
        console.error('Unable to check for updates:', error);
        return publish({
          state: 'error',
          progress: 0,
          message: 'Unable to check for updates. Please try again later.',
          canDownload: false,
        });
      } finally {
        checkPromise = null;
      }
    })();

    return checkPromise;
  }

  async function downloadUpdate() {
    if (status.state !== 'available' || !status.canDownload) {
      return { ok: false, message: 'No downloadable update is available.' };
    }

    // Let a previously cancelled download finish unwinding first:
    // electron-updater keeps its own download promise until then and would
    // hand that stale promise to the next attempt.
    if (activeDownload?.settled) {
      await activeDownload.settled.catch(() => {});
    }

    // Another download may have started while this one was waiting.
    if (status.state !== 'available' || !status.canDownload) {
      return { ok: false, message: 'A download is already in progress.' };
    }

    const download = {
      token: new CancellationToken(),
      cancelled: false,
      settled: null,
    };
    activeDownload = download;

    publish({
      state: 'downloading',
      progress: 0,
      message: null,
      canDownload: false,
    });

    download.settled = (async () => {
      try {
        // The API check above prompts the user. electron-updater then uses the
        // latest.yml uploaded with the release to download the installer.
        const result = await autoUpdater.checkForUpdates();
        if (isCancelled(download)) return { ok: false, cancelled: true };

        if (!isNewerVersion(result?.updateInfo?.version, currentVersion)) {
          throw new Error('The published update manifest does not contain a newer version');
        }

        await autoUpdater.downloadUpdate(download.token);
        if (isCancelled(download)) return { ok: false, cancelled: true };

        if (status.state !== 'downloaded') {
          publish({
            state: 'downloaded',
            progress: 100,
            message: 'Update downloaded. Restarting to install it…',
          });
          autoUpdater.quitAndInstall(false, true);
        }

        return { ok: true };
      } catch (error) {
        // Cancellation is a user action, not a failure: the status was already
        // reset to `available` by `cancelDownload`.
        if (isCancelled(download)) return { ok: false, cancelled: true };

        // Defensive: never leave the UI stuck in `downloading` if the updater
        // cancels the transfer on its own.
        if (isCancellationError(error)) {
          publish({
            state: 'available',
            progress: 0,
            message: null,
            canDownload: app.isPackaged,
          });
          return { ok: false, cancelled: true };
        }

        console.error('Unable to download update:', error);
        updateUnavailable('The update could not be downloaded. Please try again.');
        return { ok: false, message: 'The update could not be downloaded. Please try again.' };
      } finally {
        if (activeDownload === download) activeDownload = null;
      }
    })();

    return download.settled;
  }

  function cancelDownload() {
    if (status.state !== 'downloading' || !activeDownload || isCancelled(activeDownload)) {
      return { ok: false, message: 'No update download is in progress.' };
    }

    // Stop the in-flight download and restore the pre-download UI: the update
    // is available again, with no progress or error message.
    activeDownload.cancelled = true;
    activeDownload.token.cancel();

    publish({
      state: 'available',
      progress: 0,
      message: null,
      canDownload: app.isPackaged,
    });

    return { ok: true };
  }

  return {
    checkForUpdates,
    downloadUpdate,
    cancelDownload,
    getStatus: () => ({ ...status }),
    onStatusChange: (listener) => listeners.add(listener),
  };
}

module.exports = {
  createUpdateService,
  isNewerVersion,
  RELEASES_API_URL,
};

const path = require('node:path');
const { version: currentVersion } = require(path.resolve(__dirname, '../../../package.json'));

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
  const listeners = new Set();

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

  // Downloads are always initiated from the Settings page, never silently.
  autoUpdater.autoDownload = false;
  autoUpdater.autoInstallOnAppQuit = false;

  autoUpdater.on('download-progress', (progress) => {
    publish({
      state: 'downloading',
      progress: Math.round(progress.percent ?? 0),
      message: null,
      canDownload: false,
    });
  });

  autoUpdater.on('update-downloaded', (info) => {
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

    publish({
      state: 'downloading',
      progress: 0,
      message: null,
      canDownload: false,
    });

    try {
      // The API check above prompts the user. electron-updater then uses the
      // latest.yml uploaded with the release to download the installer.
      const result = await autoUpdater.checkForUpdates();
      if (!isNewerVersion(result?.updateInfo?.version, currentVersion)) {
        throw new Error('The published update manifest does not contain a newer version');
      }

      await autoUpdater.downloadUpdate();

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
      console.error('Unable to download update:', error);
      updateUnavailable('The update could not be downloaded. Please try again.');
      return { ok: false, message: 'The update could not be downloaded. Please try again.' };
    }
  }

  return {
    checkForUpdates,
    downloadUpdate,
    getStatus: () => ({ ...status }),
    onStatusChange: (listener) => listeners.add(listener),
  };
}

module.exports = {
  createUpdateService,
  isNewerVersion,
  RELEASES_API_URL,
};

const updateStatus = document.getElementById('update-status');
const downloadUpdate = document.getElementById('download-update');
const cancelUpdate = document.getElementById('cancel-update');
const openUpdateRelease = document.getElementById('open-update-release');

function renderUpdateStatus(status) {
  const latest = status.latestVersion ? ` ${status.latestVersion}` : '';

  // Hide Cancel by default; show it only while downloading.
  cancelUpdate.style.display = 'none';
  cancelUpdate.disabled = false;

  // Update the UI based on the current update status.
  switch (status.state) {
    case 'checking':
      updateStatus.textContent = 'Checking for updates…';
      break;

    case 'available':
      updateStatus.innerHTML = `
        <span class="update-info available">
          ${status.message || `Version${latest} is available.`}
          <span class="material-symbols-outlined">cached</span>
        </span>
      `;
      downloadUpdate.style.display = status.canDownload ? 'flex' : 'none';
      break;

    case 'downloading':
      updateStatus.innerHTML = `
        <span class="update-info downloading">
          Downloading update${latest}… ${status.progress}%
          <span class="material-symbols-outlined">cached</span>
        </span>
      `;
      downloadUpdate.style.display = 'none';
      cancelUpdate.style.display = 'flex';
      break;

    case 'downloaded':
      updateStatus.innerHTML = `
        <span class="update-info success">
          ${status.message || `Version${latest} is restarting to install the update…`}
          <span class="material-symbols-outlined">arrow_downward</span>
        </span>
      `;
      downloadUpdate.style.display = 'none';
      break;

    case 'not-available':
      updateStatus.innerHTML = `
        <span class="update-info success">
          You’re all up to date!
          <span class="material-symbols-outlined">check</span>
        </span>
      `;
      downloadUpdate.style.display = 'none';
      break;

    case 'error':
      updateStatus.innerHTML = `
        <span class="update-info error">
          ${status.message}
          <span class="material-symbols-outlined">close</span>
        </span>
      `;
      downloadUpdate.style.display = 'none';
      break;

    default:
      updateStatus.textContent = 'Updates are checked automatically at startup.';
      downloadUpdate.style.display = 'none';
  }
}

// Handle the download update button click event.
downloadUpdate.addEventListener('click', async () => {
  const result = await window.electronAPI.downloadUpdate();

  if (!result.ok && !result.cancelled) {
    updateStatus.textContent = result.message;
  }
});

// Handle cancellation of the update download.
cancelUpdate.addEventListener('click', async () => {
  // Prevent repeated cancellation requests while waiting for confirmation.
  cancelUpdate.disabled = true;

  try {
    const result = await window.electronAPI.cancelUpdateDownload();

    if (!result.ok && !result.cancelled) {
      updateStatus.textContent = result.message;
    }
  } catch (error) {
    updateStatus.textContent = 'Failed to cancel the update download.';
    console.error('Failed to cancel update download:', error);
  } finally {
    cancelUpdate.disabled = false;
  }
});

// Keep View release available at all times.
openUpdateRelease.addEventListener('click', () => {
  window.electronAPI.openUpdateRelease();
});

// Listen for update status changes and render the initial status.
window.electronAPI.onUpdateStatus(renderUpdateStatus);
window.electronAPI.getUpdateStatus().then(renderUpdateStatus);

// Handle resetting overlay settings.
document
  .getElementById('reset-overlay-settings')
  .addEventListener('click', () => {
    if (!confirm('Reset all overlay settings?')) {
      return;
    }

    window.electronAPI.resetOverlaySettings();
    alert('Overlay settings have been reset');
  });

// Handle opening the installation directory.
document
  .getElementById('open-install-dir')
  .addEventListener('click', () => {
    window.electronAPI.openInstallDir();
  });

// Handle uninstalling the application.
document
  .getElementById('uninstall-app')
  .addEventListener('click', () => {
    if (!confirm('Run uninstaller and close RedWave overlays?')) {
      return;
    }

    window.electronAPI.uninstallApp();
  });

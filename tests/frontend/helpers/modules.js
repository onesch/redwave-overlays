// Shared helpers for loading frontend modules and clearing their require cache
// to isolate tests from previously loaded modules.

const path = require('node:path');

const FRONTEND_DIR = path.join(__dirname, '..', '..', '..', 'frontend');
const BASE_UPDATER = '../../../frontend/overlays/shared/baseUpdater.js';

function purgeFrontendModules() {
  const prefix = `${FRONTEND_DIR}${path.sep}`;
  Object.keys(require.cache)
    .filter((file) => file.startsWith(prefix))
    .forEach((file) => { delete require.cache[file]; });
}

// Paths are relative to `frontend/`, e.g. 'utils/overlays/overlay_size'.
function loadFrontendModule(relativePath) {
  return require(path.join(FRONTEND_DIR, relativePath));
}

module.exports = { FRONTEND_DIR, loadFrontendModule, purgeFrontendModules, BASE_UPDATER };

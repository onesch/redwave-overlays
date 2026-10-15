const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');

const { FRONTEND_DIR, loadFrontendModule } = require('../helpers/modules');
const { useElectronMock } = require('../helpers/electron');

useElectronMock();

// The utilities are only exercised inside Electron, so a module that moves or
// loses one of its dependencies would otherwise break at runtime unnoticed.
test('every frontend utility module loads', () => {
  const files = fs
    .readdirSync(path.join(FRONTEND_DIR, 'utils'), { recursive: true })
    .filter((file) => file.endsWith('.js'));

  assert.ok(files.length > 0, 'no utility modules found');

  for (const file of files) {
    assert.doesNotThrow(() => loadFrontendModule(path.join('utils', file)), file);
  }
});

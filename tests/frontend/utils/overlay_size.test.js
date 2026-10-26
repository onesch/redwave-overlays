const test = require('node:test');
const assert = require('node:assert/strict');

const { loadFrontendModule } = require('../helpers/modules');
const { createOverlayWindow } = require('../helpers/electron');

test('Overlay size resolves base sizes for direct and variant-based overlays', () => {
  const { resolveBaseSize } = loadFrontendModule('utils/overlays/overlay_size');

  assert.deepEqual(resolveBaseSize('radar'), { width: 180, height: 180 });
  assert.deepEqual(resolveBaseSize('track-map', 'circle'), { width: 240, height: 240 });
  // Unknown track types fall back to the linear layout.
  assert.deepEqual(resolveBaseSize('track-map', 'unknown'), { width: 350, height: 100 });
  assert.equal(resolveBaseSize('unknown-overlay'), null);
});

test('Overlay size resizes the overlay window for the zoom factor and keeps its position', () => {
  const { applyOverlaySize } = loadFrontendModule('utils/overlays/overlay_size');
  const overlay = createOverlayWindow({ bounds: { x: 30, y: 40, width: 450, height: 300 } });

  applyOverlaySize(overlay, 'leaderboard', 0.5, undefined, true);

  assert.equal(overlay.zoomFactor, 0.5);
  assert.deepEqual(overlay.bounds, { x: 30, y: 40, width: 225, height: 150 });
  assert.equal(overlay.animate, true);
});

test('Overlay size ignores windows that are gone and overlays without a configured size', () => {
  const { applyOverlaySize } = loadFrontendModule('utils/overlays/overlay_size');

  applyOverlaySize(null, 'radar', 2);

  const destroyed = createOverlayWindow({ destroyed: true });
  applyOverlaySize(destroyed, 'radar', 2);
  assert.equal(destroyed.zoomFactor, 1);

  const unknownOverlay = createOverlayWindow();
  applyOverlaySize(unknownOverlay, 'unknown-overlay', 2);
  assert.equal(unknownOverlay.zoomFactor, 1);
});

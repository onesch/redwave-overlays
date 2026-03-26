const overlayConfig = require('../../windows/overlays_config');

// Return base values from baseSize
function resolveBaseSize(overlayName, trackType) {
  const baseSize = overlayConfig[overlayName]?.baseSize;
  if (!baseSize) return null;

  // Other overlays (width/height directly)
  if ('width' in baseSize && 'height' in baseSize) {
    return baseSize;
  }

  // Variant-based overlay (track-map)
  return baseSize[trackType] ?? baseSize.linear;
}

// Resize overlay window according to the base size configuration.
function applyOverlaySize(
  win, overlayName, zoomFactor, trackType, animate = false
) {
  // Dont touch the UI if there is no window.
  if (!win || win.isDestroyed()) return;

  const baseSize = resolveBaseSize(overlayName, trackType);
  if (!baseSize) return;

  const newWidth  = Math.round(baseSize.width  * zoomFactor);
  const newHeight = Math.round(baseSize.height * zoomFactor);

  win.webContents.setZoomFactor(zoomFactor);

  // setBounds always flushes the geometry update.
  // Electron can silently ignore setSize when the value
  // matches its internal cache (stale after a
  // previous type switch changed the window dimensions).
  const bounds = win.getBounds();
  win.setBounds(
    { x: bounds.x, y: bounds.y, width: newWidth, height: newHeight },
    animate
  );
}

module.exports = {
  resolveBaseSize,
  applyOverlaySize,
};

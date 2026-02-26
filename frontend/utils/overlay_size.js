const overlayConfig = require('../windows/overlays_config');

// Return base values ​​from baseSize
function resolveBaseSize(overlayName, trackType) {
  const baseSize = overlayConfig[overlayName]?.baseSize;
  if (!baseSize) return null;

  // Other overlays (width/height)
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
  const baseSize = resolveBaseSize(overlayName, trackType);
  if (!baseSize) return;

  win.webContents.setZoomFactor(zoomFactor);
  win.setSize(
    Math.round(baseSize.width * zoomFactor),
    Math.round(baseSize.height * zoomFactor),
    animate
  );
}

module.exports = {
  resolveBaseSize,
  applyOverlaySize,
};

import { mountOverlayFeature } from './overlayShell.js';
import { watchDragModeBorder } from './dragModeBorder.js';

// Read the overlay feature name from the current shell URL.
const featureName = new URLSearchParams(window.location.search).get('feature');

// Mark the window while overlays can be dragged.
watchDragModeBorder(document).catch((error) => {
    console.error('Unable to track overlay drag mode:', error);
});

// Mount the requested overlay feature into the shared shell.
mountOverlayFeature(document, featureName).catch((error) => {
    console.error('Unable to initialize overlay:', error);
});

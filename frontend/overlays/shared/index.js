import { mountOverlayFeature } from './overlayShell.js';

// Read the overlay feature name from the current shell URL.
const featureName = new URLSearchParams(window.location.search).get('feature');

// Mount the requested overlay feature into the shared shell.
mountOverlayFeature(document, featureName).catch((error) => {
    console.error('Unable to initialize overlay:', error);
});

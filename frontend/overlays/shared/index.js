import { mountOverlayFeature } from './overlayShell.js';

const featureName = new URLSearchParams(window.location.search).get('feature');

mountOverlayFeature(document, featureName).catch((error) => {
    console.error('Unable to initialize overlay:', error);
});

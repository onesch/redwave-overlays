// Allow only safe overlay feature names used to build resource paths.
const FEATURE_NAME_PATTERN = /^[a-z][a-z0-9-]*$/;

// Build HTML, CSS, and JS resource paths for an overlay feature.
export function getFeatureResources(featureName) {
    if (!FEATURE_NAME_PATTERN.test(featureName)) {
        throw new Error(`Invalid overlay feature name: ${featureName}`);
    }

    const featureRoot = `/overlays/${featureName}`;
    return {
        content: `${featureRoot}/${featureName}.html`,
        stylesheet: `${featureRoot}/${featureName}.css`,
        entrypoint: `${featureRoot}/index.js`,
    };
}

// Load and mount the requested overlay feature into the shared shell.
export async function mountOverlayFeature(document, featureName, {
    fetchImpl = globalThis.fetch.bind(globalThis),
    importModule = (path) => import(path),
} = {}) {
    const resources = getFeatureResources(featureName);
    // Load the feature-specific HTML fragment.
    const response = await fetchImpl(resources.content);
    if (!response.ok) {
        throw new Error(`Unable to load ${featureName} overlay content (${response.status})`);
    }

    // Find the shared container where feature markup will be mounted.
    const overlayBody = document.querySelector('.overlay-body');
    if (!overlayBody) {
        throw new Error('The shared overlay shell is missing .overlay-body');
    }

    // Mount the feature markup into the shared overlay document.
    document.title = featureName
        .split('-')
        .map((word) => word.charAt(0).toUpperCase() + word.slice(1))
        .join(' ');
    overlayBody.innerHTML = await response.text();

     // Attach the feature-specific stylesheet.
    const stylesheet = document.createElement('link');
    stylesheet.rel = 'stylesheet';
    stylesheet.href = resources.stylesheet;
    document.head.append(stylesheet);

    // Start the feature by importing its composition root.
    await importModule(resources.entrypoint);
}

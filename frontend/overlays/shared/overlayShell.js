const FEATURE_NAME_PATTERN = /^[a-z][a-z0-9-]*$/;

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

export async function mountOverlayFeature(document, featureName, {
    fetchImpl = globalThis.fetch.bind(globalThis),
    importModule = (path) => import(path),
} = {}) {
    const resources = getFeatureResources(featureName);
    const response = await fetchImpl(resources.content);
    if (!response.ok) {
        throw new Error(`Unable to load ${featureName} overlay content (${response.status})`);
    }

    const overlayBody = document.querySelector('.overlay-body');
    if (!overlayBody) {
        throw new Error('The shared overlay shell is missing .overlay-body');
    }

    document.title = featureName.charAt(0).toUpperCase() + featureName.slice(1);
    overlayBody.innerHTML = await response.text();

    const stylesheet = document.createElement('link');
    stylesheet.rel = 'stylesheet';
    stylesheet.href = resources.stylesheet;
    document.head.append(stylesheet);

    await importModule(resources.entrypoint);
}

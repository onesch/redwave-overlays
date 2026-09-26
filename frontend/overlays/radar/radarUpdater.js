import { BaseUpdater } from '../shared/baseUpdater.js';

export class RadarUpdater extends BaseUpdater {
    constructor(api, renderer, options = {}) {
        super(api, renderer, {
            ...options,
            overlayName: 'radar',
        });
    }

    // Initialize radar-specific settings.
    async initFeature() {
        await this.initRadarVisibility();
    }

    // Load radar visibility mode and subscribe to changes.
    async initRadarVisibility() {
        const mode =
            await this.electronAPI.getRadarVisibility?.(this.overlayName);

        this.renderer.setRadarMode(mode);

        this.electronAPI.onRadarVisibilityUpdate?.((value) => {
            this.renderer.setRadarMode(value);
        });
    }

    async getDto() {
        return this.api.getRadar();
    }
}

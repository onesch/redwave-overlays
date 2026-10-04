import { BaseUpdater } from '../shared/baseUpdater.js';

export class TrackMapUpdater extends BaseUpdater {
    constructor(api, renderer, options = {}) {
        super(api, renderer, {
            updateInterval: 100,
            ...options,
            overlayName: 'track-map',
        });
    }

    // Initialize track-map-specific settings.
    async initFeature() {
        await this.initTrackType();
    }

    // Load the selected track type and subscribe to runtime changes.
    async initTrackType() {
        const type = await this.electronAPI.getTrackType?.(
            this.overlayName
        );

        if (type) {
            this.renderer.setTrackType(type);
        }

        this.electronAPI.onTrackTypeUpdate?.((value) => {
            this.renderer.setTrackType(value);
        });
    }

    // Fetch the latest track map DTO from the backend API.
    async getDto() {
        return this.api.getTrackMap();
    }
}

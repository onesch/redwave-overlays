import { BaseUpdater } from '../shared/baseUpdater.js';

export class TrackMapUpdater extends BaseUpdater {
    constructor(api, renderer, options = {}) {
        super(api, renderer, {
            ...options,
            overlayName: 'track-map',
        });
    }

    async initFeature() {
        const type = await this.electronAPI.getTrackType?.(this.overlayName);
        if (type) this.renderer.setTrackType(type);

        this.electronAPI.onTrackTypeUpdate?.((value) => {
            this.renderer.setTrackType(value);
        });
    }

    async getDto() {
        return this.api.getTrackMap();
    }
}

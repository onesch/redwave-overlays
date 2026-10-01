import { BaseUpdater } from '../shared/baseUpdater.js';

export class TelemetryUpdater extends BaseUpdater {
    constructor(api, renderer, options = {}) {
        super(api, renderer, {
            updateInterval: 50,
            ...options,
            overlayName: 'telemetry',
        });
    }

    async getDto() {
        return this.api.getTelemetry();
    }
}

import { BaseUpdater } from '../shared/baseUpdater.js';

export class TelemetryUpdater extends BaseUpdater {
    constructor(api, renderer, options = {}) {
        super(api, renderer, {
            updateInterval: 50,
            ...options,
            overlayName: 'telemetry',
        });
    }

    // Initialize telemetry-specific settings.
    async initFeature() {
        await this.initSpeedUnit();
    }

    // Load the selected speed unit and subscribe to runtime changes.
    async initSpeedUnit() {
        const unit = await this.electronAPI.getSpeedUnit?.(this.overlayName);
        this.renderer.setSpeedUnit(unit);

        this.electronAPI.onSpeedUnitUpdate?.((value) => {
            this.renderer.setSpeedUnit(value);
        });
    }

    async getDto() {
        return this.api.getTelemetry();
    }
}

import { BaseUpdater } from '../shared/baseUpdater.js';

export class LeaderboardUpdater extends BaseUpdater {
    constructor(api, renderer, options = {}) {
        // Configure shared updater behavior for the leaderboard overlay.
        super(api, renderer, {
            ...options,
            overlayName: 'leaderboard',
        });
    }

    // Initialize leaderboard-specific settings.
    async initFeature() {
        await this.initLastLapFormat();
    }

    // Load the selected Last Lap format and subscribe to runtime changes.
    async initLastLapFormat() {
        const format = await this.electronAPI.getLastLapFormat?.(this.overlayName);
        this.renderer.setLastLapFormat(format);

        this.electronAPI.onLastLapFormatUpdate?.((value) => {
            this.renderer.setLastLapFormat(value);
        });
    }

    async getDto() {
        return this.api.getLeaderboard();
    }
}

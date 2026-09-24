import { BaseUpdater } from '../shared/baseUpdater.js';

export class LeaderboardUpdater extends BaseUpdater {
    constructor(api, renderer, options = {}) {
        super(api, renderer, {
            ...options,
            overlayName: 'leaderboard',
        });
    }

    async initFeature() {
        await this.initLastLapFormat();
    }

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

    isVisible(location) {
        if (!location) return true;
        if (this.displayMode === 'all_time') return true;
        return this.displayMode === location;
    }

    async handleDto(dto) {
        if ((dto.status === 'waiting' && dto.location === undefined) ||
            !this.isVisible(dto.location)) {
            this.renderer.setVisible(false);
            return;
        }

        this.renderer.setVisible(true);
        this.renderer.render(dto);
    }
}

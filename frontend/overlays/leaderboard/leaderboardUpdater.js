export class LeaderboardUpdater {
    constructor(api, renderer, {
        electronAPI = globalThis.window?.electronAPI,
        updateInterval = 100,
        timer = globalThis,
        logger = console,
    } = {}) {
        this.api = api;
        this.renderer = renderer;
        this.electronAPI = electronAPI ?? {};
        this.updateInterval = updateInterval;
        this.timer = timer;
        this.logger = logger;
        this.overlayName = 'leaderboard';
        this.displayMode = 'all_time';
        this.timerId = null;
    }

    async start() {
        await this.initDisplayMode();
        await this.initBackgroundOpacity();
        await this.initLastLapFormat();
        await this.update();

        this.timerId = this.timer.setInterval(() => {
            this.update();
        }, this.updateInterval);
    }

    stop() {
        if (this.timerId !== null) {
            this.timer.clearInterval(this.timerId);
            this.timerId = null;
        }
    }

    async initDisplayMode() {
        const mode = await this.electronAPI.getDisplayMode?.(this.overlayName);
        this.displayMode = mode ?? 'all_time';

        this.electronAPI.onDisplayModeUpdate?.((value) => {
            this.displayMode = value;
        });
    }

    async initBackgroundOpacity() {
        const opacity = await this.electronAPI.getOverlayBgOpacity?.(this.overlayName);
        if (opacity != null) this.renderer.setBackgroundOpacity(opacity);

        this.electronAPI.onOverlayBgOpacityUpdate?.((value) => {
            this.renderer.setBackgroundOpacity(value);
        });
    }

    async initLastLapFormat() {
        const format = await this.electronAPI.getLastLapFormat?.(this.overlayName);
        this.renderer.setLastLapFormat(format);

        this.electronAPI.onLastLapFormatUpdate?.((value) => {
            this.renderer.setLastLapFormat(value);
        });
    }

    isVisible(location) {
        if (!location) return true;
        if (this.displayMode === 'all_time') return true;
        return this.displayMode === location;
    }

    async update() {
        try {
            const dto = await this.api.getLeaderboard();

            if (!dto) {
                this.logger.error('Error:', 'lost data');
                return;
            }
            if (dto.error) {
                this.logger.error('Error:', dto.error);
                return;
            }

            if ((dto.status === 'waiting' && dto.location === undefined) ||
                !this.isVisible(dto.location)) {
                this.renderer.setVisible(false);
                return;
            }

            this.renderer.setVisible(true);
            this.renderer.render(dto);
        } catch (error) {
            this.logger.error('Error:', error);
        }
    }
}

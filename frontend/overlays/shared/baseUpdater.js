export class BaseUpdater {
    constructor(api, renderer, {
        overlayName,
        electronAPI = globalThis.window?.electronAPI,
        updateInterval = 100,
        timer = globalThis,
        logger = console,
    } = {}) {
        this.api = api;
        this.renderer = renderer;
        this.overlayName = overlayName;
        this.electronAPI = electronAPI ?? {};
        this.updateInterval = updateInterval;
        this.timer = timer;
        this.logger = logger;
        this.displayMode = 'all_time';
        this.timerId = null;
    }

    async start() {
        await this.initDisplayMode();
        await this.initBackgroundOpacity();
        await this.initFeature();
        await this.update();

        this.timerId = this.timer.setInterval(() => {
            this.update();
        }, this.updateInterval);
    }

    stop() {
        if (this.timerId === null) return;

        this.timer.clearInterval(this.timerId);
        this.timerId = null;
    }

    async initDisplayMode() {
        if (!this.overlayName) return;

        const mode = await this.electronAPI.getDisplayMode?.(this.overlayName);
        this.displayMode = mode ?? 'all_time';

        this.electronAPI.onDisplayModeUpdate?.((value) => {
            this.displayMode = value;
        });
    }

    async initBackgroundOpacity() {
        if (!this.overlayName) return;

        const opacity = await this.electronAPI.getOverlayBgOpacity?.(this.overlayName);
        if (opacity != null) this.renderer.setBackgroundOpacity?.(opacity);

        this.electronAPI.onOverlayBgOpacityUpdate?.((value) => {
            this.renderer.setBackgroundOpacity?.(value);
        });
    }

    async initFeature() {}

    async getDto() {
        throw new Error('Concrete updater must implement getDto()');
    }

    async handleDto(_dto) {
        throw new Error('Concrete updater must implement handleDto()');
    }

    async update() {
        try {
            const dto = await this.getDto();

            if (!dto) {
                this.logger.error('Error:', 'lost data');
                return;
            }
            if (dto.error) {
                this.logger.error('Error:', dto.error);
                return;
            }

            await this.handleDto(dto);
        } catch (error) {
            this.logger.error('Error:', error);
        }
    }
}

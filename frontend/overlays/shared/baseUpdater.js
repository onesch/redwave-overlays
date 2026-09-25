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
    }

    // Initialize shared overlay state and start the update loop.
    async start() {
        await this.initDisplayMode();
        await this.initBackgroundOpacity();
        await this.initFeature();
        await this.update();

        // Poll overlay data at the configured interval.
        this.timer.setInterval(() => {
            this.update();
        }, this.updateInterval);
    }

    // Fetch, validate, and render the latest overlay DTO.
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
            // Hide the overlay while waiting or when display mode does not match.
            if (
                (dto.status === 'waiting' && dto.location === undefined) ||
                !this.isVisible(dto.location)
            ) {
                this.renderer.setVisible(false);
                return;
            }

            // Render valid and visible overlay data.
            this.renderer.setVisible(true);
            this.renderer.render(dto);
        } catch (error) {
            this.logger.error('Error:', error);
        }
    }

    // Must be implemented by each concrete overlay updater.
    async getDto() {
        throw new Error('Concrete updater must implement getDto()');
    }

    // Check whether the overlay should be visible for the current location.
    isVisible(location) {
        if (!location) return true;
        if (this.displayMode === 'all_time') return true;
        return this.displayMode === location;
    }

    // Load display mode and subscribe to runtime updates.
    async initDisplayMode() {
        if (!this.overlayName) return;

        const mode = await this.electronAPI.getDisplayMode?.(this.overlayName);
        this.displayMode = mode ?? 'all_time';

        this.electronAPI.onDisplayModeUpdate?.((value) => {
            this.displayMode = value;
        });
    }

    // Load background opacity and forward changes to the renderer.
    async initBackgroundOpacity() {
        if (!this.overlayName) return;

        const opacity = await this.electronAPI.getOverlayBgOpacity?.(this.overlayName);
        if (opacity != null) this.renderer.setBackgroundOpacity?.(opacity);

        this.electronAPI.onOverlayBgOpacityUpdate?.((value) => {
            this.renderer.setBackgroundOpacity?.(value);
        });
    }

    // Optional hook for overlay-specific initialization.
    async initFeature() {}
}

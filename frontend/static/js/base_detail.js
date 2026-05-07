class OverlayBase {
    constructor(overlayName) {
        this.overlayName = overlayName;
        this.init();
    }

    init() {
        this.zoomRange = document.getElementById('zoomRange');
        this.zoomValue = document.getElementById('zoomValue');

        this.opacityRange = document.getElementById('opacityRange');
        this.opacityValue = document.getElementById('opacityValue');

        this.openBtn = document.getElementById('OpenBtn');
        this.toggleMovementBtn = document.getElementById('ToggleMovementBtn');

        this.displayButtons = {
            all_time: document.getElementById('DisplayAllTimeBtn'),
            track:    document.getElementById('DisplayTrackBtn'),
            garage:   document.getElementById('DisplayGarageBtn'),
        };

        this.autoStartButtons = {
            on:  document.getElementById('AutoStartOnBtn'),
            off: document.getElementById('AutoStartOffBtn'),
        };

        this.setupEventListeners();
        this.loadZoomSettings();
        this.loadBackgroundOpacitySettings();
        this.loadDisplayMode();
        this.loadAutoStartMode();
        this.loadOverlayMovementState();
    }

    setupEventListeners() {
        if (this.zoomRange) {
            this.zoomRange.addEventListener('input', () => this.handleZoomChange());
        }
        if (this.opacityRange) {
            this.opacityRange.addEventListener('input', () => this.handleBackgroundOpacityChange());
        }
        if (this.toggleMovementBtn) {
            this.toggleMovementBtn.addEventListener('click', () => this.handleOverlayMovementToggle());
        }
        window.electronAPI.onOverlayMovementStateUpdate?.((isMovable) => {
            this.applyOverlayMovementState(isMovable);
        });
        Object.entries(this.displayButtons).forEach(([mode, btn]) => {
            if (btn) btn.addEventListener('click', () => this.handleDisplayModeChange(mode));
        });
        Object.entries(this.autoStartButtons).forEach(([value, btn]) => {
            if (btn) btn.addEventListener('click', () => this.handleAutoStartModeChange(value));
        });
    }

    async loadZoomSettings() {
        const zoomFactor = await window.electronAPI.getOverlayZoom(this.overlayName);
        const percent = Math.round(zoomFactor * 100);
        this.zoomRange.value = percent;
        this.zoomValue.textContent = `${percent}%`;
    }

    handleZoomChange() {
        const percent = this.zoomRange.value;
        this.zoomValue.textContent = `${percent}%`;
        window.electronAPI.setOverlayZoom(this.overlayName, percent / 100);
    }

    async loadBackgroundOpacitySettings() {
        if (!this.opacityRange && !this.opacityValue) return;

        const opacity = await this.getBackgroundOpacity();
        if (opacity != null) {
            if (this.opacityRange) this.opacityRange.value = opacity;
            if (this.opacityValue) this.opacityValue.textContent = opacity.toFixed(2);

            const card = document.querySelector('.card');
            if (card) card.style.setProperty('--overlay-bg-opacity', opacity);
        }
    }

    handleBackgroundOpacityChange() {
        if (!this.opacityRange && !this.opacityValue) return;

        const value = parseFloat(this.opacityRange.value);
        if (this.opacityValue) this.opacityValue.textContent = value.toFixed(2);

        this.setBackgroundOpacity(value);
    }

    async getBackgroundOpacity() {
        if (window.electronAPI.getOverlayBgOpacity) {
            return window.electronAPI.getOverlayBgOpacity(this.overlayName);
        }
        return window.electronAPI.getCardBgOpacity?.(this.overlayName);
    }

    setBackgroundOpacity(value) {
        if (window.electronAPI.setOverlayBgOpacity) {
            window.electronAPI.setOverlayBgOpacity(this.overlayName, value);
            return;
        }
    }

    async loadDisplayMode() {
        const mode = await window.electronAPI.getDisplayMode?.(this.overlayName);
        this.applyDisplayMode(mode ?? 'all_time');
    }

    handleDisplayModeChange(mode) {
        window.electronAPI.setDisplayMode?.(this.overlayName, mode);
        this.applyDisplayMode(mode);
    }

    applyDisplayMode(mode) {
        Object.entries(this.displayButtons).forEach(([key, btn]) => {
            if (btn) btn.classList.toggle('active', key === mode);
        });
    }

    async loadAutoStartMode() {
        const mode = await window.electronAPI.getAutoStartMode?.(this.overlayName);
        this.applyAutoStartMode(mode ?? 'off');
    }

    handleAutoStartModeChange(value) {
        window.electronAPI.setAutoStartMode?.(this.overlayName, value);
        this.applyAutoStartMode(value);
    }

    applyAutoStartMode(value) {
        Object.entries(this.autoStartButtons).forEach(([key, btn]) => {
            if (btn) btn.classList.toggle('active', key === value);
        });
    }

    async loadOverlayMovementState() {
        if (!this.toggleMovementBtn || !window.electronAPI.getOverlayMovementState) return;

        const isMovable = await window.electronAPI.getOverlayMovementState();
        this.applyOverlayMovementState(isMovable);
    }

    async handleOverlayMovementToggle() {
        if (!window.electronAPI.toggleOverlayMovement) return;

        const isMovable = await window.electronAPI.toggleOverlayMovement();
        this.applyOverlayMovementState(isMovable);
    }

    applyOverlayMovementState(isMovable) {
        if (!this.toggleMovementBtn) return;

        this.toggleMovementBtn.innerHTML = `
            <span class="material-symbols-outlined">
                ${isMovable ? 'lock_open_right' : 'lock'}
            </span>
        `;

        this.toggleMovementBtn.classList.toggle(
            'primary-btn',
            isMovable,
        );
    }
}

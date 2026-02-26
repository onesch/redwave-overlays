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

        this.displayButtons = {
            all_time: document.getElementById('DisplayAllTimeBtn'),
            track:    document.getElementById('DisplayTrackBtn'),
            garage:   document.getElementById('DisplayGarageBtn'),
        };

        this.setupEventListeners();
        this.loadZoomSettings();
        this.loadOpacitySettings();
        this.loadDisplayMode();
    }

    setupEventListeners() {
        if (this.zoomRange) {
            this.zoomRange.addEventListener('input', () => this.handleZoomChange());
        }
        if (this.opacityRange) {
            this.opacityRange.addEventListener('input', () => this.handleOpacityChange());
        }
        Object.entries(this.displayButtons).forEach(([mode, btn]) => {
            if (btn) btn.addEventListener('click', () => this.handleDisplayModeChange(mode));
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

    async loadOpacitySettings() {
        if (!this.opacityRange && !this.opacityValue) return;

        const opacity = await window.electronAPI.getCardBgOpacity?.(this.overlayName);
        if (opacity != null) {
            if (this.opacityRange) this.opacityRange.value = opacity;
            if (this.opacityValue) this.opacityValue.textContent = opacity.toFixed(2);

            const card = document.querySelector('.card');
            if (card) card.style.setProperty('--card-bg-opacity', opacity);
        }
    }

    handleOpacityChange() {
        if (!this.opacityRange && !this.opacityValue) return;

        const value = parseFloat(this.opacityRange.value);
        if (this.opacityValue) this.opacityValue.textContent = value.toFixed(2);

        window.electronAPI.setCardBgOpacity?.(this.overlayName, value);
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
}

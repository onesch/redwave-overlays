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

        this.setupEventListeners();
        this.loadZoomSettings();
        this.loadOpacitySettings();
    }

    setupEventListeners() {
        if (this.zoomRange) {
            this.zoomRange.addEventListener('input', () => this.handleZoomChange());
        }
        if (this.opacityRange) {
            this.opacityRange.addEventListener('input', () => this.handleOpacityChange());
        }
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
}

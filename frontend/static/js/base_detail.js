class OverlayBase {
    constructor(overlayName) {
        this.overlayName = overlayName;
        this.init();
    }

    init() {
        this.zoomRange = document.getElementById('zoomRange');
        this.zoomValue = document.getElementById('zoomValue');
        this.openBtn = document.getElementById('OpenBtn');

        this.setupEventListeners();
        this.loadZoomSettings();
    }

    setupEventListeners() {
        this.zoomRange.addEventListener('input', () => this.handleZoomChange());
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
}

// Экспорт для использования в других модулях
if (typeof module !== 'undefined' && module.exports) {
    module.exports = OverlayBase;
} else {
    window.OverlayBase = OverlayBase;
}

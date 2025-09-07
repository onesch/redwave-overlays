class OverlayBase {
    constructor(overlayName) {
        this.overlayName = overlayName;
        this.init();
    }

    init() {
        this.zoomRange = document.getElementById('zoomRange');
        this.zoomValue = document.getElementById('zoomValue');
        this.videoWrapper = document.getElementById('videoWrapper');
        this.videoModal = document.getElementById('videoModal');
        this.modalVideo = document.getElementById('modalVideo');
        this.closeBtn = document.querySelector('.close');
        this.progressBar = document.getElementById('progressBar');
        this.openBtn = document.getElementById('OpenBtn');

        this.setupEventListeners();
        this.loadZoomSettings();
    }

    setupEventListeners() {
        this.zoomRange.addEventListener('input', () => this.handleZoomChange());
        this.videoWrapper.addEventListener('click', () => this.openVideoModal());
        this.closeBtn.addEventListener('click', () => this.closeVideoModal());
        
        window.addEventListener('click', (e) => {
            if (e.target === this.videoModal) this.closeVideoModal();
        });

        this.modalVideo.addEventListener('timeupdate', () => this.updateProgressBar());
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

    openVideoModal() {
        this.videoModal.style.display = 'flex';
        const source = document.querySelector('.video-wrapper video source');
        if (source) {
            this.modalVideo.src = source.src;
            this.modalVideo.currentTime = 0;
            this.modalVideo.play().catch(err => console.warn("Autoplay blocked:", err));
        } else {
            console.error("Видео-источник не найден");
        }
    }

    closeVideoModal() {
        this.modalVideo.pause();
        this.modalVideo.src = "";
        this.videoModal.style.display = 'none';
    }

    updateProgressBar() {
        const percent = (this.modalVideo.currentTime / this.modalVideo.duration) * 100;
        this.progressBar.style.width = percent + '%';
    }
}

// Экспорт для использования в других модулях
if (typeof module !== 'undefined' && module.exports) {
    module.exports = OverlayBase;
} else {
    window.OverlayBase = OverlayBase;
}
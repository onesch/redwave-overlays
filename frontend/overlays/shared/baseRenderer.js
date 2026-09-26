export class BaseRenderer {
    constructor(document) {
        this.document = document;
    }

    // Show or hide the whole overlay.
    setVisible(visible) {
        const body = this.document.querySelector('.overlay-body');

        if (body) {
            body.style.visibility = visible ? 'visible' : 'hidden';
        }
    }
}

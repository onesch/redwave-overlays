import { BaseRenderer } from '../shared/baseRenderer.js';

const RADAR_HEIGHT = 260;
const CENTER_Y = RADAR_HEIGHT / 2;
const SIDE_BOX_HEIGHT = 40;

export class RadarRenderer extends BaseRenderer {
    constructor(document) {
        super(document);

        this.radarMode = undefined;
    }

    render(data) {
        this.setFrontBack(
            this.document.getElementById('fb-ahead'),
            data.ahead_m,
            data.ahead_severity,
        );
        this.setFrontBack(
            this.document.getElementById('fb-behind'),
            data.behind_m,
            data.behind_severity,
        );

        const bothSides = Boolean(data.left && data.right);
        this.renderSide('side-left', 'left', data.left, bothSides);
        this.renderSide('side-right', 'right', data.right, bothSides);
        this.updateRadarVisibility(data);
    }

    setRadarMode(mode) {
        this.radarMode = mode;
    }

    setFrontBack(element, distance, severity) {
        element.classList.remove('sev-red', 'sev-yellow', 'sev-gray');

        if (distance == null) {
            element.style.opacity = 0;
            return;
        }

        element.style.opacity = 1;
        if (severity === 'red') element.classList.add('sev-red');
        else if (severity === 'yellow') element.classList.add('sev-yellow');
        else element.classList.add('sev-gray');
    }

    renderSide(id, side, info, bothSides) {
        if (!info) {
            this.document.getElementById(id)?.remove();
            return;
        }

        const element = this.getSideElement(id, side);
        element.classList.remove('red', 'gray');

        const offsetRatio = bothSides ? 0 : info.offset_ratio;
        const offsetPx = offsetRatio * (RADAR_HEIGHT / 2 - SIDE_BOX_HEIGHT / 2);
        element.style.top = `${CENTER_Y - SIDE_BOX_HEIGHT - offsetPx - 20}px`;
        element.style.opacity = 1;
        element.classList.add('red');
    }

    // Recreating a returning indicator prevents a transition from its old top position
    getSideElement(id, side) {
        let element = this.document.getElementById(id);
        if (!element) {
            element = this.document.createElement('div');
            element.id = id;
            element.className = `side-box ${side}`;
            this.document.querySelector('.radar-container').appendChild(element);
        }
        return element;
    }

        // Update radar visibility based on the current mode and distances
    updateRadarVisibility(data) {
        const element = this.document.querySelector('.radar-container');

        // Always show if any cars are nearby
        if (data.left || data.right) {
            element.style.display = 'block';
            element.style.opacity = 1;
            return;
        }

        // Always show overlay
        if (this.radarMode === 'show') {
            element.style.display = 'block';
            element.style.opacity = 1;
            return;
        }

        // Hide if no cars nearby
        if (this.radarMode === 'hide') {
            if (!data.ahead_nearby && !data.behind_nearby) {
                element.style.opacity = 0;
                element.style.pointerEvents = 'none';
                return;
            }
            element.style.opacity = 1;
            element.style.pointerEvents = 'auto';
            return;
        }

        // Dim if no cars nearby
        element.style.display = 'block';
        element.style.opacity = !data.ahead_nearby && !data.behind_nearby ? 0.35 : 1;
    }
}

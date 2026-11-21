import { BaseRenderer } from '../shared/baseRenderer.js';
import { TrackPath } from './trackPath.js';

const SVG_NS = 'http://www.w3.org/2000/svg';

// Half length of the start/finish line in track (viewBox) units. The line
// sticks out of the track (45 units wide in track-map.css) on both sides.
const START_FINISH_HALF_LENGTH = 40;


export class TrackMapRenderer extends BaseRenderer {
    constructor(document) {
        super(document);

        this.trackType = 'linear';
        this.cars = {}; // key: player_id, value: div
        // Track geometry from the backend: { viewBox, path, startFinish },
        // or null while the track is unknown or its map is unavailable.
        this.track = null;
        this.trackId = null;

        this.trackContainer = document.getElementById('track-container');
        this.trackLine = document.getElementById('track-line');
    }

    render(data) {
        if (data.status === 'ok' && data.is_session_changed) {
            this.clearCars();
        }

        const track = data.track ?? null;
        if ((track?.id ?? null) !== this.trackId) {
            this.setTrack(track);
        }

        this.renderCars(data.cars, data.player_id);
    }

    // Store the track geometry of the DTO and redraw the track map with it.
    setTrack(track) {
        this.trackId = track?.id ?? null;
        const path = track ? new TrackPath(track.points) : null;
        this.track = path?.length > 0
            ? { viewBox: track.view_box, path, startFinish: track.start_finish }
            : null;
        if (this.trackType === 'track') {
            this.renderTrackLine();
        }
    }

    // Change track type and re-render
    setTrackType(type) {
        this.trackType = type;
        this.document.body.dataset.trackType = type;
        this.clearCars();
        this.renderTrackLine();
    }

    // Renders the layout of the current track type
    renderTrackLine() {
        this.trackLine.replaceChildren();
        this.trackLine.classList.remove('circle', 'linear');
        if (this.trackType === 'track') {
            this.renderSvgTrack();
            return;
        }
        this.trackLine.classList.add(this.trackType);

        if (this.trackType === 'circle') {
            this.trackContainer.style.aspectRatio = '1 / 1';
            // Finish line at the bottom of the circle
            const finish = this.document.createElement('div');
            finish.className = 'track-finish-line';
            this.trackLine.appendChild(finish);
        } else if (this.trackType === 'linear') {
            this.trackContainer.style.aspectRatio = '4 / 1';
        }
    }

    // Draws the real track layout in its viewBox, sized to the container.
    renderSvgTrack() {
        if (!this.track) {
            this.trackContainer.style.aspectRatio = '';
            return;
        }

        const { viewBox, path } = this.track;
        this.trackContainer.style.aspectRatio = `${viewBox[2]} / ${viewBox[3]}`;

        const svg = this._createSvgElement('svg', { viewBox: viewBox.join(' ') });
        const pathData = path.toSvgPathData();
        svg.appendChild(this._createSvgElement('path', { class: 'track outer', d: pathData }));
        svg.appendChild(this._createSvgElement('path', { class: 'track surface', d: pathData }));
        svg.appendChild(this._createStartFinishLine());

        this.trackLine.appendChild(svg);
    }

    // Line across the track at the start/finish position.
    _createStartFinishLine() {
        const { x, y, dx, dy } = this.track.path.pointAt(this.track.startFinish.pct);
        // Normal of the track direction, scaled to the half line length.
        const nx = -dy * START_FINISH_HALF_LENGTH;
        const ny = dx * START_FINISH_HALF_LENGTH;

        return this._createSvgElement('line', {
            class: 'track-start-finish',
            x1: x - nx,
            y1: y - ny,
            x2: x + nx,
            y2: y + ny,
        });
    }

    _createSvgElement(tag, attributes) {
        const element = this.document.createElementNS(SVG_NS, tag);
        Object.entries(attributes).forEach(([name, value]) => {
            element.setAttribute(name, value);
        });
        return element;
    }

    // Cleaning old cars from data this.cars
    clearCars() {
        Object.values(this.cars).forEach(car => car.remove());
        this.cars = {};
    }

    // Render all cars received from API
    renderCars(cars, playerId) {
        // Without a track map there is nothing to place the cars on.
        if (this.trackType === 'track' && !this.track) {
            this.clearCars();
            return;
        }

        cars.forEach(car => {
            if (this._isCarInactiveAndRemove(car)) return;

            let carDiv = this.cars[car.player_id] || this.createCarDiv(car);
            this.updateCarAppearance(carDiv, car, playerId);
            this.updateCarPosition(carDiv, car.lap_dist_pct);
        });
    }

    // Remove a car that is no longer on the road
    _isCarInactiveAndRemove(car) {
        if (car.lap_dist_pct === -1) {
            if (this.cars[car.player_id]) {
                this.cars[car.player_id].remove();
                delete this.cars[car.player_id];
            }
            return true;
        }
        return false;
    }

    // Create new car DOM element
    createCarDiv(car) {
        const carDiv = this.document.createElement('div');
        carDiv.classList.add('track-map-car');
        carDiv.innerText = car.car_number;
        carDiv.style.setProperty('--car-color', car.color);

        this.trackContainer.appendChild(carDiv);
        this.cars[car.player_id] = carDiv;

        carDiv.style.transition = 'top 0.1s linear, left 0.1s linear';
        return carDiv;
    }

    // Highlight player car and adjust z-index
    updateCarAppearance(carDiv, car, playerId) {
        if (car.player_id === playerId) {
            carDiv.classList.add('player');
            carDiv.style.zIndex = '999';
        } else {
            carDiv.classList.remove('player');
            carDiv.style.zIndex = '1';
        }
    }

    // Update car position based on current track type
    updateCarPosition(carDiv, lapDistPct) {
        if (this.trackType === 'track') {
            this.positionCarSvgTrack(carDiv, lapDistPct);
        } else if (this.trackType === 'circle') {
            this.positionCarCircle(carDiv, lapDistPct);
        } else if (this.trackType === 'linear') {
            this.positionCarLinear(carDiv, lapDistPct);
        }
    }

    // Positions a car dot on the track layout, counting the lap distance
    // from the start/finish line in the track's direction of travel.
    positionCarSvgTrack(carDiv, lapDistPct) {
        const { path, startFinish } = this.track;
        const point = path.pointAt(startFinish.pct + startFinish.direction * lapDistPct);
        const { x, y } = this._trackToContainer(point);

        this._applyCarTransition(carDiv, lapDistPct, x, y);
    }

    // Positions a car dot on a circle track layout using lap distance percentage
    positionCarCircle(carDiv, lapDistPct) {
        // Compute circle geometry centered in the container
        const cr = this.trackContainer.getBoundingClientRect();
        const size = Math.min(cr.width, cr.height);
        const cx = cr.width / 2;
        const cy = cr.height / 2;
        const radius = size * 0.35;

        // Convert lap percentage to an angle and project onto the circle
        const angle = -lapDistPct * 2 * Math.PI + Math.PI / 2;
        const x = cx + radius * Math.cos(angle);
        const y = cy + radius * Math.sin(angle);

        this._applyCarTransition(carDiv, lapDistPct, x, y);
    }

    // Converts track (viewBox) coordinates to container pixels, matching how
    // the SVG scales its viewBox (default preserveAspectRatio: xMidYMid meet).
    _trackToContainer({ x, y }) {
        const cr = this.trackContainer.getBoundingClientRect();
        const [minX, minY, width, height] = this.track.viewBox;
        const scale = Math.min(cr.width / width, cr.height / height);

        return {
            x: (x - minX) * scale + (cr.width - width * scale) / 2,
            y: (y - minY) * scale + (cr.height - height * scale) / 2,
        };
    }

    // Positions a car dot on a horizontal linear bar using lap distance percentage
    positionCarLinear(carDiv, lapDistPct) {
        // Map lap percentage to a pixel X position across the container width
        const cr = this.trackContainer.getBoundingClientRect();
        const x = lapDistPct * cr.width;
        const y = cr.height / 2;

        this._applyCarTransition(carDiv, lapDistPct, x, y);
    }

    // Applies smooth CSS transition to a car dot, suppressing it on lap wrap-around jumps
    _applyCarTransition(carDiv, lapDistPct, x, y) {
        const lastPct = parseFloat(carDiv.dataset.lastLapPct ?? lapDistPct);
        carDiv.style.transition = Math.abs(lastPct - lapDistPct) > 0.5 ? 'none' : 'top 0.1s linear, left 0.1s linear';
        carDiv.style.left = `${x}px`;
        carDiv.style.top = `${y}px`;
        carDiv.dataset.lastLapPct = lapDistPct;
    }
}

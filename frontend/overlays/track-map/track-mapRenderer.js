import { BaseRenderer } from '../shared/baseRenderer.js';
import { TrackPath } from './trackPath.js';

const SVG_NS = 'http://www.w3.org/2000/svg';

// Checkered start/finish grid: 2 cells along the track, 5 across it.
const START_FINISH_COLS = 2;
const START_FINISH_ROWS = 5;
const CAR_TRANSITION = 'transform 0.1s linear';

// Marker shapes (see data-shape in track-map.css), assigned to car classes in
// order of appearance; the first one is also used in single-class sessions.
const CAR_SHAPES = ['circle', 'square', 'diamond', 'hexagon', 'pentagon'];

// Synthetic track geometry.
const LINEAR_VIEW_BOX = [0, 0, 300, 75];
const CIRCLE_VIEW_BOX = [0, 0, 100, 100];

const LINEAR_POINTS = [
    [18, 37.5],
    [282, 37.5],
];

const CIRCLE_SEGMENTS = 128;
const CIRCLE_RADIUS = 35;


// Tight view box around the track points: the backend view box carries its
// own empty margins, which would shrink the map inside the window.
// Returns null when the points have no area.
function getPointsViewBox(points) {
    let minX = Infinity;
    let minY = Infinity;
    let maxX = -Infinity;
    let maxY = -Infinity;

    for (const [x, y] of points) {
        minX = Math.min(minX, x);
        minY = Math.min(minY, y);
        maxX = Math.max(maxX, x);
        maxY = Math.max(maxY, y);
    }

    const width = maxX - minX;
    const height = maxY - minY;

    if (!(width > 0 && height > 0)) {
        return null;
    }

    return [minX, minY, width, height];
}

export class TrackMapRenderer extends BaseRenderer {
    constructor(document) {
        super(document);

        this.trackType = 'linear';

        // key: player_id, value: car DOM element
        this.cars = {};

        // key: car.color (car class), value: marker shape name
        this.classShapes = new Map();

        // Original track geometry received from the backend.
        this.sourceTrack = null;
        this.trackId = null;

        // Active geometry used for rendering and car positioning.
        this.track = null;

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

        this.renderCars(data.cars, data.player_id, data.multiclass);
    }

    // Store original track geometry and rebuild the active layout.
    setTrack(track) {
        this.trackId = track?.id ?? null;
        this.sourceTrack = track;

        this.renderTrackLine();
    }

    // Change track type and rebuild its geometry.
    setTrackType(type) {
        if (!['linear', 'circle', 'track'].includes(type)) {
            return;
        }

        if (this.trackType === type) {
            return;
        }

        this.trackType = type;
        this.document.body.dataset.trackType = type;

        this.clearCars();
        this.renderTrackLine();
    }

    // Build geometry and render the selected track layout.
    renderTrackLine() {
        this.trackLine.replaceChildren();
        this.trackLine.classList.remove('circle', 'linear');

        this.track = this._createTrackLayout();

        if (!this.track) {
            this.trackContainer.style.aspectRatio = '';
            return;
        }

        const { viewBox } = this.track;

        // The track type fills the window and centers the map itself;
        // the synthetic layouts size the container by their aspect ratio.
        this.trackContainer.style.aspectRatio =
            this.trackType === 'track'
                ? ''
                : `${viewBox[2]} / ${viewBox[3]}`;

        this.trackLine.classList.add(this.trackType);

        this.renderSvgTrack();
    }

    // Create geometry for the selected track type.
    _createTrackLayout() {
        if (this.trackType === 'track') {
            return this._createSourceTrack();
        }

        if (this.trackType === 'circle') {
            return this._createCircleTrack();
        }

        if (this.trackType === 'linear') {
            return this._createLinearTrack();
        }

        return null;
    }

    // Create a track from the geometry received from the backend.
    _createSourceTrack() {
        const source = this.sourceTrack;

        if (!source || source.points?.length < 2) {
            return null;
        }

        const path = new TrackPath(source.points);

        if (path.length <= 0) {
            return null;
        }

        return {
            viewBox:
                getPointsViewBox(source.points) ??
                source.view_box,
            path,
            startFinish: source.start_finish,
            startFinishCellSize: 16,
            lapSpan: 1,
        };
    }

    // Create a circular track using the same TrackPath pipeline.
    _createCircleTrack() {
        const [minX, minY, width, height] = CIRCLE_VIEW_BOX;

        const cx = minX + width / 2;
        const cy = minY + height / 2;

        const points = Array.from(
            { length: CIRCLE_SEGMENTS + 1 },
            (_, index) => {
                const angle =
                    Math.PI / 2 -
                    (index / CIRCLE_SEGMENTS) * Math.PI * 2;

                return [
                    cx + CIRCLE_RADIUS * Math.cos(angle),
                    cy + CIRCLE_RADIUS * Math.sin(angle),
                ];
            }
        );

        return {
            viewBox: CIRCLE_VIEW_BOX,
            path: new TrackPath(points),
            startFinish: {
                pct: 0,
                direction: 1,
            },
            startFinishCellSize: 1,
            lapSpan: 1,
        };
    }

    // Create a horizontal track using the same TrackPath pipeline.
    _createLinearTrack() {
        return {
            viewBox: LINEAR_VIEW_BOX,
            path: new TrackPath(LINEAR_POINTS),
            startFinish: {
                pct: 0,
                direction: 1,
            },
            startFinishCellSize: 3,
            // TrackPath closes the loop (there and back), so a lap
            // uses only its forward half: left end -> right end.
            lapSpan: 0.5,
        };
    }

    // Draw track geometry using SVG.
    renderSvgTrack() {
        const { viewBox, path } = this.track;

        const svg = this._createSvgElement('svg', {
            viewBox: viewBox.join(' '),
            preserveAspectRatio: 'xMidYMid meet',
            'aria-hidden': 'true',
            focusable: 'false',
        });

        const pathData = path.toSvgPathData();

        // Draw the white outline first, then the dark track surface.
        for (const layer of ['outer', 'surface']) {
            const trackPath = this._createSvgElement('path', {
                class: `track ${layer}`,
                d: pathData,
            });

            svg.appendChild(trackPath);
        }

        svg.appendChild(this._createStartFinishLine());

        this.trackLine.appendChild(svg);
    }

    // Draw the start/finish line across the track.
    _createStartFinishLine() {
        const { x, y, dx, dy } =
            this.track.path.pointAt(this.track.startFinish.pct);

        const angle = Math.atan2(dy, dx) * 180 / Math.PI;

        // Local coordinates: one cell is 1x1, the grid is 2 cells along
        // the track and 5 cells across it, centered on the origin.
        const group = this._createSvgElement('g', {
            class: 'track-start-finish',
            transform:
                `translate(${x} ${y}) rotate(${angle}) ` +
                `scale(${this.track.startFinishCellSize}) ` +
                `translate(${-START_FINISH_COLS / 2} ${-START_FINISH_ROWS / 2})`,
        });

        for (let row = 0; row < START_FINISH_ROWS; row++) {
            for (let col = 0; col < START_FINISH_COLS; col++) {
                group.appendChild(this._createSvgElement('rect', {
                    x: col,
                    y: row,
                    width: 1,
                    height: 1,
                    fill: (row + col) % 2 === 0 ? '#ff3333' : '#ffffff',
                }));
            }
        }

        return group;
    }

    // Create an SVG element with the specified attributes.
    _createSvgElement(tag, attributes) {
        const element = this.document.createElementNS(SVG_NS, tag);

        for (const [name, value] of Object.entries(attributes)) {
            element.setAttribute(name, value);
        }

        return element;
    }

    // Remove all existing car elements.
    clearCars() {
        Object.values(this.cars).forEach(car => car.remove());
        this.cars = {};
        this.classShapes.clear();
    }

    // Render all cars received from the API.
    renderCars(cars, playerId, isMulticlass) {
        if (!this.track) {
            this.clearCars();
            return;
        }

        for (const car of cars ?? []) {
            if (this._isCarInactiveAndRemove(car)) {
                continue;
            }

            let carDiv = this.cars[car.player_id];

            if (!carDiv) {
                carDiv = this.createCarDiv(car);
            }

            this.updateCarAppearance(carDiv, car, playerId, isMulticlass);
            this.updateCarPosition(carDiv, car.lap_dist_pct);
        }
    }

    // Remove cars that are no longer on the track.
    _isCarInactiveAndRemove(car) {
        if (car.lap_dist_pct === -1) {
            const carDiv = this.cars[car.player_id];

            if (carDiv) {
                carDiv.remove();
                delete this.cars[car.player_id];
            }

            return true;
        }

        return false;
    }

    // Create a new car DOM element.
    createCarDiv(car) {
        const carDiv = this.document.createElement('div');

        carDiv.classList.add('track-map-car');

        // The shape layer is separate from the number, so clipping the
        // marker does not clip the text or the player indicator.
        const shape = this.document.createElement('span');
        shape.classList.add('track-map-car-shape');

        carDiv.append(shape, String(car.car_number));

        this.trackContainer.appendChild(carDiv);
        this.cars[car.player_id] = carDiv;

        return carDiv;
    }

    // Update the car's visual appearance based on session type and player identity.
    updateCarAppearance(carDiv, car, playerId, isMulticlass) {
        carDiv.classList.toggle('player', car.player_id === playerId);

        carDiv.style.setProperty(
            '--car-color',
            isMulticlass ? car.color : 'var(--yellow-primary)'
        );

        carDiv.dataset.shape = this._getCarShape(car.color, isMulticlass);
    }

    // Shape of a car class: the same color always gets the same shape.
    _getCarShape(color, isMulticlass) {
        if (!isMulticlass) {
            return CAR_SHAPES[0];
        }

        if (!this.classShapes.has(color)) {
            this.classShapes.set(
                color,
                CAR_SHAPES[this.classShapes.size % CAR_SHAPES.length]
            );
        }

        return this.classShapes.get(color);
    }

    // Update car position using the active track geometry.
    updateCarPosition(carDiv, lapDistPct) {
        if (!Number.isFinite(lapDistPct) || !this.track) {
            return;
        }

        const { path, startFinish, lapSpan } = this.track;

        const point = path.pointAt(
            startFinish.pct + startFinish.direction * lapDistPct * lapSpan
        );

        const { x, y } = this._trackToContainer(point);

        this._applyCarTransition(carDiv, lapDistPct, x, y);
    }

    // Convert SVG viewBox coordinates into container pixels.
    _trackToContainer({ x, y }) {
        const cr = this.trackContainer.getBoundingClientRect();

        const [minX, minY, width, height] = this.track.viewBox;

        const scale = Math.min(
            cr.width / width,
            cr.height / height
        );

        return {
            x: (x - minX) * scale + (cr.width - width * scale) / 2,
            y: (y - minY) * scale + (cr.height - height * scale) / 2,
        };
    }

    // Apply smooth movement using GPU-friendly transforms.
    _applyCarTransition(carDiv, lapDistPct, x, y) {
        const lastPct = Number(carDiv.dataset.lastLapPct);

        // First positioning: place the car immediately without animation.
        const isFirstPosition = !Number.isFinite(lastPct);

        // Suppress animation when the car crosses the start/finish line.
        const crossedLapBoundary =
            !isFirstPosition &&
            Math.abs(lastPct - lapDistPct) > 0.5;

        carDiv.style.transition =
            isFirstPosition || crossedLapBoundary
                ? 'none'
                : CAR_TRANSITION;

        carDiv.style.transform =
            `translate3d(${x}px, ${y}px, 0) translate(-50%, -50%)`;

        carDiv.dataset.lastLapPct = lapDistPct;
    }
}

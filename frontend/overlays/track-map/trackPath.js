// Closed track loop measured by arc length.
// Lap fractions are distances along the lap, while the track points are not
// evenly spaced, so positions are interpolated by length, not by point index.
export class TrackPath {
    constructor(points) {
        // Close the loop unless the last point already repeats the first one.
        const [first] = points;
        const last = points[points.length - 1];
        const isClosed = first[0] === last[0] && first[1] === last[1];
        this.vertices = isClosed ? points : [...points, first];

        // offsets[i]: length of the loop from the first vertex to vertex i.
        this.offsets = [0];
        for (let i = 1; i < this.vertices.length; i++) {
            const [x0, y0] = this.vertices[i - 1];
            const [x1, y1] = this.vertices[i];
            this.offsets.push(this.offsets[i - 1] + Math.hypot(x1 - x0, y1 - y0));
        }
        this.length = this.offsets[this.offsets.length - 1];
    }

    // Point at a lap fraction (wrapped into [0, 1)), with the unit
    // direction (dx, dy) of the loop at that point.
    pointAt(fraction) {
        const target = (((fraction % 1) + 1) % 1) * this.length;

        // Last vertex whose offset is <= target; its segment has a positive length.
        let low = 0;
        let high = this.offsets.length - 2;
        while (low < high) {
            const mid = Math.ceil((low + high) / 2);
            if (this.offsets[mid] <= target) low = mid;
            else high = mid - 1;
        }

        const [x0, y0] = this.vertices[low];
        const [x1, y1] = this.vertices[low + 1];
        const segmentLength = this.offsets[low + 1] - this.offsets[low];
        const t = segmentLength > 0 ? (target - this.offsets[low]) / segmentLength : 0;
        return {
            x: x0 + (x1 - x0) * t,
            y: y0 + (y1 - y0) * t,
            dx: segmentLength > 0 ? (x1 - x0) / segmentLength : 1,
            dy: segmentLength > 0 ? (y1 - y0) / segmentLength : 0,
        };
    }

    // SVG path data drawing the closed loop.
    toSvgPathData() {
        const [[x, y], ...rest] = this.vertices;
        return `M${x},${y}${rest.map(([px, py]) => `L${px},${py}`).join('')}Z`;
    }
}

const test = require('node:test');
const assert = require('node:assert/strict');

const TRACK_PATH = '../../../frontend/overlays/track-map/trackPath.js';

test('TrackPath closes the loop once', async () => {
  const { TrackPath } = await import(TRACK_PATH);
  const open = new TrackPath([[0, 0], [10, 0], [10, 5]]);
  const closed = new TrackPath([[0, 0], [10, 0], [10, 5], [0, 0]]);

  // The first point is repeated at the end only when missing.
  assert.equal(open.toSvgPathData(), 'M0,0L10,0L10,5L0,0Z');
  assert.equal(closed.toSvgPathData(), open.toSvgPathData());
  assert.equal(open.length, closed.length);
});

test('TrackPath finds points by distance, not by point index', async () => {
  const { TrackPath } = await import(TRACK_PATH);
  // Uneven spacing: a 1-unit and a 9-unit segment, then back (20 in total).
  const path = new TrackPath([[0, 0], [1, 0], [10, 0]]);

  assert.equal(path.length, 20);
  assert.deepEqual(path.pointAt(0.25), { x: 5, y: 0, dx: 1, dy: 0 });
});

test('TrackPath wraps lap fractions outside [0, 1)', async () => {
  const { TrackPath } = await import(TRACK_PATH);
  const path = new TrackPath([[0, 0], [10, 0]]);

  assert.deepEqual(path.pointAt(1.25), path.pointAt(0.25));
  // A negative fraction lands on the way back, moving in reverse.
  assert.deepEqual(path.pointAt(-0.25), { x: 5, y: 0, dx: -1, dy: 0 });
});

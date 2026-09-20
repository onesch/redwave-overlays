const test = require('node:test');
const assert = require('node:assert/strict');

const LastLapTime = require('../../frontend/static/js/last_lap_time');

test('formats a lap in every supported display format', () => {
  assert.equal(LastLapTime.format(83.456, 'MM:SS.sss'), '01:23.456');
  assert.equal(LastLapTime.format(83.456, 'MM:SS.ss'), '01:23.45');
  assert.equal(LastLapTime.format(83.331, 'SS.sss'), '23.331');
  assert.equal(LastLapTime.format(83.331, 'SS.ss'), '23.33');
});

test('seconds-only formats drop complete minutes', () => {
  assert.equal(LastLapTime.format(143.009, 'SS.sss'), '23.009');
});

test('empty placeholders match their selected formats', () => {
  assert.equal(LastLapTime.format(-1, 'MM:SS.sss'), '--:--.---');
  assert.equal(LastLapTime.format(null, 'MM:SS.ss'), '--:--.--');
  assert.equal(LastLapTime.format(0, 'SS.sss'), '--.---');
  assert.equal(LastLapTime.format(undefined, 'SS.ss'), '--.--');
});

test('unknown formats fall back to the default', () => {
  assert.equal(LastLapTime.normalizeFormat('invalid'), LastLapTime.DEFAULT_FORMAT);
  assert.equal(LastLapTime.format(83.456, 'invalid'), '01:23.456');
});

test('provides balanced driver and time column widths for every format', () => {
  assert.deepEqual(
    LastLapTime.columnWidths('MM:SS.sss'),
    { driver: '105px', time: '80px' },
  );
  assert.deepEqual(
    LastLapTime.columnWidths('MM:SS.ss'),
    { driver: '115px', time: '70px' },
  );
  assert.deepEqual(
    LastLapTime.columnWidths('SS.sss'),
    { driver: '130px', time: '55px' },
  );
  assert.deepEqual(
    LastLapTime.columnWidths('SS.ss'),
    { driver: '140px', time: '45px' },
  );

  for (const widths of Object.values(LastLapTime.COLUMN_WIDTHS)) {
    assert.equal(parseInt(widths.driver) + parseInt(widths.time), 185);
  }
});

test('provides a header label appropriate for each format width', () => {
  assert.equal(LastLapTime.headerLabel('MM:SS.sss'), 'Last Lap');
  assert.equal(LastLapTime.headerLabel('MM:SS.ss'), 'Last Lap');
  assert.equal(LastLapTime.headerLabel('SS.sss'), 'Last Lp');
  assert.equal(LastLapTime.headerLabel('SS.ss'), 'Last L');
});

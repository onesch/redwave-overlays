const test = require('node:test');
const assert = require('node:assert/strict');

const { describeApiContract } = require('../helpers/api_contract');

const LEADERBOARD_API = '../../../frontend/overlays/leaderboard/leaderboardApi.js';
const LEADERBOARD_UPDATER = '../../../frontend/overlays/leaderboard/leaderboardUpdater.js';
const LAST_LAP_TIME = '../../../frontend/overlays/leaderboard/lastLapTime.js';
const BASE_UPDATER = '../../../frontend/overlays/shared/baseUpdater.js';

describeApiContract({
  title: 'LeaderboardApi',
  loadApi: async () => (await import(LEADERBOARD_API)).LeaderboardApi,
  method: 'getLeaderboard',
  endpoint: '/api/leaderboard',
});

test('LeaderboardUpdater delegates loading and Last Lap format settings', async () => {
  const { BaseUpdater } = await import(BASE_UPDATER);
  const { LeaderboardUpdater } = await import(LEADERBOARD_UPDATER);
  const dto = { status: 'ok' };
  const formats = [];
  let formatListener;

  const updater = new LeaderboardUpdater(
    { getLeaderboard: async () => dto },
    { setLastLapFormat: (format) => formats.push(format) },
    {
      electronAPI: {
        getLastLapFormat: async () => 'SS.sss',
        onLastLapFormatUpdate: (listener) => { formatListener = listener; },
      },
    },
  );

  assert.ok(updater instanceof BaseUpdater);
  assert.equal(await updater.getDto(), dto);

  await updater.initFeature();
  formatListener('MM:SS.ss');
  assert.deepEqual(formats, ['SS.sss', 'MM:SS.ss']);
});

test('LastLapTime render in every supported format', async () => {
  const LastLapTime = await import(LAST_LAP_TIME);

  assert.equal(LastLapTime.format(83.456, 'MM:SS.sss'), '01:23.456');
  assert.equal(LastLapTime.format(83.456, 'MM:SS.ss'), '01:23.45');
  assert.equal(LastLapTime.format(83.331, 'SS.sss'), '23.331');
  // Seconds-only formats drop the completed minutes.
  assert.equal(LastLapTime.format(143.009, 'SS.ss'), '23.00');

  // Missing or zero lap times render as the placeholder of the format.
  assert.equal(LastLapTime.format(-1, 'MM:SS.sss'), '--:--.---');
  assert.equal(LastLapTime.format(null, 'SS.ss'), '--.--');
  assert.equal(LastLapTime.format(0, 'SS.sss'), '--.---');
  assert.equal(LastLapTime.placeholder('MM:SS.ss'), '--:--.--');
});

test('LastLapTime formats fall back to the default and every format stays complete', async () => {
  const LastLapTime = await import(LAST_LAP_TIME);

  assert.equal(LastLapTime.normalizeFormat('invalid'), LastLapTime.DEFAULT_FORMAT);
  assert.equal(LastLapTime.format(83.456, 'invalid'), '01:23.456');

  // The renderer reads a header label and column widths per format.
  for (const format of LastLapTime.FORMATS) {
    assert.ok(LastLapTime.headerLabel(format), `no header label for ${format}`);
    assert.deepEqual(
      Object.keys(LastLapTime.columnWidths(format)).sort(),
      ['driver', 'time'],
      `incomplete column widths for ${format}`,
    );
  }
});

test('LastLapTime provides balanced driver and time column widths for every format', async () => {
  const LastLapTime = await import(LAST_LAP_TIME);

  assert.deepEqual(LastLapTime.columnWidths('MM:SS.sss'), { driver: '105px', time: '80px' });
  assert.deepEqual(LastLapTime.columnWidths('MM:SS.ss'), { driver: '115px', time: '70px' });
  assert.deepEqual(LastLapTime.columnWidths('SS.sss'), { driver: '130px', time: '55px' });
  assert.deepEqual(LastLapTime.columnWidths('SS.ss'), { driver: '140px', time: '45px' });

  for (const widths of Object.values(LastLapTime.COLUMN_WIDTHS)) {
    assert.equal(parseInt(widths.driver) + parseInt(widths.time), 185);
  }
});

test('LastLapTime provides a header label appropriate for each format width', async () => {
  const LastLapTime = await import(LAST_LAP_TIME);

  assert.equal(LastLapTime.headerLabel('MM:SS.sss'), 'Last Lap');
  assert.equal(LastLapTime.headerLabel('MM:SS.ss'), 'Last Lap');
  assert.equal(LastLapTime.headerLabel('SS.sss'), 'Last Lp');
  assert.equal(LastLapTime.headerLabel('SS.ss'), 'Last L');
});

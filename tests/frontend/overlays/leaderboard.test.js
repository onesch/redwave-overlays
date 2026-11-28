const test = require('node:test');
const assert = require('node:assert/strict');

const { describeApiContract } = require('../helpers/api_contract');
const { BASE_UPDATER } = require('../helpers/modules');

const LEADERBOARD_API = '../../../frontend/overlays/leaderboard/leaderboardApi.js';
const LEADERBOARD_UPDATER = '../../../frontend/overlays/leaderboard/leaderboardUpdater.js';
const LAST_LAP_TIME = '../../../frontend/overlays/leaderboard/lastLapTime.js';
const LEADERBOARD_RENDERER = '../../../frontend/overlays/leaderboard/leaderboardRenderer.js';

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

test('LeaderboardRenderer places the closest neighbors right next to the player row', async () => {
  const { FakeDocument } = require('../helpers/dom');
  const { LeaderboardRenderer } = await import(LEADERBOARD_RENDERER);

  // Row slots are placed by the CSS grid, not by markup order: ahead-row-1
  // (.s-3) and behind-row-1 (.s1) sit right above and below the player row.
  const rowIds = [1, 2, 3].flatMap((i) => [`ahead-row-${i}`, `behind-row-${i}`]);
  const document = new FakeDocument(Object.fromEntries(rowIds.map((id) => [id, 'row'])));
  const renderer = new LeaderboardRenderer(document);

  const rendered = {};
  renderer.renderCar = (rowId, car) => { rendered[rowId] = car.name; };
  renderer.renderPlayer = () => {};
  renderer.updateSessionLapTime = () => {};
  renderer.updateStrengthOfField = () => {};
  renderer.updateSessionTime = () => {};

  const render = (ahead, behind) => {
    Object.keys(rendered).forEach((key) => delete rendered[key]);
    renderer.render({
      player: { laps_started: 0 },
      neighbors: { ahead, behind },
      leaderboard_data: {},
    });
    return { ...rendered };
  };

  // The backend sends both neighbor lists closest first.
  assert.deepEqual(
    render(
      [{ name: 'ahead_1' }, { name: 'ahead_2' }, { name: 'ahead_3' }],
      [{ name: 'behind_1' }, { name: 'behind_2' }, { name: 'behind_3' }],
    ),
    {
      'ahead-row-1': 'ahead_1',
      'ahead-row-2': 'ahead_2',
      'ahead-row-3': 'ahead_3',
      'behind-row-1': 'behind_1',
      'behind-row-2': 'behind_2',
      'behind-row-3': 'behind_3',
    },
  );

  // With a single car ahead it stays right above the player.
  assert.deepEqual(render([{ name: 'ahead_1' }], []), { 'ahead-row-1': 'ahead_1' });
});

test('LeaderboardRenderer shows the pit label of the car as sent by the backend', async () => {
  const { FakeDocument } = require('../helpers/dom');
  const { LeaderboardRenderer } = await import(LEADERBOARD_RENDERER);

  const document = new FakeDocument();
  const renderer = new LeaderboardRenderer(document);

  const name = document.createElement('div');
  const pitFlag = document.createElement('div');
  const row = {
    querySelector: (selector) => ({ '.driver .name': name, '.driver .pit-flag': pitFlag })[selector] ?? null,
  };

  const pitFlagOf = (car) => {
    renderer.renderDriverName(row, car);
    renderer.renderPitFlag(row, car);
    return { text: pitFlag.textContent, display: pitFlag.style.display, inPit: name.classList.contains('in-pit') };
  };

  assert.deepEqual(
    pitFlagOf({ pit_label: 'IN PIT', is_in_pitroad: true }),
    { text: 'IN PIT', display: 'inline-flex', inPit: true },
  );
  assert.deepEqual(
    pitFlagOf({ pit_label: 'L6', is_in_pitroad: false }),
    { text: 'L6', display: 'inline-flex', inPit: false },
  );
  // No pit stop: the flag is hidden.
  assert.equal(pitFlagOf({ pit_label: null, is_in_pitroad: false }).display, 'none');
});

test('LeaderboardRenderer colors the gap by the lap flags of the car', async () => {
  const { FakeDocument } = require('../helpers/dom');
  const { LeaderboardRenderer } = await import(LEADERBOARD_RENDERER);

  const document = new FakeDocument();
  const renderer = new LeaderboardRenderer(document);
  renderer.updateLapTime = () => {};
  renderer.updateGap = () => {};

  const gap = document.createElement('div');
  const row = { querySelector: (selector) => (selector === '.gap' ? gap : null) };

  const gapClasses = (car) => {
    renderer.renderGapAndLap(row, car);
    return [...gap.classList.names].sort();
  };

  assert.deepEqual(gapClasses({ is_lap_ahead: true, is_lap_behind: false }), ['ahead_lap', 'gap']);
  assert.deepEqual(gapClasses({ is_lap_ahead: false, is_lap_behind: true }), ['behind_lap', 'gap']);
  // The same lap: the classes of the previous render are cleared.
  assert.deepEqual(gapClasses({ is_lap_ahead: false, is_lap_behind: false }), ['gap']);
  // A car in the pits keeps its lap color.
  assert.deepEqual(
    gapClasses({ is_lap_ahead: true, is_lap_behind: false, is_in_pitroad: true }),
    ['ahead_lap', 'gap', 'in-pit'],
  );
});

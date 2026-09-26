const test = require('node:test');
const assert = require('node:assert/strict');

test('LeaderboardApi uses its default endpoint and returns parsed data', async () => {
  const { LeaderboardApi } = await import(
    '../../../frontend/overlays/leaderboard/leaderboardApi.js'
  );
  const dto = { status: 'ok', neighbors: {} };
  let requestedEndpoint;
  const api = new LeaderboardApi(undefined, async (endpoint) => {
    requestedEndpoint = endpoint;
    return { ok: true, json: async () => dto };
  });

  assert.equal(await api.getLeaderboard(), dto);
  assert.equal(requestedEndpoint, '/api/leaderboard');
});

test('LeaderboardApi rejects non-success responses', async () => {
  const { LeaderboardApi } = await import(
    '../../../frontend/overlays/leaderboard/leaderboardApi.js'
  );
  const api = new LeaderboardApi('/api/leaderboard', async () => ({
    ok: false,
    status: 500,
  }));

  await assert.rejects(api.getLeaderboard(), /Failed to fetch leaderboard: 500/);
});

test('LeaderboardUpdater delegates loading and Last Lap format settings', async () => {
  const { BaseUpdater } = await import('../../../frontend/overlays/shared/baseUpdater.js');
  const { LeaderboardUpdater } = await import(
    '../../../frontend/overlays/leaderboard/leaderboardUpdater.js'
  );
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

test('feature Last Lap helpers format values and visual metadata', async () => {
  const LastLapTime = await import(
    '../../../frontend/overlays/leaderboard/lastLapTime.js'
  );

  assert.equal(LastLapTime.format(83.456, 'MM:SS.sss'), '01:23.456');
  assert.equal(LastLapTime.format(83.456, 'SS.ss'), '23.45');
  assert.equal(LastLapTime.placeholder('SS.sss'), '--.---');
  assert.deepEqual(LastLapTime.columnWidths('MM:SS.ss'), {
    driver: '115px',
    time: '70px',
  });
  assert.equal(LastLapTime.headerLabel('SS.ss'), 'Last L');
});

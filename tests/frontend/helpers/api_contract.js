const test = require('node:test');
const assert = require('node:assert/strict');

// Shared contract of the overlay API clients
function describeApiContract({ title, loadApi, method, endpoint }) {
  test(`${title} requests ${endpoint} and returns the parsed DTO`, async () => {
    const Api = await loadApi();
    const dto = { status: 'ok' };
    const requested = [];
    const api = new Api(undefined, async (url) => {
      requested.push(url);
      return { ok: true, json: async () => dto };
    });

    assert.equal(await api[method](), dto);
    assert.deepEqual(requested, [endpoint]);
  });

  test(`${title} rejects non-success responses`, async () => {
    const Api = await loadApi();
    const api = new Api(endpoint, async () => ({ ok: false, status: 503 }));

    await assert.rejects(api[method](), /Failed to fetch .+: 503/);
  });
}

module.exports = { describeApiContract };

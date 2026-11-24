const test = require('node:test');
const assert = require('node:assert/strict');

const COLORS = '../../../../frontend/overlays/shared/colors.js';

test('isDarkColor tells dark colors from light ones', async () => {
  const { isDarkColor } = await import(COLORS);

  assert.equal(isDarkColor('#000080'), true); // navy
  assert.equal(isDarkColor('#008000'), true); // green
  assert.equal(isDarkColor('#ff0000'), false); // red: dark text still reads better
  assert.equal(isDarkColor('#ffda59'), false); // yellow
});

test('isDarkColor treats a missing or malformed color as light', async () => {
  const { isDarkColor } = await import(COLORS);

  assert.equal(isDarkColor(null), false);
  assert.equal(isDarkColor('not a color'), false);
});

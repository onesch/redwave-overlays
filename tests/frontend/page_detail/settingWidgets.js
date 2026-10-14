const test = require('node:test');
const assert = require('node:assert/strict');

const { FakeDocument } = require('../helpers/dom');

const SETTING_WIDGETS = '../../../frontend/static/js/page_detail/settingWidgets.js';

const activeIds = (document, ids) =>
  ids.filter((id) => document.getElementById(id).classList.contains('active'));

function createZoomFields() {
  const document = new FakeDocument({ zoomRange: '', zoomValue: '' });
  const input = document.getElementById('zoomRange');
  const label = document.getElementById('zoomValue');
  return { document, input, label };
}

test('slider field renders a loaded value and reports user input', async () => {
  const { createSliderField } = await import(SETTING_WIDGETS);
  const { input, label } = createZoomFields();
  const field = createSliderField({ input, label, format: (value) => `${value}%` });

  assert.equal(field.setFromLoad(120), true);
  assert.equal(input.value, '120');
  assert.equal(label.textContent, '120%');

  const changes = [];
  field.onInput((value) => changes.push(value));
  input.setValue('150');

  assert.deepEqual(changes, ['150']);
  assert.equal(label.textContent, '150%');
});

test('slider field keeps a late load reply from overwriting user input', async () => {
  const { createSliderField } = await import(SETTING_WIDGETS);
  const { input, label } = createZoomFields();
  const field = createSliderField({ input, label, format: (value) => `${value}%` });
  field.onInput(() => {});

  input.setValue('80');

  assert.equal(field.setFromLoad(100), false);
  assert.equal(input.value, '80');
  assert.equal(label.textContent, '80%');
});

test('button group highlights one value and stops reacting to loads after a click', async () => {
  const { createButtonGroup } = await import(SETTING_WIDGETS);
  const document = new FakeDocument({ hideBtn: '', dimBtn: '', showBtn: '' });
  const ids = ['hideBtn', 'dimBtn', 'showBtn'];
  const group = createButtonGroup({
    buttons: {
      hide: document.getElementById('hideBtn'),
      dim: document.getElementById('dimBtn'),
      show: document.getElementById('showBtn'),
    },
  });

  group.select('dim');
  assert.deepEqual(activeIds(document, ids), ['dimBtn']);

  const selected = [];
  group.onSelect((value) => selected.push(value));
  document.getElementById('showBtn').click();

  assert.deepEqual(selected, ['show']);
  // A load reply arriving after the click must not flip the highlight.
  assert.equal(group.setFromLoad('hide'), false);
  assert.deepEqual(activeIds(document, ids), ['dimBtn']);
});

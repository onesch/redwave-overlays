const test = require('node:test');
const assert = require('node:assert/strict');

const { FakeDocument } = require('../../helpers/dom');

const DRAG_MODE_BORDER = '../../../../frontend/overlays/shared/dragModeBorder.js';

test('Drag mode border follows the shared overlay movement state', async () => {
  const { watchDragModeBorder, DRAG_MODE_CLASS } = await import(DRAG_MODE_BORDER);
  const document = new FakeDocument();
  let movementListener;

  await watchDragModeBorder(document, {
    electronAPI: {
      getOverlayMovementState: async () => true,
      onOverlayMovementStateUpdate: (listener) => {
        movementListener = listener;
      },
    },
  });

  assert.equal(document.body.classList.contains(DRAG_MODE_CLASS), true);

  movementListener(false);
  assert.equal(document.body.classList.contains(DRAG_MODE_CLASS), false);

  movementListener(true);
  assert.equal(document.body.classList.contains(DRAG_MODE_CLASS), true);
});

test('Drag mode border stays hidden without a movement state to follow', async () => {
  const { watchDragModeBorder, DRAG_MODE_CLASS } = await import(DRAG_MODE_BORDER);

  for (const electronAPI of [
    {},
    { getOverlayMovementState: async () => false },
  ]) {
    const document = new FakeDocument();

    await assert.doesNotReject(
      watchDragModeBorder(document, { electronAPI }),
    );

    assert.equal(document.body.classList.contains(DRAG_MODE_CLASS), false);
  }
});

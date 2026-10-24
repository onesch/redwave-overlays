// Border drawn around an overlay window while the global overlay movement
// mode is enabled, so draggable and locked overlays can be told apart.
// The border itself is styled in the shared overlay stylesheet.

// Body class that reveals the drag-mode border.
const DRAG_MODE_CLASS = 'overlay-drag-mode';

// Show or hide the drag-mode border on the given overlay document.
export function applyDragModeBorder(overlayDocument, isMovementEnabled) {
    overlayDocument.body.classList.toggle(
        DRAG_MODE_CLASS,
        Boolean(isMovementEnabled),
    );
}

// Follow the shared movement state, including the state the overlay opened in.
export async function watchDragModeBorder(overlayDocument, {
    electronAPI = globalThis.window?.electronAPI,
} = {}) {
    if (!electronAPI) return;

    // The main process broadcasts every movement mode change to all windows.
    electronAPI.onOverlayMovementStateUpdate?.((isMovementEnabled) => {
        applyDragModeBorder(overlayDocument, isMovementEnabled);
    });

    applyDragModeBorder(
        overlayDocument,
        await electronAPI.getOverlayMovementState?.(),
    );
}

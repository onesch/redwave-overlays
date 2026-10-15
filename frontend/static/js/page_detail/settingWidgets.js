// Reusable DOM/UI primitives for the overlay settings in detail pages.
// They own how controls render; features own what the values mean.
//
// Both controls track user interaction so that `setFromLoad` can ignore
// a late initial-load response: the IPC get is started at mount, so its
// reply can arrive after the user already changed the control, and it
// must never overwrite the newer input.

// Slider input paired with a formatted value label.
export function createSliderField({ input, label, format = (value) => `${value}` }) {
  let interacted = false;

  const set = (value) => {
    if (input) input.value = value;
    if (label) label.textContent = format(value);
  };

  return {
    // Apply a value coming from the initial load. Returns false and
    // does nothing once the user has interacted with the control.
    setFromLoad(value) {
      if (interacted) return false;
      set(value);
      return true;
    },
    // Notify on user input; the label tracks the raw slider value first.
    onInput(handler) {
      if (!input) return;
      input.addEventListener('input', () => {
        interacted = true;
        if (label) label.textContent = format(input.value);
        handler(input.value);
      });
    },
  };
}

// Group of buttons where exactly one value is marked active.
export function createButtonGroup({ buttons }) {
  let interacted = false;

  const select = (value) => {
    Object.entries(buttons).forEach(([key, button]) => {
      button?.classList.toggle('active', key === value);
    });
  };

  return {
    // Highlight the button matching the value (all others inactive).
    select,
    // Apply a value coming from the initial load. Returns false and
    // does nothing once the user has clicked any button.
    setFromLoad(value) {
      if (interacted) return false;
      select(value);
      return true;
    },
    // Notify with the value of the clicked button.
    onSelect(handler) {
      Object.entries(buttons).forEach(([key, button]) => {
        button?.addEventListener('click', () => {
          interacted = true;
          handler(key);
        });
      });
    },
  };
}

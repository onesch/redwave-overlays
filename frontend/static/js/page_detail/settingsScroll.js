const CONTAINER_SELECTOR = '.settings-container';
const FIELD_SELECTOR = ':scope > .setting-container, :scope > .range-container';
const MAX_VISIBLE_FIELDS = 5;

// Sizes `.settings-container` to fit at most `MAX_VISIBLE_FIELDS` fields and
// steps one field per wheel tick when additional fields overflow.
export function createSettingsScroll({
  document = globalThis.document,
  window = globalThis.window,
} = {}) {
  const getStyle =
    window?.getComputedStyle?.bind(window)
    ?? globalThis.getComputedStyle
    ?? ((element) => element?.style ?? {});
  const requestFrame =
    window?.requestAnimationFrame?.bind(window)
    ?? globalThis.requestAnimationFrame
    ?? ((callback) => callback());
  const Observer = window?.ResizeObserver ?? globalThis.ResizeObserver;

  return {
    mount() {
      const container = document?.querySelector?.(CONTAINER_SELECTOR);
      if (!container) return;

      let isScrolling = false;

      const getFields = () => [...container.querySelectorAll(FIELD_SELECTOR)];

      const updateSettingsScroll = () => {
        const fields = getFields();
        const visibleFields = fields.slice(0, MAX_VISIBLE_FIELDS);

        const style = getStyle(container);
        const paddingTop = parseFloat(style?.paddingTop) || 0;

        const visibleHeight = visibleFields.reduce((height, field) => {
          const fieldStyle = getStyle(field);
          const marginBottom = parseFloat(fieldStyle?.marginBottom) || 0;

          return height + field.getBoundingClientRect().height + marginBottom;
        }, paddingTop);

        container.style.height = `${visibleHeight}px`;
        container.style.overflowY =
          fields.length > MAX_VISIBLE_FIELDS ? 'auto' : 'hidden';
      };

      container.addEventListener(
        'wheel',
        (event) => {
          const fields = getFields();

          if (
            fields.length <= MAX_VISIBLE_FIELDS
            || event.deltaY === 0
            || isScrolling
          ) {
            return;
          }

          event.preventDefault();

          const currentScroll = container.scrollTop;
          const containerTop = container.getBoundingClientRect().top;
          const currentIndex = fields.findIndex(
            (field) => field.getBoundingClientRect().top >= containerTop - 2,
          );

          const index = currentIndex === -1 ? fields.length - 1 : currentIndex;
          const nextIndex = Math.max(
            0,
            Math.min(fields.length - 1, index + (event.deltaY > 0 ? 1 : -1)),
          );

          const targetScroll =
            currentScroll
            + fields[nextIndex].getBoundingClientRect().top
            - containerTop;

          isScrolling = true;

          container.scrollTo({
            top: targetScroll,
            behavior: 'auto',
          });

          requestFrame(() => {
            isScrolling = false;
          });
        },
        { passive: false },
      );

      updateSettingsScroll();

      if (Observer) {
        const observer = new Observer(updateSettingsScroll);
        getFields().forEach((field) => observer.observe(field));
        observer.observe(container);
      }
    },
  };
}

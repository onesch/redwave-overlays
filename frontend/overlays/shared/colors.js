// Relative luminance at which dark text (#130A06, --car-text-color) and white
// text (--car-text-light-color) give the same contrast ratio on a color:
// darker colors need white text.
const DARK_COLOR_LUMINANCE = 0.19;

// sRGB channel (0-255) to linear light, as defined by WCAG.
function toLinear(channel) {
    const c = channel / 255;
    return c <= 0.04045 ? c / 12.92 : ((c + 0.055) / 1.055) ** 2.4;
}

// Check if a '#rrggbb' color is dark, by its WCAG relative luminance.
// Returns false for a missing or malformed color.
export function isDarkColor(hex) {
    const rgb = parseInt(String(hex ?? '').slice(1), 16);

    if (Number.isNaN(rgb)) {
        return false;
    }

    const luminance =
        0.2126 * toLinear((rgb >> 16) & 0xff) +
        0.7152 * toLinear((rgb >> 8) & 0xff) +
        0.0722 * toLinear(rgb & 0xff);

    return luminance < DARK_COLOR_LUMINANCE;
}

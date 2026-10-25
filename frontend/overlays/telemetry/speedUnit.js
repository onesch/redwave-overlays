// Telemetry speeds arrive from the backend in meters per second (m/s).
// Every speed readout shares the conversion and label logic below so the
// main, TOP and EXIT values can never disagree about the selected unit.
export const DEFAULT_SPEED_UNIT = 'kmh';
export const SPEED_UNITS = new Set([DEFAULT_SPEED_UNIT, 'mph']);

export const MS_TO_KMH = 3.6;
export const KMH_TO_MPH = 0.621371;
export const MS_TO_MPH = MS_TO_KMH * KMH_TO_MPH;

const SPEED_UNIT_LABELS = Object.freeze({
  kmh: 'KM/H',
  mph: 'MPH',
});

export function normalizeSpeedUnit(value) {
  return value === 'mph' ? 'mph' : DEFAULT_SPEED_UNIT;
}

export function speedUnitLabel(unit) {
  return SPEED_UNIT_LABELS[normalizeSpeedUnit(unit)];
}

// Convert a raw m/s value into the selected display unit. Non-numeric values
// are passed through unchanged so callers can render their placeholder.
export function toDisplaySpeed(speedMs, unit) {
  const speed = Number(speedMs);
  if (speedMs == null || !Number.isFinite(speed)) return speedMs;

  const factor = normalizeSpeedUnit(unit) === 'mph' ? MS_TO_MPH : MS_TO_KMH;
  return speed * factor;
}

export const convertSpeed = toDisplaySpeed;

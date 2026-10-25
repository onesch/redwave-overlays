export const DEFAULT_SPEED_UNIT = 'kmh';

// Telemetry comes from the backend in km/h; mph is derived when needed.
export const KMH_TO_MPH = 0.621371;

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

export function toDisplaySpeed(speedKm, unit) {
  if (!Number.isFinite(speedKm)) return speedKm;
  return normalizeSpeedUnit(unit) === 'mph' ? speedKm * KMH_TO_MPH : speedKm;
}

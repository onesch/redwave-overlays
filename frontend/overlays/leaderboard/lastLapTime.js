export const DEFAULT_FORMAT = 'MM:SS.sss';

export const FORMATS = Object.freeze([
  DEFAULT_FORMAT,
  'MM:SS.ss',
  'SS.sss',
  'SS.ss',
]);

export const COLUMN_WIDTHS = Object.freeze({
  'MM:SS.sss': Object.freeze({ driver: '105px', time: '80px' }),
  'MM:SS.ss': Object.freeze({ driver: '115px', time: '70px' }),
  'SS.sss': Object.freeze({ driver: '130px', time: '55px' }),
  'SS.ss': Object.freeze({ driver: '140px', time: '45px' }),
});

const PLACEHOLDERS = Object.freeze({
  'MM:SS.sss': '--:--.---',
  'MM:SS.ss': '--:--.--',
  'SS.sss': '--.---',
  'SS.ss': '--.--',
});

const HEADER_LABELS = Object.freeze({
  'MM:SS.sss': 'Last Lap',
  'MM:SS.ss': 'Last Lap',
  'SS.sss': 'Last Lp',
  'SS.ss': 'Last L',
});

export function normalizeFormat(value) {
  return FORMATS.includes(value) ? value : DEFAULT_FORMAT;
}

export function placeholder(format) {
  return PLACEHOLDERS[normalizeFormat(format)];
}

export function columnWidths(format) {
  return COLUMN_WIDTHS[normalizeFormat(format)];
}

export function headerLabel(format) {
  return HEADER_LABELS[normalizeFormat(format)];
}

export function format(value, selectedFormat) {
  const selected = normalizeFormat(selectedFormat);
  if (value === undefined || value === null || value <= 0) {
    return placeholder(selected);
  }

  const decimals = selected.endsWith('sss') ? 3 : 2;
  const milliseconds = Math.round(value * 1000) % 60000;
  const wholeSeconds = Math.floor(milliseconds / 1000);
  const fractional = decimals === 3
    ? milliseconds % 1000
    : Math.floor((milliseconds % 1000) / 10);
  const formattedSeconds = `${wholeSeconds.toString().padStart(2, '0')}.${fractional
    .toString()
    .padStart(decimals, '0')}`;

  if (selected.startsWith('SS')) {
    return formattedSeconds;
  }

  const minutes = Math.floor(value / 60).toString().padStart(2, '0');
  return `${minutes}:${formattedSeconds}`;
}

(function initLastLapTimeFormatter(root, factory) {
  const formatter = factory();

  if (typeof module === 'object' && module.exports) {
    module.exports = formatter;
  } else {
    root.LastLapTime = formatter;
  }
}(typeof globalThis !== 'undefined' ? globalThis : this, () => {
  const DEFAULT_FORMAT = 'MM:SS.sss';
  const FORMATS = new Set([DEFAULT_FORMAT, 'MM:SS.ss', 'SS.sss', 'SS.ss']);
  const COLUMN_WIDTHS = Object.freeze({
    'MM:SS.sss': Object.freeze({ driver: '105px', time: '80px' }),
    'MM:SS.ss': Object.freeze({ driver: '115px', time: '70px' }),
    'SS.sss': Object.freeze({ driver: '130px', time: '55px' }),
    'SS.ss': Object.freeze({ driver: '140px', time: '45px' }),
  });

  function normalizeFormat(format) {
    return FORMATS.has(format) ? format : DEFAULT_FORMAT;
  }

  function placeholder(format) {
    const normalized = normalizeFormat(format);
    const decimals = normalized.endsWith('sss') ? '---' : '--';
    return normalized.startsWith('MM') ? `--:--.${decimals}` : `--.${decimals}`;
  }

  function columnWidths(format) {
    return COLUMN_WIDTHS[normalizeFormat(format)];
  }

  function headerLabel(format) {
      const normalized = normalizeFormat(format);

      if (normalized === 'SS.ss') {
          return 'Last L';
      }

      return normalized.startsWith('MM') ? 'Last Lap' : 'Last Lp';
  }

  function format(seconds, format = DEFAULT_FORMAT) {
    const normalized = normalizeFormat(format);
    if (typeof seconds !== 'number' || !Number.isFinite(seconds) || seconds <= 0) {
      return placeholder(normalized);
    }

    const totalMilliseconds = Math.floor(seconds * 1000);
    const minutes = Math.floor(totalMilliseconds / 60000);
    const secondsInMinute = Math.floor((totalMilliseconds % 60000) / 1000);
    const milliseconds = totalMilliseconds % 1000;
    const fraction = normalized.endsWith('sss')
      ? String(milliseconds).padStart(3, '0')
      : String(Math.floor(milliseconds / 10)).padStart(2, '0');
    const secondsPart = String(secondsInMinute).padStart(2, '0');

    return normalized.startsWith('MM')
      ? `${String(minutes).padStart(2, '0')}:${secondsPart}.${fraction}`
      : `${secondsPart}.${fraction}`;
  }

  return {
    COLUMN_WIDTHS,
    DEFAULT_FORMAT,
    FORMATS,
    columnWidths,
    format,
    headerLabel,
    normalizeFormat,
    placeholder,
  };
}));

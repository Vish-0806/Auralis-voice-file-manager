export const spacing = {
  none: '0',
  xs: '0.25rem',     // 4px
  sm: '0.5rem',      // 8px
  md: '1rem',        // 16px
  lg: '1.5rem',      // 24px
  xl: '2rem',        // 32px
  '2xl': '3rem',     // 48px
  '3xl': '4rem',     // 64px
  '4xl': '6rem',     // 96px
};

export const typography = {
  fontFamilies: {
    sans: "system-ui, -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif",
    mono: "SFMono-Regular, Menlo, Monaco, Consolas, 'Liberation Mono', 'Courier New', monospace"
  },
  fontSizes: {
    display: '2.5rem',   // 40px
    h1: '2rem',          // 32px
    h2: '1.5rem',        // 24px
    h3: '1.25rem',       // 20px
    h4: '1.1rem',        // 17.6px
    bodyLarge: '1.125rem', // 18px
    body: '1rem',        // 16px
    bodySmall: '0.875rem', // 14px
    caption: '0.75rem',  // 12px
    label: '0.875rem',   // 14px
    code: '0.875rem'     // 14px
  },
  fontWeights: {
    light: '300',
    normal: '400',
    medium: '500',
    semibold: '600',
    bold: '700'
  },
  lineHeights: {
    none: '1',
    tight: '1.25',
    normal: '1.5',
    loose: '1.75'
  },
  letterSpacing: {
    tighter: '-0.05em',
    tight: '-0.025em',
    normal: '0',
    wide: '0.025em'
  }
};

export const borders = {
  widths: {
    none: '0',
    thin: '1px',
    medium: '2px',
    thick: '4px'
  },
  radii: {
    none: '0',
    sm: '0.25rem',      // 4px
    md: '0.375rem',     // 6px
    lg: '0.5rem',       // 8px
    xl: '0.75rem',      // 12px
    pill: '50rem',
    circle: '50%'
  }
};

export const shadows = {
  none: 'none',
  sm: '0 0.125rem 0.25rem rgba(0, 0, 0, 0.075)',
  md: '0 0.5rem 1rem rgba(0, 0, 0, 0.15)',
  lg: '0 1rem 3rem rgba(0, 0, 0, 0.175)',
  xl: '0 1.5rem 4rem rgba(0, 0, 0, 0.2)'
};

export const motion = {
  durations: {
    fast: '150ms',
    normal: '250ms',
    slow: '350ms'
  },
  easings: {
    easeIn: 'cubic-bezier(0.4, 0, 1, 1)',
    easeOut: 'cubic-bezier(0, 0, 0.2, 1)',
    easeInOut: 'cubic-bezier(0.4, 0, 0.2, 1)',
    linear: 'linear'
  }
};

export const breakpoints = {
  xs: '0',
  sm: '576px',
  md: '768px',
  lg: '992px',
  xl: '1200px',
  xxl: '1400px'
};

export const zIndex = {
  base: '0',
  dropdown: '1000',
  sticky: '1020',
  fixed: '1030',
  sidebar: '1040',
  modalBackdrop: '1050',
  modal: '1060',
  toast: '1070',
  tooltip: '1080'
};

export const tokens = {
  spacing,
  typography,
  borders,
  shadows,
  motion,
  breakpoints,
  zIndex
};

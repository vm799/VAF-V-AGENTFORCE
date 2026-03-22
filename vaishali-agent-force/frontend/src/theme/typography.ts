/** Typography tokens — using Inter font */

export const typography = {
  fontFamily: "'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif",
  sizes: {
    hero: '2rem',
    h1: '1.5rem',
    h2: '1.125rem',
    h3: '1rem',
    body: '0.875rem',
    small: '0.75rem',
    xs: '0.625rem',
  },
  weights: {
    light: 300,
    regular: 400,
    medium: 500,
    semibold: 600,
    bold: 700,
  },
} as const;

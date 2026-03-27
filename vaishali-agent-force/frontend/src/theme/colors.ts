/** Vaishali Command Center — Design Tokens */

export const colors = {
  // Backgrounds
  bg: {
    primary: '#0f1117',      // Near-black with blue tint
    secondary: '#161b22',    // Card backgrounds
    tertiary: '#1c2333',     // Elevated surfaces
    hover: '#21293a',        // Hover state
  },

  // Accent colours per agent
  accent: {
    teal: '#2dd4bf',         // Primary accent
    finance: '#4ade80',      // Soft green
    content: '#a78bfa',      // Purple
    education: '#60a5fa',    // Blue
    research: '#38bdf8',     // Light blue
    health: '#fb923c',       // Warm orange
  },

  // Text
  text: {
    primary: '#e2e8f0',      // Main text
    secondary: '#94a3b8',    // Muted text
    muted: '#64748b',        // Very muted
    inverse: '#0f1117',      // On light backgrounds
  },

  // Status
  status: {
    success: '#4ade80',
    warning: '#fbbf24',
    error: '#f87171',
    info: '#60a5fa',
  },

  // Borders
  border: {
    subtle: '#1e293b',
    default: '#334155',
  },
} as const;

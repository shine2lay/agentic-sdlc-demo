/* Color and layout constants for the execution detail view. */

export const STATUS_COLORS: Record<string, string> = {
  completed: 'var(--color-temper-completed)',
  running: 'var(--color-temper-running)',
  failed: 'var(--color-temper-failed)',
  pending: 'var(--color-temper-pending)',
};

export const STATUS_BG_COLORS: Record<string, string> = {
  completed: 'var(--color-temper-bg-completed)',
  running: 'var(--color-temper-bg-running)',
  failed: 'var(--color-temper-bg-failed)',
  pending: 'var(--color-temper-bg-pending)',
};

export const STAGE_PALETTE = [
  '#42a5f5', // blue
  '#ab47bc', // purple
  '#26a69a', // teal
  '#ffa726', // orange
  '#ec407a', // pink
  '#7e57c2', // deep purple
  '#26c6da', // cyan
  '#d4e157', // lime
  '#8d6e63', // brown
  '#78909c', // blue-grey
];

export const EDGE_COLORS = {
  dataFlow: 'var(--color-temper-running)',
  loopBack: 'var(--color-temper-loop-back)',
  collaboration: 'var(--color-temper-pending)',
  dataWire: '#10b981', // emerald-500
};

/* Layout constants for the DAG */
export const LAYOUT = {
  AGENT_WIDTH: 220,
  AGENT_HEIGHT: 100,
  AGENT_GAP_Y: 12,
  STAGE_GAP_X: 120,
  STAGE_GAP_Y: 40,
  STAGE_PAD_X: 20,
  STAGE_PAD_Y: 60,
  STAGE_HEADER_HEIGHT: 48,
  STAGE_METRICS_HEIGHT: 28,
  EXPANDED_AGENT_WIDTH: 480,
  EXPANDED_AGENT_HEIGHT: 280,
  EXPANDED_COLLAB_HEIGHT: 120,
  EXPANDED_STAGE_IO_HEIGHT: 160,
} as const;

/** DAG auto-fit padding (fraction of viewport). */
export const DAG_FIT_PADDING = 0.05;

/* Event log limits */
export const MAX_EVENT_LOG_SIZE = 1000;

/* Status icons (for colorblind accessibility) */
export const STATUS_ICONS: Record<string, string> = {
  completed: '\u2713', // checkmark
  running: '\u25B6',   // play triangle
  failed: '\u2717',    // cross
  pending: '\u25CB',   // circle
};

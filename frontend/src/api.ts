const API_URL = import.meta.env.VITE_API_URL || '';

export async function fetchHealth(): Promise<{ status: string }> {
  const res = await fetch(`${API_URL}/api/health`);
  if (!res.ok) throw new Error(`Health check failed: ${res.status}`);
  return res.json();
}

export async function fetchVersion(): Promise<{ version: string; deployed_by: string }> {
  const res = await fetch(`${API_URL}/api/version`);
  if (!res.ok) throw new Error(`Fetch version failed: ${res.status}`);
  return res.json();
}

export interface TypewriterLine { text: string; css_class: string; }
export interface TypewriterConfig { enabled: boolean; lines: TypewriterLine[]; speed_ms: number; start_delay_ms: number; }

export async function fetchTypewriterConfig(): Promise<TypewriterConfig> {
  const res = await fetch(`${API_URL}/api/typewriter-config`);
  if (!res.ok) throw new Error(`Fetch typewriter config failed: ${res.status}`);
  return res.json();
}

export interface BackToTopConfig {
  enabled: boolean;
  scroll_threshold_px: number;
  position_right_px: number;
  position_bottom_px: number;
  size_px: number;
  bg_color: string;
  hover_bg_color: string;
  icon_color: string;
  border_radius: string;
  transition_ms: number;
  scroll_behavior: ScrollBehavior;
}

export async function fetchBackToTopConfig(): Promise<BackToTopConfig> {
  const res = await fetch(`${API_URL}/api/back-to-top-config`);
  if (!res.ok) throw new Error(`Fetch back-to-top config failed: ${res.status}`);
  return res.json();
}

export interface ParallaxConfig {
  enabled: boolean;
  speed_factor: number;
  max_offset_px: number;
  direction: 'up' | 'down';
  easing: string;
}

export async function fetchParallaxConfig(): Promise<ParallaxConfig> {
  const res = await fetch(`${API_URL}/api/parallax-config`);
  if (!res.ok) throw new Error(`Fetch parallax config failed: ${res.status}`);
  return res.json();
}

export interface SparkleConfig {
  enabled: boolean;
  particle_count: number;
  duration_ms: number;
  spread_px: number;
  colors: string[];
  repeat_interval_ms: number;
  size_px: number;
  target: string;
}

export async function fetchSparkleConfig(): Promise<SparkleConfig> {
  const res = await fetch(`${API_URL}/api/sparkle-config`);
  if (!res.ok) throw new Error(`Fetch sparkle config failed: ${res.status}`);
  return res.json();
}

export interface GradientBorderConfig {
  enabled: boolean;
  colors: string[];
  angle_deg: number;
  animation_duration_ms: number;
  border_width_px: number;
  border_radius: string;
  target: string;
}

export async function fetchGradientBorderConfig(): Promise<GradientBorderConfig> {
  const res = await fetch(`${API_URL}/api/gradient-border-config`);
  if (!res.ok) throw new Error(`Fetch gradient border config failed: ${res.status}`);
  return res.json();
}

export interface TicTacToeConfig {
  board_size: number;
  player_symbols: string[];
  player_colors: string[];
  winning_length: number;
  empty_cell: string;
  title: string;
}

export async function fetchTicTacToeConfig(): Promise<TicTacToeConfig> {
  const res = await fetch(`${API_URL}/api/tictactoe-config`);
  if (!res.ok) throw new Error(`Fetch tictactoe config failed: ${res.status}`);
  return res.json();
}

export interface MarkdownPreviewConfig {
  title: string;
  default_markdown: string;
  editor_placeholder: string;
  debounce_ms: number;
}

export async function fetchMarkdownPreviewConfig(): Promise<MarkdownPreviewConfig> {
  const res = await fetch(`${API_URL}/api/markdown-preview-config`);
  if (!res.ok) throw new Error(`Fetch markdown preview config failed: ${res.status}`);
  return res.json();
}

export interface ColorPickerConfig {
  title: string;
  default_color: string;
  formats: string[];
  show_preview: boolean;
  preset_colors: string[];
}

export async function fetchColorPickerConfig(): Promise<ColorPickerConfig> {
  const res = await fetch(`${API_URL}/api/color-picker-config`);
  if (!res.ok) throw new Error(`Fetch color picker config failed: ${res.status}`);
  return res.json();
}

export interface SuggestionsCountData {
  total_suggestions: number;
  poll_interval_ms: number;
}

export async function fetchSuggestionsCount(): Promise<SuggestionsCountData> {
  const res = await fetch(`${API_URL}/api/suggestions-count`);
  if (!res.ok) throw new Error(`Fetch suggestions count failed: ${res.status}`);
  return res.json();
}

export interface ProgrammingJoke {
  joke: string;
  category: string;
}

export async function fetchProgrammingJoke(): Promise<ProgrammingJoke> {
  const res = await fetch(`${API_URL}/api/programming-joke`);
  if (!res.ok) throw new Error(`Fetch programming joke failed: ${res.status}`);
  return res.json();
}

export interface BounceButtonConfig {
  enabled: boolean;
  scale_start: number;
  scale_peak: number;
  duration_ms: number;
  easing: string;
  iteration_count: number;
  delay_ms: number;
  debounce_ms: number;
  skip_initial_render: boolean;
  respect_reduced_motion: boolean;
  target: string;
}

export async function fetchBounceButtonConfig(): Promise<BounceButtonConfig> {
  const res = await fetch(`${API_URL}/api/bounce-button-config`);
  if (!res.ok) throw new Error(`Fetch bounce button config failed: ${res.status}`);
  return res.json();
}

export interface ConfettiConfig {
  enabled: boolean;
  particle_count: number;
  duration_ms: number;
  spread_px: number;
  colors: string[];
  gravity: number;
  drift: number;
  size_range: number[];
  shapes: string[];
  trigger: string;
  trigger_from: string;
  trigger_to: string;
  respect_reduced_motion: boolean;
  target: string;
  max_concurrent: number;
}

export async function fetchConfettiConfig(): Promise<ConfettiConfig> {
  const res = await fetch(`${API_URL}/api/confetti-config`);
  if (!res.ok) throw new Error(`Fetch confetti config failed: ${res.status}`);
  return res.json();
}

export interface AsciiArtConfig {
  title: string;
  default_text: string;
  max_length: number;
  block_char: string;
  empty_char: string;
  supported_characters: string;
  letter_height: number;
}

export interface AsciiArtResponse {
  art: string;
  original_text: string;
  width: number;
  height: number;
}

export async function fetchAsciiArtConfig(): Promise<AsciiArtConfig> {
  const res = await fetch(`${API_URL}/api/ascii-art-config`);
  if (!res.ok) throw new Error(`Fetch ASCII art config failed: ${res.status}`);
  return res.json();
}

export async function generateAsciiArt(text: string): Promise<AsciiArtResponse> {
  const res = await fetch(`${API_URL}/api/ascii-art-generate`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ text }),
  });
  if (!res.ok) throw new Error(`Generate ASCII art failed: ${res.status}`);
  return res.json();
}

export async function fetchRuns(): Promise<{ runs: Run[]; total: number }> {
  const res = await fetch(`${API_URL}/api/runs`);
  if (!res.ok) throw new Error(`Fetch runs failed: ${res.status}`);
  return res.json();
}

export async function fetchRun(id: string): Promise<Run> {
  const res = await fetch(`${API_URL}/api/runs/${id}`);
  if (!res.ok) throw new Error(`Fetch run failed: ${res.status}`);
  return res.json();
}

export async function submitSuggestion(suggestion: string): Promise<{ status: string; execution_id?: string; message: string }> {
  const res = await fetch(`${API_URL}/api/suggest`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ suggestion }),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: 'Request failed' }));
    throw new Error(err.detail || 'Request failed');
  }
  return res.json();
}

export interface Run {
  id: string;
  workflow: string;
  status: string;
  inputs?: Record<string, unknown>;
  result?: Record<string, unknown> | null;
  error?: string | null;
  worker_id?: string | null;
  created_at: string;
  started_at?: string | null;
  completed_at?: string | null;
  has_result?: boolean;
  duration_seconds?: number | null;
  total_tokens?: number | null;
  workflow_output?: { result?: string; reason?: string } | null;
}

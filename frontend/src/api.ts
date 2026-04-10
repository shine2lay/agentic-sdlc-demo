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
export interface TypewriterConfig { lines: TypewriterLine[]; speed_ms: number; start_delay_ms: number; }

export async function fetchTypewriterConfig(): Promise<TypewriterConfig> {
  const res = await fetch(`${API_URL}/api/typewriter-config`);
  if (!res.ok) throw new Error(`Fetch typewriter config failed: ${res.status}`);
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

export async function createRun(workflow: string, inputs: Record<string, unknown> = {}): Promise<{ id: string; status: string }> {
  const res = await fetch(`${API_URL}/api/runs`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ workflow, inputs }),
  });
  return res.json();
}

export function connectRunWebSocket(runId: string, onMessage: (msg: unknown) => void): WebSocket {
  const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
  const wsBase = API_URL.replace(/^http(s?):/, `ws$1:`) || `${protocol}//${window.location.host}`;
  const ws = new WebSocket(`${wsBase}/ws/${runId}`);
  ws.onmessage = (e) => onMessage(JSON.parse(e.data));
  return ws;
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

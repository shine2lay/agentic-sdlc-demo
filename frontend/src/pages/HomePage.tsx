import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { fetchHealth, fetchRuns, submitSuggestion, type Run } from '../api';
import { formatTimeAgo } from '../execution/utils';

function formatDuration(seconds: number | null | undefined): string {
  if (seconds === null || seconds === undefined) return '';
  if (seconds < 60) return `${Math.round(seconds)}s`;
  if (seconds < 3600) return `${Math.round(seconds / 60)}m ${Math.round(seconds % 60)}s`;
  const hours = Math.floor(seconds / 3600);
  const mins = Math.round((seconds % 3600) / 60);
  return `${hours}h ${mins}m`;
}

function formatTokens(tokens: number | null | undefined): string {
  if (tokens === null || tokens === undefined) return '';
  if (tokens >= 1000000) return `${(tokens / 1000000).toFixed(1)}M tokens`;
  if (tokens >= 1000) return `${(tokens / 1000).toFixed(1)}K tokens`;
  return `${tokens} tokens`;
}

function isClickable(run: Run): boolean {
  if (run.status === 'running' || run.status === 'claimed') return true;
  // List endpoint returns has_result instead of full result data
  return !!(run as unknown as { has_result?: boolean }).has_result;
}

function StatusDot({ status }: { status: string }) {
  const colors: Record<string, string> = {
    ok: 'bg-emerald-500',
    error: 'bg-red-500',
    loading: 'bg-gray-500',
    pending: 'bg-yellow-500',
    claimed: 'bg-blue-500',
    running: 'bg-blue-500',
    completed: 'bg-emerald-500',
    failed: 'bg-red-500',
  };
  return <span className={`inline-block w-2 h-2 rounded-full ${colors[status] ?? 'bg-gray-500'}`} />;
}

function StatusBadge({ status }: { status: string }) {
  const styles: Record<string, string> = {
    pending: 'bg-yellow-900/50 text-yellow-400 border-yellow-700/50',
    claimed: 'bg-blue-900/50 text-blue-400 border-blue-700/50',
    running: 'bg-blue-900/50 text-blue-400 border-blue-700/50',
    completed: 'bg-emerald-900/50 text-emerald-400 border-emerald-700/50',
    failed: 'bg-red-900/50 text-red-400 border-red-700/50',
  };
  return (
    <span className={`text-xs font-medium px-2 py-0.5 rounded border ${styles[status] ?? 'bg-gray-800 text-gray-400 border-gray-700'}`}>
      {status}
    </span>
  );
}

const RUNS_CACHE_KEY = 'sdlc-runs-cache';

function getCachedRuns(): Run[] {
  try {
    const cached = sessionStorage.getItem(RUNS_CACHE_KEY);
    return cached ? JSON.parse(cached) : [];
  } catch { return []; }
}

function cacheRuns(runs: Run[]) {
  try { sessionStorage.setItem(RUNS_CACHE_KEY, JSON.stringify(runs)); } catch { /* ignore */ }
}

export function HomePage() {
  const navigate = useNavigate();
  const [health, setHealth] = useState<string>('loading');
  const [runs, setRuns] = useState<Run[]>(getCachedRuns);
  const [loading, setLoading] = useState(runs.length === 0);
  const [suggestion, setSuggestion] = useState('');
  const [submitState, setSubmitState] = useState<'idle' | 'submitting' | 'success' | 'error'>('idle');
  const [submitMessage, setSubmitMessage] = useState('');

  useEffect(() => {
    fetchHealth()
      .then(() => setHealth('ok'))
      .catch(() => setHealth('error'));

    fetchRuns()
      .then((data) => {
        const r = data?.runs ?? [];
        setRuns(r);
        cacheRuns(r);
        setLoading(false);
      })
      .catch(() => setLoading(false));

    const interval = setInterval(() => {
      fetchRuns()
        .then((data) => {
          const r = data?.runs ?? [];
          setRuns(r);
          cacheRuns(r);
        })
        .catch(() => {});
    }, 5000);

    return () => clearInterval(interval);
  }, []);

  const handleSubmit = async () => {
    if (!suggestion.trim()) return;
    setSubmitState('submitting');
    setSubmitMessage('');
    try {
      const result = await submitSuggestion(suggestion);
      setSubmitState('success');
      setSubmitMessage(result.message);
      setSuggestion('');
      setTimeout(() => setSubmitState('idle'), 5000);
    } catch (err) {
      setSubmitState('error');
      setSubmitMessage(err instanceof Error ? err.message : 'Something went wrong');
      setTimeout(() => setSubmitState('idle'), 5000);
    }
  };

  return (
    <div className="max-w-4xl mx-auto p-8 h-full overflow-auto">
      <div className="flex justify-between items-center mb-8 pb-4 border-b border-[var(--temper-border)]">
        <div>
          <h1 className="text-xl font-semibold text-[var(--temper-text)]">Agentic SDLC</h1>
          <p className="text-sm text-[var(--temper-text-muted)] mt-1">Autonomous multi-agent software development pipeline</p>
        </div>
        <div className="flex items-center gap-2 text-sm text-[var(--temper-text-muted)]">
          <StatusDot status={health} />
          {health === 'ok' ? 'API connected' : health === 'error' ? 'API unreachable' : 'Connecting...'}
        </div>
      </div>

      <div className="mb-8">
        <div className="text-xs font-semibold text-[var(--temper-text-muted)] uppercase tracking-wide mb-3">
          Suggest a Feature
        </div>
        <div className="flex gap-3 items-end">
          <textarea
            className="flex-1 bg-[var(--temper-surface)] border border-[var(--temper-border)] rounded-lg px-3 py-2 text-sm text-[var(--temper-text)] placeholder-[var(--temper-text-dim)] resize-y min-h-[60px] focus:outline-none focus:border-[var(--temper-accent)] transition-colors"
            placeholder="Describe a feature or change you'd like to see. Your suggestion will be triaged, analyzed, and processed through our agentic AI pipeline - from initial review to code generation, testing, and deployment - all handled autonomously by AI agents."
            value={suggestion}
            onChange={(e) => setSuggestion(e.target.value)}
            rows={3}
            disabled={submitState === 'submitting'}
          />
          <button
            className="bg-[var(--temper-accent)] text-white rounded-lg px-5 py-2 text-sm font-medium whitespace-nowrap hover:opacity-85 disabled:opacity-40 disabled:cursor-not-allowed transition-opacity"
            onClick={handleSubmit}
            disabled={!suggestion.trim() || submitState === 'submitting'}
          >
            {submitState === 'submitting' ? 'Submitting...' : 'Send Suggestion'}
          </button>
        </div>
        {submitMessage && (
          <div className={`mt-2 text-sm px-3 py-2 rounded-md ${submitState === 'success' ? 'bg-emerald-950 text-emerald-400' : 'bg-red-950 text-red-400'}`}>
            {submitMessage}
          </div>
        )}
      </div>

      <div className="text-xs font-semibold text-[var(--temper-text-muted)] uppercase tracking-wide mb-3">
        Runs
      </div>

      {loading ? (
        <div className="flex flex-col gap-2">
          {Array.from({ length: 3 }).map((_, i) => (
            <div key={i} className="bg-[var(--temper-surface)] border border-[var(--temper-border)] rounded-lg px-4 py-3 flex justify-between items-center">
              <div className="flex flex-col gap-2">
                <div className="skeleton h-4 w-32" />
                <div className="skeleton h-3 w-48" />
              </div>
              <div className="skeleton h-5 w-16 rounded" />
            </div>
          ))}
        </div>
      ) : runs.length === 0 ? (
        <div className="text-center py-12 text-[var(--temper-text-muted)]">
          No runs yet. Submit a suggestion to kick off the pipeline.
        </div>
      ) : (
        <div className="flex flex-col gap-2">
          {runs.map((run) => {
            const clickable = isClickable(run);
            const duration = formatDuration(run.duration_seconds);
            const tokens = formatTokens(run.total_tokens);
            return (
              <div
                key={run.id}
                className={`bg-[var(--temper-surface)] border border-[var(--temper-border)] rounded-lg px-4 py-3 flex justify-between items-center transition-colors ${clickable ? 'cursor-pointer hover:border-[var(--temper-accent)]' : ''}`}
                onClick={() => clickable && navigate(`/runs/${run.id}`)}
              >
                <div className="flex flex-col gap-1 min-w-0">
                  <span className="font-medium text-sm truncate">
                    {(run.inputs as Record<string, unknown>)?.task_description as string || run.workflow}
                  </span>
                  <span className="text-xs text-[var(--temper-text-muted)]">
                    {run.id.slice(0, 8)} &middot; {formatTimeAgo(run.created_at)}
                  </span>
                  {(duration || tokens) && (
                    <span className="text-xs text-[var(--temper-text-dim)]">
                      {duration && <span>{duration}</span>}
                      {duration && tokens && <span className="mx-2">&middot;</span>}
                      {tokens && <span>{tokens}</span>}
                    </span>
                  )}
                  {run.error && <span className="text-xs text-red-400 font-medium">{run.error.slice(0, 100)}</span>}
                </div>
                <div className="flex items-center gap-3">
                  <StatusBadge status={run.status} />
                  {clickable && <span className="text-[var(--temper-text-muted)] text-lg">&rsaquo;</span>}
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}

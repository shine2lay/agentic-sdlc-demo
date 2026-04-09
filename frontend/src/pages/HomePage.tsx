import { useEffect, useMemo, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { fetchHealth, fetchRuns, submitSuggestion, type Run } from '../api';
import { formatTimeAgo } from '../execution/utils';

// ── Helpers ────────────────────────────────────────────────

function formatDuration(seconds: number | null | undefined): string {
  if (seconds === null || seconds === undefined) return '';
  if (seconds < 60) return `${Math.round(seconds)}s`;
  if (seconds < 3600) return `${Math.round(seconds / 60)}m ${Math.round(seconds % 60)}s`;
  const hours = Math.floor(seconds / 3600);
  const mins = Math.round((seconds % 3600) / 60);
  return `${hours}h ${mins}m`;
}

function formatCost(cost: number | null | undefined): string {
  if (cost === null || cost === undefined || cost === 0) return '';
  return `$${cost.toFixed(2)}`;
}

function isClickable(run: Run): boolean {
  if (run.status === 'running' || run.status === 'claimed') return true;
  return !!(run as unknown as { has_result?: boolean }).has_result;
}

function getErrorCategory(error: string): string {
  if (!error) return '';
  const lower = error.toLowerCase();
  if (lower.includes('duplicate') || lower.includes('semantically identical')) return 'Duplicate detected';
  if (lower.includes('safety') || lower.includes('security') || lower.includes('malicious')) return 'Safety rejected';
  if (lower.includes('scope') || lower.includes('complex') || lower.includes('out of scope')) return 'Out of scope';
  if (lower.includes('content') || lower.includes('inappropriate')) return 'Content rejected';
  return 'Rejected';
}

// ── Pipeline stages data ───────────────────────────────────

const PIPELINE_STAGES = [
  { num: 1, name: 'Validate', agents: 3, type: '👑 leader', desc: 'Feasibility, safety, product fit' },
  { num: 2, name: 'Dedup', agents: 1, type: 'single', desc: 'Check for duplicate features' },
  { num: 3, name: 'Clone', agents: 0, type: 'script', desc: 'Clone the repository' },
  { num: 4, name: 'Analyze', agents: 2, type: '⚡ parallel', desc: 'Code + test analysis' },
  { num: 5, name: 'Plan', agents: 3, type: '👑 leader', desc: 'Architecture, critique, decision' },
  { num: 6, name: 'Build', agents: 2, type: '→ sequential', desc: 'Write tests, then implement' },
  { num: 7, name: 'Review', agents: 4, type: '👑 leader', desc: 'Syntax, tests, diff review' },
  { num: 8, name: 'Push', agents: 0, type: 'script', desc: 'Git push + merge' },
  { num: 9, name: 'Cleanup', agents: 0, type: 'script', desc: 'Remove temp files' },
  { num: 10, name: 'Verify', agents: 3, type: '⚡ parallel', desc: 'Health, smoke, visual check' },
];

// ── Small components ───────────────────────────────────────

function StatusDot({ status }: { status: string }) {
  const colors: Record<string, string> = {
    ok: 'bg-emerald-500', error: 'bg-red-500', loading: 'bg-gray-500',
  };
  return <span className={`inline-block w-2 h-2 rounded-full ${colors[status] ?? 'bg-gray-500'}`} />;
}

// ── Run list cache ─────────────────────────────────────────

const RUNS_CACHE_KEY = 'sdlc-runs-cache';
function getCachedRuns(): Run[] {
  try { return JSON.parse(sessionStorage.getItem(RUNS_CACHE_KEY) || '[]'); } catch { return []; }
}
function cacheRuns(runs: Run[]) {
  try { sessionStorage.setItem(RUNS_CACHE_KEY, JSON.stringify(runs)); } catch {}
}

// ── Main component ─────────────────────────────────────────

export function HomePage() {
  const navigate = useNavigate();
  const [health, setHealth] = useState<string>('loading');
  const [runs, setRuns] = useState<Run[]>(getCachedRuns);
  const [loading, setLoading] = useState(runs.length === 0);
  const [suggestion, setSuggestion] = useState('');
  const [submitState, setSubmitState] = useState<'idle' | 'submitting' | 'success' | 'error'>('idle');
  const [submitMessage, setSubmitMessage] = useState('');
  const [filter, setFilter] = useState<'all' | 'completed' | 'failed'>('all');
  const [showCount, setShowCount] = useState(10);

  useEffect(() => {
    fetchHealth().then(() => setHealth('ok')).catch(() => setHealth('error'));
    fetchRuns().then((data) => {
      const r = data?.runs ?? [];
      setRuns(r);
      cacheRuns(r);
      setLoading(false);
    }).catch(() => setLoading(false));

    const interval = setInterval(() => {
      fetchRuns().then((data) => {
        const r = data?.runs ?? [];
        setRuns(r);
        cacheRuns(r);
      }).catch(() => {});
    }, 5000);
    return () => clearInterval(interval);
  }, []);

  // Computed stats
  const stats = useMemo(() => {
    const completed = runs.filter(r => r.status === 'completed').length;
    const failed = runs.filter(r => r.status === 'failed').length;
    const completedRuns = runs.filter(r => r.status === 'completed' && r.duration_seconds);
    const avgDuration = completedRuns.length > 0
      ? completedRuns.reduce((s, r) => s + (r.duration_seconds || 0), 0) / completedRuns.length
      : 0;
    return { total: runs.length, completed, failed, avgDuration };
  }, [runs]);

  // Filtered runs
  const filteredRuns = useMemo(() => {
    const filtered = filter === 'all' ? runs : runs.filter(r => r.status === filter);
    return filtered.slice(0, showCount);
  }, [runs, filter, showCount]);

  const totalFiltered = filter === 'all' ? runs.length : runs.filter(r => r.status === filter).length;

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
    <div className="max-w-4xl mx-auto px-8 h-full overflow-auto">

      {/* ── Hero ────────────────────────────────────────── */}
      <section className="pt-12 pb-8 text-center">
        <div className="flex items-center justify-center gap-2 mb-6">
          <StatusDot status={health} />
          <span className="text-xs text-[var(--temper-text-muted)]">
            {health === 'ok' ? 'API connected' : health === 'error' ? 'API unreachable' : 'Connecting...'}
          </span>
        </div>

        <h1 className="text-3xl font-bold tracking-tight text-[var(--temper-text)]">
          Agentic SDLC
        </h1>
        <p className="text-xl text-[var(--temper-text-muted)] mt-3 max-w-2xl mx-auto">
          From idea to deployed code in under 7 minutes.
        </p>
        <p className="text-base text-[var(--temper-text-dim)] mt-2 max-w-xl mx-auto leading-relaxed">
          An autonomous AI pipeline that validates, plans, codes, tests, reviews, and deploys your feature request — no human in the loop.
        </p>

        {stats.total > 0 && (
          <div className="flex gap-4 justify-center mt-8">
            {[
              { value: String(stats.completed), label: 'deployed' },
              { value: '10', label: 'stages' },
              { value: '21', label: 'AI agents' },
              { value: `~${formatDuration(stats.avgDuration)}`, label: 'avg time' },
            ].map(({ value, label }) => (
              <div key={label} className="bg-[var(--temper-surface)] border border-[var(--temper-border)] rounded-lg px-5 py-3">
                <div className="text-2xl font-bold text-[var(--temper-accent)]">{value}</div>
                <div className="text-xs text-[var(--temper-text-muted)] uppercase tracking-wide">{label}</div>
              </div>
            ))}
          </div>
        )}

        <a
          href="#suggest"
          className="inline-block mt-6 bg-[var(--temper-accent)] text-black rounded-lg px-6 py-2.5 text-sm font-medium hover:opacity-85 transition-opacity"
        >
          Try it — suggest a feature ↓
        </a>
      </section>

      {/* ── How It Works ────────────────────────────────── */}
      <section className="py-8 border-t border-[var(--temper-border)]">
        <div className="text-xs font-semibold text-[var(--temper-text-muted)] uppercase tracking-wide mb-2">
          How It Works
        </div>
        <p className="text-sm text-[var(--temper-text-dim)] mb-5">
          You describe a feature. AI agents handle the rest.
        </p>

        <div className="grid grid-cols-5 gap-2">
          {PIPELINE_STAGES.map((stage, i) => (
            <div
              key={stage.num}
              className="bg-[var(--temper-surface)] border border-[var(--temper-border)] rounded-lg p-2.5 relative"
            >
              <div className="text-[10px] text-[var(--temper-accent)] font-mono mb-0.5">{stage.num}</div>
              <div className="text-xs font-medium text-[var(--temper-text)] leading-tight">{stage.name}</div>
              <div className="text-[10px] text-[var(--temper-text-dim)] mt-0.5 leading-tight">{stage.desc}</div>
              {stage.agents > 0 && (
                <div className="text-[10px] text-[var(--temper-text-muted)] mt-1">{stage.agents} agents</div>
              )}
              {stage.agents === 0 && (
                <div className="text-[10px] text-[var(--temper-text-muted)] mt-1 italic">script</div>
              )}
              {/* Arrow */}
              {i < PIPELINE_STAGES.length - 1 && (
                <span className="absolute -right-2 top-1/2 -translate-y-1/2 text-[var(--temper-border-light)] text-xs z-10">→</span>
              )}
            </div>
          ))}
        </div>

        <p className="text-xs text-[var(--temper-text-dim)] mt-4">
          Safety guardrails are built in — {stats.failed} runs have been correctly rejected for security, content, scope, or duplication.
        </p>
      </section>

      {/* ── Suggest ─────────────────────────────────────── */}
      <section id="suggest" className="py-8 border-t border-[var(--temper-border)]">
        <div className="text-xs font-semibold text-[var(--temper-text-muted)] uppercase tracking-wide mb-2">
          Try It Yourself
        </div>
        <p className="text-sm text-[var(--temper-text-dim)] mb-4">
          Describe a feature and watch AI agents build, test, and deploy it in minutes.
        </p>

        <div className="flex gap-3 items-end">
          <textarea
            className="flex-1 bg-[var(--temper-surface)] border border-[var(--temper-border)] rounded-lg px-3 py-2 text-sm text-[var(--temper-text)] placeholder-[var(--temper-text-dim)] resize-y min-h-[60px] focus:outline-none focus:border-[var(--temper-accent)] transition-colors"
            placeholder='e.g. "Add a /api/reverse endpoint that takes a text parameter and returns it reversed"'
            value={suggestion}
            onChange={(e) => setSuggestion(e.target.value)}
            rows={3}
            disabled={submitState === 'submitting'}
          />
          <button
            className="bg-[var(--temper-accent)] text-black rounded-lg px-5 py-2 text-sm font-medium whitespace-nowrap hover:opacity-85 disabled:opacity-40 disabled:cursor-not-allowed transition-opacity"
            onClick={handleSubmit}
            disabled={!suggestion.trim() || submitState === 'submitting'}
          >
            {submitState === 'submitting' ? 'Submitting...' : 'Send Suggestion'}
          </button>
        </div>

        <p className="text-xs text-[var(--temper-text-dim)] mt-2">
          💡 Good suggestions: simple API endpoints with clear input/output. The pipeline handles validation, coding, testing, review, and deployment automatically.
        </p>

        {submitMessage && (
          <div className={`mt-2 text-sm px-3 py-2 rounded-md ${submitState === 'success' ? 'bg-emerald-950 text-emerald-400' : 'bg-red-950 text-red-400'}`}>
            {submitMessage}
          </div>
        )}
      </section>

      {/* ── Runs ────────────────────────────────────────── */}
      <section className="py-8 border-t border-[var(--temper-border)] pb-16">
        <div className="text-xs font-semibold text-[var(--temper-text-muted)] uppercase tracking-wide mb-3">
          Recent Runs
        </div>

        {/* Filter tabs */}
        <div className="flex gap-4 mb-4 border-b border-[var(--temper-border)]">
          {(['all', 'completed', 'failed'] as const).map((tab) => {
            const count = tab === 'all' ? runs.length : runs.filter(r => r.status === tab).length;
            const active = filter === tab;
            return (
              <button
                key={tab}
                onClick={() => { setFilter(tab); setShowCount(10); }}
                className={`text-sm font-medium pb-2 transition-colors ${
                  active
                    ? 'text-[var(--temper-text)] border-b-2 border-[var(--temper-accent)]'
                    : 'text-[var(--temper-text-muted)] hover:text-[var(--temper-text)]'
                }`}
              >
                {tab === 'all' ? 'All' : tab === 'completed' ? '✓ Completed' : '✗ Failed'}
                <span className="text-xs text-[var(--temper-text-dim)] ml-1">({count})</span>
              </button>
            );
          })}
        </div>

        {loading ? (
          <div className="flex flex-col gap-2">
            {[1, 2, 3].map(i => (
              <div key={i} className="bg-[var(--temper-surface)] border border-[var(--temper-border)] rounded-lg px-4 py-3">
                <div className="skeleton h-4 w-64" />
                <div className="skeleton h-3 w-32 mt-2" />
              </div>
            ))}
          </div>
        ) : filteredRuns.length === 0 ? (
          <div className="text-center py-12 text-[var(--temper-text-muted)]">
            {filter === 'all' ? 'No runs yet. Submit a suggestion to kick off the pipeline.' : `No ${filter} runs.`}
          </div>
        ) : (
          <>
            <div className="flex flex-col gap-2">
              {filteredRuns.map((run) => {
                const clickable = isClickable(run);
                const duration = formatDuration(run.duration_seconds);
                const cost = formatCost((run as any).total_cost_usd);
                const isCompleted = run.status === 'completed';
                const isFailed = run.status === 'failed';
                const borderColor = isCompleted
                  ? 'border-l-emerald-500'
                  : isFailed
                  ? 'border-l-red-500'
                  : 'border-l-blue-500';

                return (
                  <div
                    key={run.id}
                    className={`bg-[var(--temper-surface)] border border-[var(--temper-border)] border-l-[3px] ${borderColor} rounded-lg px-4 py-3 transition-colors ${clickable ? 'cursor-pointer hover:border-[var(--temper-accent)] hover:border-l-[var(--temper-accent)]' : ''}`}
                    onClick={() => clickable && navigate(`/runs/${run.id}`)}
                  >
                    <div className="flex items-start gap-2">
                      <span className={`mt-0.5 text-sm ${isCompleted ? 'text-emerald-400' : isFailed ? 'text-red-400' : 'text-blue-400'}`}>
                        {isCompleted ? '✓' : isFailed ? '✗' : '●'}
                      </span>
                      <div className="min-w-0 flex-1">
                        <p className="text-sm text-[var(--temper-text)] truncate font-medium">
                          {(run.inputs as Record<string, unknown>)?.task_description as string || run.workflow}
                        </p>
                        <p className="text-xs text-[var(--temper-text-muted)] mt-1">
                          {duration && <span>{duration}</span>}
                          {duration && cost && <span className="mx-1.5">·</span>}
                          {cost && <span>{cost}</span>}
                          {(duration || cost) && <span className="mx-1.5">·</span>}
                          <span>{formatTimeAgo(run.created_at)}</span>
                        </p>
                        {isFailed && run.error && (
                          <p className="text-xs text-red-400/80 mt-1">{getErrorCategory(run.error)}</p>
                        )}
                      </div>
                    </div>
                  </div>
                );
              })}
            </div>

            {showCount < totalFiltered && (
              <button
                onClick={() => setShowCount(c => c + 10)}
                className="mt-4 w-full text-center text-sm text-[var(--temper-text-muted)] hover:text-[var(--temper-text)] py-2 border border-[var(--temper-border)] rounded-lg hover:bg-[var(--temper-surface)] transition-colors"
              >
                Show more ({totalFiltered - showCount} remaining)
              </button>
            )}
          </>
        )}
      </section>
    </div>
  );
}

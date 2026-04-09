import { useEffect, useMemo, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { fetchHealth, fetchRuns, submitSuggestion, type Run } from '../api';
import { formatTimeAgo } from '../execution/utils';

// ── Helpers ────────────────────────────────────────────────

function formatDuration(s: number | null | undefined): string {
  if (!s) return '';
  if (s < 60) return `${Math.round(s)}s`;
  return `${Math.round(s / 60)}m ${Math.round(s % 60)}s`;
}

function isClickable(run: Run): boolean {
  if (run.status === 'running' || run.status === 'claimed') return true;
  return !!(run as unknown as { has_result?: boolean }).has_result;
}

function StatusDot({ status }: { status: string }) {
  const c: Record<string, string> = { ok: 'bg-emerald-500', error: 'bg-red-500', loading: 'bg-gray-500' };
  return <span className={`inline-block w-2 h-2 rounded-full ${c[status] ?? 'bg-gray-500'}`} />;
}

// ── Pipeline animation ─────────────────────────────────────

const STAGES = ['Validate', 'Analyze', 'Plan', 'Build', 'Test', 'Review', 'Deploy', 'Verify'];

function PipelineAnimation() {
  const [active, setActive] = useState(0);
  useEffect(() => {
    const timer = setInterval(() => setActive(a => (a + 1) % STAGES.length), 800);
    return () => clearInterval(timer);
  }, []);

  return (
    <div className="flex items-center justify-center gap-1 py-6">
      {STAGES.map((stage, i) => (
        <div key={stage} className="flex items-center">
          <div className={`flex flex-col items-center transition-all duration-300 ${i <= active ? 'opacity-100' : 'opacity-30'}`}>
            <div
              className={`w-10 h-10 rounded-full flex items-center justify-center text-xs font-bold transition-all duration-300 ${
                i < active ? 'bg-emerald-500/20 text-emerald-400 border-2 border-emerald-500/50' :
                i === active ? 'bg-[var(--temper-accent)]/20 text-[var(--temper-accent)] border-2 border-[var(--temper-accent)] scale-110 shadow-lg shadow-[var(--temper-accent)]/20' :
                'bg-[var(--temper-surface)] text-[var(--temper-text-dim)] border-2 border-[var(--temper-border)]'
              }`}
            >
              {i < active ? '✓' : i + 1}
            </div>
            <span className={`text-[10px] mt-1.5 font-medium transition-colors duration-300 ${
              i === active ? 'text-[var(--temper-accent)]' : 'text-[var(--temper-text-dim)]'
            }`}>
              {stage}
            </span>
          </div>
          {i < STAGES.length - 1 && (
            <div className={`w-6 h-0.5 mx-0.5 transition-colors duration-300 ${
              i < active ? 'bg-emerald-500/50' : 'bg-[var(--temper-border)]'
            }`} />
          )}
        </div>
      ))}
    </div>
  );
}

// ── Example suggestions ────────────────────────────────────

const EXAMPLE_SUGGESTIONS = [
  '🎨 Add a gradient banner at the top of the page that says "Powered by AI"',
  '✨ Add a confetti animation that triggers when viewing a completed run',
  '🌙 Add a greeting message in the header that changes based on time of day',
  '📊 Show a mini chart on the homepage that visualizes the success rate',
  '🎯 Add a pulsing "Live" indicator next to running suggestions',
];

// ── Cache ──────────────────────────────────────────────────

const CACHE_KEY = 'sdlc-runs-cache';
function getCached(): Run[] { try { return JSON.parse(sessionStorage.getItem(CACHE_KEY) || '[]'); } catch { return []; } }
function setCache(r: Run[]) { try { sessionStorage.setItem(CACHE_KEY, JSON.stringify(r)); } catch {} }

// ── Main ───────────────────────────────────────────────────

export function HomePage() {
  const navigate = useNavigate();
  const [health, setHealth] = useState<string>('loading');
  const [runs, setRuns] = useState<Run[]>(getCached);
  const [loading, setLoading] = useState(runs.length === 0);
  const [suggestion, setSuggestion] = useState('');
  const [submitState, setSubmitState] = useState<'idle' | 'submitting' | 'success' | 'error'>('idle');
  const [submitMessage, setSubmitMessage] = useState('');
  const [filter, setFilter] = useState<'all' | 'completed' | 'failed'>('all');
  const [showCount, setShowCount] = useState(8);

  useEffect(() => {
    fetchHealth().then(() => setHealth('ok')).catch(() => setHealth('error'));
    fetchRuns().then((d) => { const r = d?.runs ?? []; setRuns(r); setCache(r); setLoading(false); }).catch(() => setLoading(false));
    const interval = setInterval(() => {
      fetchRuns().then((d) => { const r = d?.runs ?? []; setRuns(r); setCache(r); }).catch(() => {});
    }, 5000);
    return () => clearInterval(interval);
  }, []);

  const stats = useMemo(() => {
    const completed = runs.filter(r => r.status === 'completed').length;
    const failed = runs.filter(r => r.status === 'failed').length;
    return { total: runs.length, completed, failed };
  }, [runs]);

  const filteredRuns = useMemo(() => {
    const f = filter === 'all' ? runs : runs.filter(r => r.status === filter);
    return f.slice(0, showCount);
  }, [runs, filter, showCount]);
  const totalFiltered = filter === 'all' ? runs.length : runs.filter(r => r.status === filter).length;

  const handleSubmit = async () => {
    if (!suggestion.trim()) return;
    setSubmitState('submitting');
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
    <div className="h-full overflow-auto">

      {/* ── Hero ──────────────────────────────────────── */}
      <section className="relative overflow-hidden">
        <div className="absolute inset-0 bg-gradient-to-b from-[var(--temper-accent)]/5 via-transparent to-transparent pointer-events-none" />

        <div className="max-w-4xl mx-auto px-8 pt-16 pb-8 text-center relative">
          <div className="flex items-center justify-center gap-2 mb-8">
            <StatusDot status={health} />
            <span className="text-xs text-[var(--temper-text-muted)]">
              {health === 'ok' ? 'Live' : health === 'error' ? 'Offline' : '...'}
            </span>
          </div>

          <h1 className="text-4xl font-bold tracking-tight text-[var(--temper-text)]">
            Describe a change.<br />
            <span className="text-[var(--temper-accent)]">Watch AI build it.</span>
          </h1>
          <p className="text-lg text-[var(--temper-text-muted)] mt-4 max-w-xl mx-auto leading-relaxed">
            Type what you want changed on this website. AI agents will validate, plan, code, test, review, and deploy it — automatically.
          </p>

          <PipelineAnimation />

          {stats.total > 0 && (
            <div className="flex gap-8 justify-center text-center mt-2">
              <div>
                <div className="text-2xl font-bold text-emerald-400">{stats.completed}</div>
                <div className="text-xs text-[var(--temper-text-dim)]">changes shipped</div>
              </div>
              <div>
                <div className="text-2xl font-bold text-[var(--temper-text)]">8</div>
                <div className="text-xs text-[var(--temper-text-dim)]">pipeline stages</div>
              </div>
              <div>
                <div className="text-2xl font-bold text-[var(--temper-text)]">21</div>
                <div className="text-xs text-[var(--temper-text-dim)]">AI agents</div>
              </div>
            </div>
          )}
        </div>
      </section>

      {/* ── Suggest ───────────────────────────────────── */}
      <section id="suggest" className="max-w-2xl mx-auto px-8 py-10">
        <div className="bg-[var(--temper-surface)] border border-[var(--temper-border)] rounded-xl p-6">
          <h2 className="text-base font-semibold text-[var(--temper-text)] mb-1">
            What would you like to change?
          </h2>
          <p className="text-sm text-[var(--temper-text-dim)] mb-4">
            Describe any visual or functional change. The AI pipeline handles the rest.
          </p>

          <textarea
            className="w-full bg-[var(--temper-bg)] border border-[var(--temper-border)] rounded-lg px-4 py-3 text-sm text-[var(--temper-text)] placeholder-[var(--temper-text-dim)] resize-none focus:outline-none focus:border-[var(--temper-accent)] transition-colors"
            placeholder='e.g. "Add a gradient banner at the top that says Powered by AI"'
            value={suggestion}
            onChange={(e) => setSuggestion(e.target.value)}
            rows={3}
            disabled={submitState === 'submitting'}
          />

          <div className="flex justify-between items-center mt-3">
            <p className="text-xs text-[var(--temper-text-dim)]">
              Changes deploy to this live site in ~7 minutes
            </p>
            <button
              className="bg-[var(--temper-accent)] text-black rounded-lg px-6 py-2 text-sm font-medium hover:opacity-85 disabled:opacity-40 disabled:cursor-not-allowed transition-opacity"
              onClick={handleSubmit}
              disabled={!suggestion.trim() || submitState === 'submitting'}
            >
              {submitState === 'submitting' ? 'Sending...' : 'Submit'}
            </button>
          </div>

          {submitMessage && (
            <div className={`mt-3 text-sm px-3 py-2 rounded-md ${submitState === 'success' ? 'bg-emerald-950 text-emerald-400' : 'bg-red-950 text-red-400'}`}>
              {submitMessage}
            </div>
          )}

          <div className="mt-4 pt-4 border-t border-[var(--temper-border)]">
            <p className="text-xs text-[var(--temper-text-dim)] mb-2">Try an example:</p>
            <div className="flex flex-wrap gap-2">
              {EXAMPLE_SUGGESTIONS.map((ex) => (
                <button
                  key={ex}
                  onClick={() => setSuggestion(ex)}
                  className="text-xs px-3 py-1.5 rounded-full bg-[var(--temper-bg)] border border-[var(--temper-border)] text-[var(--temper-text-muted)] hover:text-[var(--temper-text)] hover:border-[var(--temper-accent)]/50 transition-colors truncate max-w-[280px]"
                >
                  {ex}
                </button>
              ))}
            </div>
          </div>
        </div>
      </section>

      {/* ── Recent changes ────────────────────────────── */}
      <section className="max-w-4xl mx-auto px-8 py-8 pb-16">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-sm font-semibold text-[var(--temper-text-muted)] uppercase tracking-wide">
            Recent Changes
          </h2>
          <div className="flex gap-3">
            {(['all', 'completed', 'failed'] as const).map((tab) => {
              const count = tab === 'all' ? runs.length : runs.filter(r => r.status === tab).length;
              return (
                <button
                  key={tab}
                  onClick={() => { setFilter(tab); setShowCount(8); }}
                  className={`text-xs font-medium transition-colors ${
                    filter === tab ? 'text-[var(--temper-text)]' : 'text-[var(--temper-text-dim)] hover:text-[var(--temper-text-muted)]'
                  }`}
                >
                  {tab === 'all' ? `All (${count})` : tab === 'completed' ? `✓ Shipped (${count})` : `✗ Rejected (${count})`}
                </button>
              );
            })}
          </div>
        </div>

        {loading ? (
          <div className="grid grid-cols-2 gap-3">
            {[1, 2, 3, 4].map(i => (
              <div key={i} className="bg-[var(--temper-surface)] border border-[var(--temper-border)] rounded-lg p-4 h-24">
                <div className="skeleton h-4 w-3/4" />
                <div className="skeleton h-3 w-1/2 mt-3" />
              </div>
            ))}
          </div>
        ) : filteredRuns.length === 0 ? (
          <div className="text-center py-16 text-[var(--temper-text-muted)]">
            {filter === 'all' ? 'No changes yet. Submit a suggestion above!' : `No ${filter} changes.`}
          </div>
        ) : (
          <>
            <div className="grid grid-cols-2 gap-3">
              {filteredRuns.map((run) => {
                const clickable = isClickable(run);
                const isCompleted = run.status === 'completed';
                const isFailed = run.status === 'failed';
                const isRunning = run.status === 'running' || run.status === 'claimed';
                const task = (run.inputs as Record<string, unknown>)?.task_description as string || run.workflow;

                return (
                  <div
                    key={run.id}
                    className={`bg-[var(--temper-surface)] border rounded-lg p-4 transition-all ${
                      isCompleted ? 'border-emerald-500/30 hover:border-emerald-500/60' :
                      isFailed ? 'border-red-500/20 hover:border-red-500/40' :
                      isRunning ? 'border-[var(--temper-accent)]/30 hover:border-[var(--temper-accent)]/60' :
                      'border-[var(--temper-border)] hover:border-[var(--temper-accent)]/30'
                    } ${clickable ? 'cursor-pointer' : ''}`}
                    onClick={() => clickable && navigate(`/runs/${run.id}`)}
                  >
                    <div className="flex items-start gap-2">
                      <span className={`text-sm mt-0.5 ${
                        isCompleted ? 'text-emerald-400' :
                        isFailed ? 'text-red-400' :
                        isRunning ? 'text-[var(--temper-accent)] animate-pulse' :
                        'text-[var(--temper-text-dim)]'
                      }`}>
                        {isCompleted ? '✓' : isFailed ? '✗' : isRunning ? '●' : '○'}
                      </span>
                      <div className="min-w-0 flex-1">
                        <p className="text-sm text-[var(--temper-text)] line-clamp-2 leading-snug">
                          {task}
                        </p>
                        <p className="text-xs text-[var(--temper-text-dim)] mt-2">
                          {formatDuration(run.duration_seconds)}
                          {run.duration_seconds ? ' · ' : ''}
                          {formatTimeAgo(run.created_at)}
                        </p>
                      </div>
                    </div>
                  </div>
                );
              })}
            </div>

            {showCount < totalFiltered && (
              <button
                onClick={() => setShowCount(c => c + 8)}
                className="mt-4 w-full text-center text-xs text-[var(--temper-text-muted)] hover:text-[var(--temper-text)] py-2 border border-[var(--temper-border)] rounded-lg hover:bg-[var(--temper-surface)] transition-colors"
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

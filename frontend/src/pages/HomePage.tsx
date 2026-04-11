import React, { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { fetchHealth, fetchRuns, submitSuggestion, fetchTypewriterConfig, fetchBackToTopConfig, type Run, type TypewriterConfig, type BackToTopConfig } from '../api';
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

type RunOutcome = 'deployed' | 'rejected' | 'failed' | 'running' | 'pending';

function getOutcome(run: Run): RunOutcome {
  if (run.status === 'running' || run.status === 'claimed') return 'running';
  if (run.status === 'pending') return 'pending';
  if (run.status === 'failed') return 'failed';
  // Check workflow_output for business-level result
  const wo = run.workflow_output;
  if (wo?.result === 'REJECT' || wo?.result === 'reject') return 'rejected';
  if (run.status === 'completed') return 'deployed';
  return 'pending';
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
              className={`w-10 h-10 rounded-full flex items-center justify-center text-xs font-bold transition-[transform,colors,opacity] duration-300 ${
                i < active ? 'bg-emerald-500/20 text-emerald-400 border-2 border-emerald-500/50' :
                i === active ? 'bg-[var(--temper-accent)]/20 text-[var(--temper-accent)] border-2 border-[var(--temper-accent)] scale-110 animate-pulse-glow' :
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

const EXAMPLE_SUGGESTIONS_POOL = [
  '🎨 Add a gradient banner at the top of the page that says "Powered by AI"',
  '✨ Add a confetti animation that triggers when viewing a completed run',
  '🌙 Add a greeting message in the header that changes based on time of day',
  '📊 Show a mini chart on the homepage that visualizes the success rate',
  '🎯 Add a pulsing "Live" indicator next to running suggestions',
  '📱 Make the run cards stack into a single column on mobile screens',
  '🏷️ Add category tags to each run card like UI, API, or Docs',
  '🖼️ Add an animated SVG background behind the hero section',
  '💬 Show a random fun fact about AI on the homepage footer',
  '⏱️ Show a live elapsed-time counter on running pipeline cards',
  '🔍 Add a search bar that filters runs by keyword',
  '📋 Add a copy suggestion button next to each run description',
  '🌈 Let users toggle between light mode and dark mode',
  '📈 Add a sparkline showing deployments over the past 24 hours',
  '🤖 Add a small dancing robot animation in the footer',
  '🎉 Show a party popper emoji burst when a suggestion is submitted',
  '⭐ Add a star button on each run card to bookmark favorites',
  '🔔 Add a subtle notification sound when a new run completes',
];

function pickRandom<T>(pool: T[], count: number): T[] {
  const copy = [...pool];
  for (let i = copy.length - 1; i > 0; i--) {
    const j = Math.floor(Math.random() * (i + 1));
    [copy[i], copy[j]] = [copy[j], copy[i]];
  }
  return copy.slice(0, count);
}

// ── Hero quotes ───────────────────────────────────────────

const HERO_QUOTES = [
  { text: "Any fool can write code that a computer can understand. Good programmers write code that humans can understand.", author: "Kent Beck" },
  { text: "Make it work, make it right, make it fast.", author: "Kent Beck" },
  { text: "The best way to predict the future is to implement it.", author: "David Heinemeier Hansson" },
  { text: "First, solve the problem. Then, write the code.", author: "John Johnson" },
  { text: "I'm not a great programmer; I'm just a good programmer with great habits.", author: "Kent Beck" },
  { text: "Before software can be reusable it first has to be usable.", author: "Ralph Johnson" },
  { text: "Continuous improvement is better than delayed perfection.", author: "Mark Twain" },
  { text: "Code is like humor. When you have to explain it, it's bad.", author: "Cory House" },
];

// ── Cache ──────────────────────────────────────────────────

const CACHE_KEY = 'sdlc-runs-cache';
function getCached(): Run[] { try { return JSON.parse(sessionStorage.getItem(CACHE_KEY) || '[]'); } catch { return []; } }
function setCache(r: Run[]) { try { sessionStorage.setItem(CACHE_KEY, JSON.stringify(r)); } catch {} }

// ── Animated checkmark ────────────────────────────────────

function AnimatedCheckmark() {
  return (
    <svg className="w-5 h-5 shrink-0" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
      <circle className="animate-checkmark-circle" cx="12" cy="12" r="11" stroke="#34d399" strokeWidth="2" fill="#34d399" fillOpacity="0.1" />
      <path className="animate-checkmark-draw" d="M7 13l3 3 7-7" stroke="#34d399" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round" />
    </svg>
  );
}

// ── Typewriter heading ───────────────────────────────────

function TypewriterHeading({ lines, speedMs, startDelayMs }: {
  lines: { text: string; css_class: string }[];
  speedMs: number;
  startDelayMs: number;
}) {
  const totalChars = lines.reduce((sum, l) => sum + l.text.length, 0);
  const [charCount, setCharCount] = useState(0);
  const [isDone, setIsDone] = useState(false);

  useEffect(() => {
    if (window.matchMedia('(prefers-reduced-motion: reduce)').matches) {
      setCharCount(totalChars);
      setIsDone(true);
      return;
    }
    let intervalId: number;
    const timeoutId = window.setTimeout(() => {
      intervalId = window.setInterval(() => {
        setCharCount(prev => {
          const next = prev + 1;
          if (next >= totalChars) {
            clearInterval(intervalId);
            setIsDone(true);
            return totalChars;
          }
          return next;
        });
      }, speedMs);
    }, startDelayMs);
    return () => {
      clearTimeout(timeoutId);
      if (intervalId) clearInterval(intervalId);
    };
  }, [totalChars, speedMs, startDelayMs]);

  const fullText = lines.map(l => l.text).join(' ');
  let consumed = 0;
  return (
    <h1 className="text-4xl font-bold tracking-tight text-[var(--temper-text)]" aria-label={fullText} style={{ minHeight: '4.5rem' }}>
      {lines.map((line, i) => {
        const start = consumed;
        consumed += line.text.length;
        const visible = Math.max(0, Math.min(line.text.length, charCount - start));
        const segment = line.text.slice(0, visible);
        return (
          <span key={i}>
            {i > 0 && <br />}
            <span className={line.css_class === 'accent' ? 'text-[var(--temper-accent)]' : undefined}>
              {segment}
            </span>
          </span>
        );
      })}
      {!isDone && <span className="typewriter-cursor">|</span>}
    </h1>
  );
}

// ── Status priority ───────────────────────────────────────

const STATUS_PRIORITY: Record<RunOutcome, number> = { running: 0, pending: 1, deployed: 2, rejected: 3, failed: 4 };

// ── Main ───────────────────────────────────────────────────

export function HomePage() {
  const navigate = useNavigate();
  const [health, setHealth] = useState<string>('loading');
  const [runs, setRuns] = useState<Run[]>(getCached);
  const [loading, setLoading] = useState(runs.length === 0);
  const [suggestion, setSuggestion] = useState('');
  const [submitState, setSubmitState] = useState<'idle' | 'submitting' | 'success' | 'error'>('idle');
  const [submitMessage, setSubmitMessage] = useState('');
  const [filter, setFilter] = useState<'all' | 'deployed' | 'rejected' | 'failed'>('all');
  const [showCount, setShowCount] = useState(8);
  const [typewriterConfig, setTypewriterConfig] = useState<TypewriterConfig | null>(null);
  const scrollRef = useRef<HTMLDivElement>(null);
  const [showBackToTop, setShowBackToTop] = useState(false);
  const [backToTopConfig, setBackToTopConfig] = useState<BackToTopConfig | null>(null);
  const exampleSuggestions = useMemo(() => pickRandom(EXAMPLE_SUGGESTIONS_POOL, 5), []);
  const [quoteIndex, setQuoteIndex] = useState(() => Math.floor(Math.random() * HERO_QUOTES.length));
  useEffect(() => {
    const timer = setInterval(() => setQuoteIndex(i => (i + 1) % HERO_QUOTES.length), 12_000);
    return () => clearInterval(timer);
  }, []);

  useEffect(() => {
    fetchHealth().then(() => setHealth('ok')).catch(() => setHealth('error'));
    fetchTypewriterConfig().then(setTypewriterConfig).catch(() => {});
    fetchBackToTopConfig().then(setBackToTopConfig).catch(() => {});
    fetchRuns().then((d) => { const r = d?.runs ?? []; setRuns(r); setCache(r); setLoading(false); }).catch(() => setLoading(false));
    const interval = setInterval(() => {
      fetchRuns().then((d) => { const r = d?.runs ?? []; setRuns(r); setCache(r); }).catch(() => {});
    }, 5000);
    return () => clearInterval(interval);
  }, []);

  useEffect(() => {
    if (!backToTopConfig?.enabled || !scrollRef.current) return;
    const el = scrollRef.current;
    const threshold = backToTopConfig.scroll_threshold_px;
    let ticking = false;
    const onScroll = () => {
      if (!ticking) {
        ticking = true;
        requestAnimationFrame(() => {
          setShowBackToTop(el.scrollTop > threshold);
          ticking = false;
        });
      }
    };
    el.addEventListener('scroll', onScroll, { passive: true });
    return () => el.removeEventListener('scroll', onScroll);
  }, [backToTopConfig]);

  const scrollToTop = useCallback(() => {
    scrollRef.current?.scrollTo({ top: 0, behavior: backToTopConfig?.scroll_behavior ?? 'smooth' });
  }, [backToTopConfig]);

  const stats = useMemo(() => {
    const outcomes = runs.map(r => getOutcome(r));
    const deployed = outcomes.filter(o => o === 'deployed').length;
    const rejected = outcomes.filter(o => o === 'rejected').length;
    const failed = outcomes.filter(o => o === 'failed').length;
    return { total: runs.length, deployed, rejected, failed };
  }, [runs]);

  const filteredRuns = useMemo(() => {
    const f = filter === 'all' ? runs : runs.filter(r => getOutcome(r) === filter);
    const sorted = [...f].sort((a, b) => {
      const pa = STATUS_PRIORITY[getOutcome(a)];
      const pb = STATUS_PRIORITY[getOutcome(b)];
      if (pa !== pb) return pa - pb;
      return new Date(b.created_at).getTime() - new Date(a.created_at).getTime();
    });
    return sorted.slice(0, showCount);
  }, [runs, filter, showCount]);
  const totalFiltered = filter === 'all' ? runs.length : runs.filter(r => getOutcome(r) === filter).length;

  const handleSubmit = async () => {
    if (!suggestion.trim()) return;
    setSubmitState('submitting');
    try {
      const result = await submitSuggestion(suggestion);
      setSubmitState('success');
      setSubmitMessage(result.message || 'Suggestion submitted successfully');
      setSuggestion('');
      setTimeout(() => { setSubmitState('idle'); setSubmitMessage(''); }, 5000);
    } catch (err) {
      setSubmitState('error');
      setSubmitMessage(err instanceof Error ? err.message : 'Something went wrong');
      setTimeout(() => { setSubmitState('idle'); setSubmitMessage(''); }, 5000);
    }
  };

  return (
    <div className="relative h-full">
    <div ref={scrollRef} className="h-full overflow-auto">

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

          {typewriterConfig ? (
            <TypewriterHeading
              lines={typewriterConfig.lines}
              speedMs={typewriterConfig.speed_ms}
              startDelayMs={typewriterConfig.start_delay_ms}
            />
          ) : (
            <h1 className="text-4xl font-bold tracking-tight text-[var(--temper-text)]">
              Describe a change.<br />
              <span className="text-[var(--temper-accent)]">Watch AI build it.</span>
            </h1>
          )}
          <p className="text-lg text-[var(--temper-text-muted)] mt-4 max-w-xl mx-auto leading-relaxed">
            Type what you want changed on this website. AI agents will validate, plan, code, test, review, and deploy it — automatically.
          </p>
          <PipelineAnimation />

          {stats.total > 0 && (
            <div className="flex gap-8 justify-center text-center mt-2">
              <div>
                <div className="text-2xl font-bold text-emerald-400">{stats.deployed}</div>
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

          <p key={quoteIndex} className="text-sm italic text-[var(--temper-text-dim)] mt-6 max-w-lg mx-auto animate-fade-in">
            "{HERO_QUOTES[quoteIndex].text}"
            <span className="not-italic ml-2 text-[var(--temper-text-muted)]">— {HERO_QUOTES[quoteIndex].author}</span>
          </p>
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
            <div
              role="status"
              className={`mt-3 text-sm px-3 py-2 rounded-md flex items-center gap-2 ${submitState === 'success' ? 'bg-emerald-950 text-emerald-400' : 'bg-red-950 text-red-400'}`}
            >
              {submitState === 'success' && <AnimatedCheckmark />}
              {submitMessage}
            </div>
          )}

          <div className="mt-4 pt-4 border-t border-[var(--temper-border)]">
            <p className="text-xs text-[var(--temper-text-dim)] mb-2">Try an example:</p>
            <div className="flex flex-wrap gap-2">
              {exampleSuggestions.map((ex) => (
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
            {(['all', 'deployed', 'rejected', 'failed'] as const).map((tab) => {
              const count = tab === 'all' ? runs.length : runs.filter(r => getOutcome(r) === tab).length;
              const labels: Record<string, string> = {
                all: `All (${count})`,
                deployed: `✓ Shipped (${count})`,
                rejected: `⊘ Rejected (${count})`,
                failed: `✗ Failed (${count})`,
              };
              return (
                <button
                  key={tab}
                  onClick={() => { setFilter(tab); setShowCount(8); }}
                  className={`text-xs font-medium transition-colors pb-1 ${
                    filter === tab
                      ? 'text-[var(--temper-text)] border-b-2 border-[var(--temper-accent)]'
                      : 'text-[var(--temper-text-dim)] hover:text-[var(--temper-text-muted)] border-b-2 border-transparent'
                  }`}
                >
                  {labels[tab]}
                </button>
              );
            })}
          </div>
        </div>

        {loading ? (
          <div className="grid grid-cols-2 gap-3" role="status" aria-busy="true">
            <span className="sr-only">Loading recent changes</span>
            {Array.from({length: 8}, (_, i) => (
              <div key={i} className="bg-[var(--temper-surface)] border border-l-[3px] border-[var(--temper-border)] rounded-lg p-4">
                <div className="flex items-start gap-2">
                  <div className="skeleton w-4 h-4 rounded-full mt-0.5 shrink-0" />
                  <div className="min-w-0 flex-1">
                    <div className="skeleton h-4 w-3/4" />
                    <div className="skeleton h-4 w-1/2 mt-1" />
                    <div className="skeleton h-3 w-2/5 mt-3" />
                  </div>
                </div>
              </div>
            ))}
          </div>
        ) : filteredRuns.length === 0 ? (
          <div className="text-center py-16 text-[var(--temper-text-muted)]">
            {filter === 'all' ? 'No changes yet. Submit a suggestion above!' : `No ${filter} changes.`}
          </div>
        ) : (
          <>
            {filter === 'all' && filteredRuns.some(r => getOutcome(r) === 'running') && (
              <div className="flex items-center gap-2 mb-3">
                <span className="inline-block w-2 h-2 rounded-full bg-[var(--temper-accent)] animate-pulse" />
                <span className="text-xs font-medium text-[var(--temper-accent)]">Running now</span>
                <div className="flex-1 h-px bg-[var(--temper-border)]" />
              </div>
            )}
            <div className="grid grid-cols-2 gap-4">
              {filteredRuns.map((run, index) => {
                const clickable = isClickable(run);
                const outcome = getOutcome(run);
                const task = (run.inputs as Record<string, unknown>)?.task_description as string || run.workflow;

                const pendingRuns = filteredRuns.filter(r => getOutcome(r) === 'pending');
                const queuePos = outcome === 'pending' ? pendingRuns.indexOf(run) + 1 : 0;

                const styles: Record<RunOutcome, { border: string; leftBorder: string; icon: string; iconColor: string }> = {
                  deployed: { border: 'border-emerald-500/30 hover:border-emerald-500/60', leftBorder: 'border-l-emerald-500', icon: '✓', iconColor: 'text-emerald-400' },
                  rejected: { border: 'border-amber-500/30 hover:border-amber-500/50', leftBorder: 'border-l-amber-500', icon: '⊘', iconColor: 'text-amber-400' },
                  failed: { border: 'border-red-500/20 hover:border-red-500/40', leftBorder: 'border-l-red-500', icon: '✗', iconColor: 'text-red-400' },
                  running: { border: 'border-[var(--temper-accent)]/30 hover:border-[var(--temper-accent)]/60', leftBorder: 'border-l-[var(--temper-accent)]', icon: '●', iconColor: 'text-[var(--temper-accent)] animate-pulse' },
                  pending: { border: 'border-[var(--temper-border)]', leftBorder: 'border-l-[var(--temper-border)]', icon: '○', iconColor: 'text-[var(--temper-text-dim)]' },
                };
                const s = styles[outcome];

                const prevOutcome = index > 0 ? getOutcome(filteredRuns[index - 1]) : null;
                const showPendingHeader = filter === 'all' && outcome === 'pending' && prevOutcome !== 'pending';
                const showCompletedHeader = filter === 'all' && outcome !== 'running' && outcome !== 'pending'
                  && (prevOutcome === 'running' || prevOutcome === 'pending');

                return (
                  <React.Fragment key={run.id}>
                    {showPendingHeader && (
                      <div className="col-span-2 flex items-center gap-2 mt-2 mb-1">
                        <span className="text-xs font-medium text-[var(--temper-text-dim)]">Queue ({pendingRuns.length})</span>
                        <div className="flex-1 h-px bg-[var(--temper-border)]" />
                      </div>
                    )}
                    {showCompletedHeader && (
                      <div className="col-span-2 flex items-center gap-2 mt-2 mb-1">
                        <span className="text-xs font-medium text-[var(--temper-text-dim)]">Completed</span>
                        <div className="flex-1 h-px bg-[var(--temper-border)]" />
                      </div>
                    )}
                    <div
                      className={`bg-[var(--temper-surface)] border rounded-lg p-5 transition-all duration-200 animate-fade-in ${
                        outcome === 'running'
                          ? 'border-l-[4px] border-[var(--temper-accent)]/40 border-l-[var(--temper-accent)] shadow-[0_0_12px_rgba(125,211,252,0.1)]'
                          : `border-l-[3px] ${s.border} ${s.leftBorder}`
                      } ${clickable ? 'cursor-pointer hover:-translate-y-0.5 hover:shadow-md hover:shadow-black/20' : ''}`}
                      style={{ animationDelay: `${index * 50}ms`, animationFillMode: 'backwards' }}
                      onClick={() => clickable && navigate(`/runs/${run.id}`)}
                    >
                      <div className="flex items-start gap-2">
                        <span className={`flex items-center justify-center w-5 h-5 rounded-full text-xs shrink-0 mt-0.5 ${
                          outcome === 'deployed' ? 'bg-emerald-500/20 text-emerald-400' :
                          outcome === 'rejected' ? 'bg-amber-500/20 text-amber-400' :
                          outcome === 'failed' ? 'bg-red-500/20 text-red-400' :
                          outcome === 'running' ? 'bg-[var(--temper-accent)]/20 text-[var(--temper-accent)] animate-pulse' :
                          'bg-[var(--temper-border)] text-[var(--temper-text-dim)]'
                        }`}>{outcome === 'pending' ? `#${queuePos}` : s.icon}</span>
                        <div className="min-w-0 flex-1">
                          <p className="text-sm text-[var(--temper-text)] line-clamp-2 leading-snug">
                            {task}
                          </p>
                          {outcome === 'rejected' && run.workflow_output?.reason && (
                            <p className="text-xs text-amber-400/70 mt-1 line-clamp-1">
                              {run.workflow_output.reason}
                            </p>
                          )}
                          <p className="text-xs text-[var(--temper-text-dim)] mt-2">
                            {outcome === 'pending' ? `Queue position #${queuePos}` :
                             outcome === 'running' ? 'Processing...' :
                             `${formatDuration(run.duration_seconds)}${run.duration_seconds ? ' · ' : ''}`}
                            {outcome !== 'pending' && formatTimeAgo(run.created_at)}
                          </p>
                        </div>
                      </div>
                    </div>
                  </React.Fragment>
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

      {/* ── About ─────────────────────────────────────── */}
      <section className="max-w-3xl mx-auto px-8 py-12 pb-20">
        <div className="border-t border-[var(--temper-border)] pt-10">
          <h2 className="text-sm font-semibold text-[var(--temper-text-muted)] uppercase tracking-wide mb-6">
            About This Experiment
          </h2>

          <div className="space-y-4 text-sm text-[var(--temper-text-muted)] leading-relaxed">
            <p>
              This site is a live experiment in <span className="text-[var(--temper-text)]">fully autonomous software development</span>.
              Every suggestion you submit goes through a 10-stage AI pipeline that mirrors how a real engineering team works —
              from triage and feasibility analysis, through architecture and planning, to implementation, code review, testing,
              and production deployment.
            </p>

            <p>
              There is no human in the loop. The entire process — validating the idea, writing tests first, implementing the code,
              reviewing for quality and security, pushing to GitHub, and deploying to this live site — is handled by{' '}
              <span className="text-[var(--temper-text)]">21 specialized AI agents</span> coordinated through a multi-stage workflow.
            </p>

            <div className="bg-[var(--temper-surface)] border border-[var(--temper-border)] rounded-lg p-4 my-4">
              <p className="text-xs text-[var(--temper-text-dim)] font-medium uppercase tracking-wide mb-3">The Pipeline</p>
              <div className="grid grid-cols-2 gap-x-6 gap-y-1.5 text-xs">
                <div><span className="text-[var(--temper-accent)]">1.</span> <span className="text-[var(--temper-text)]">Validate</span> — 5 agents assess feasibility, safety, threats, code impact, and scope</div>
                <div><span className="text-[var(--temper-accent)]">2.</span> <span className="text-[var(--temper-text)]">Dedup</span> — checks if the suggestion duplicates previous work</div>
                <div><span className="text-[var(--temper-accent)]">3.</span> <span className="text-[var(--temper-text)]">Clone</span> — clones the repository into a fresh workspace</div>
                <div><span className="text-[var(--temper-accent)]">4.</span> <span className="text-[var(--temper-text)]">Analyze</span> — reads the codebase to understand existing patterns</div>
                <div><span className="text-[var(--temper-accent)]">5.</span> <span className="text-[var(--temper-text)]">Plan</span> — architect designs the approach, critic reviews it</div>
                <div><span className="text-[var(--temper-accent)]">6.</span> <span className="text-[var(--temper-text)]">Build</span> — writes tests first, then implements the feature</div>
                <div><span className="text-[var(--temper-accent)]">7.</span> <span className="text-[var(--temper-text)]">Review</span> — syntax check, test runner, diff review, security scan</div>
                <div><span className="text-[var(--temper-accent)]">8.</span> <span className="text-[var(--temper-text)]">Push</span> — commits to GitHub and deploys to Heroku</div>
                <div><span className="text-[var(--temper-accent)]">9.</span> <span className="text-[var(--temper-text)]">Verify</span> — health check and post-deploy verification</div>
                <div><span className="text-[var(--temper-accent)]">10.</span> <span className="text-[var(--temper-text)]">Cleanup</span> — removes the temporary workspace</div>
              </div>
            </div>

            <p>
              The goal is to explore what happens when you give AI agents the full software development lifecycle —
              not just code generation, but the entire process of deciding <em>what</em> to build, <em>how</em> to build it,
              and <em>whether</em> it should ship. Some suggestions get rejected by the safety reviewers. Some fail code review.
              Some make it all the way to production. That's the experiment.
            </p>

            <p className="text-[var(--temper-text-dim)]">
              Built with <a href="https://github.com/shine2lay/temper-ai" target="_blank" rel="noopener noreferrer" className="text-[var(--temper-accent)] hover:underline">Temper AI</a> —
              an open-source multi-agent workflow orchestration engine.
            </p>
          </div>
        </div>
      </section>
    </div>
    {showBackToTop && backToTopConfig && (
      <button
        onClick={scrollToTop}
        aria-label="Back to top"
        className="absolute z-40 flex items-center justify-center shadow-lg transition-opacity duration-200 hover:shadow-xl focus:outline-none focus:ring-2 focus:ring-[var(--temper-accent)] back-to-top-enter"
        style={{
          right: backToTopConfig.position_right_px,
          bottom: backToTopConfig.position_bottom_px,
          width: backToTopConfig.size_px,
          height: backToTopConfig.size_px,
          backgroundColor: backToTopConfig.bg_color,
          borderRadius: backToTopConfig.border_radius,
          color: backToTopConfig.icon_color,
          transition: `background-color ${backToTopConfig.transition_ms}ms ease`,
        }}
        onMouseEnter={e => (e.currentTarget.style.backgroundColor = backToTopConfig.hover_bg_color)}
        onMouseLeave={e => (e.currentTarget.style.backgroundColor = backToTopConfig.bg_color)}
      >
        <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
          <path d="M18 15l-6-6-6 6"/>
        </svg>
      </button>
    )}
    </div>
  );
}

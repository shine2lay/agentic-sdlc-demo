import { useCallback, useEffect, useRef, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { ArrowLeft } from 'lucide-react';
import { fetchRun } from '../api';
import { ExecutionView } from '../execution/ExecutionView';
import type { WorkflowExecution } from '../execution/types';

const POLL_INTERVAL_MS = 5000;

export function RunPage() {
  const { runId } = useParams<{ runId: string }>();
  const navigate = useNavigate();
  const [execution, setExecution] = useState<WorkflowExecution | null>(null);
  const [runStatus, setRunStatus] = useState<string | null>(null);
  const [runError, setRunError] = useState<string | null>(null);
  const [fetchError, setFetchError] = useState<string | null>(null);
  const pollRef = useRef<ReturnType<typeof setInterval>>(undefined);

  const stopPolling = useCallback(() => {
    if (pollRef.current) {
      clearInterval(pollRef.current);
      pollRef.current = undefined;
    }
  }, []);

  const loadRun = useCallback(async (id: string): Promise<boolean> => {
    try {
      const run = await fetchRun(id);
      setRunStatus(run.status);
      setRunError(run.error ?? null);

      const result = run.result as Record<string, unknown> | null;
      if (result?.execution) {
        setExecution(result.execution as WorkflowExecution);
      }

      // Stop polling if run reached a terminal state
      const isTerminal = run.status === 'completed' || run.status === 'failed';
      return isTerminal;
    } catch (err) {
      setFetchError(err instanceof Error ? err.message : 'Failed to load');
      return true; // stop polling on fetch error
    }
  }, []);

  useEffect(() => {
    if (!runId) return;

    setExecution(null);
    setRunStatus(null);
    setRunError(null);
    setFetchError(null);

    loadRun(runId).then((done) => {
      if (done) return;
      // Poll until terminal state
      pollRef.current = setInterval(async () => {
        const finished = await loadRun(runId);
        if (finished) stopPolling();
      }, POLL_INTERVAL_MS);
    });

    return stopPolling;
  }, [runId, loadRun, stopPolling]);

  if (fetchError) {
    return (
      <div className="flex flex-col items-center justify-center h-full gap-4 text-[var(--temper-text-muted)]">
        <p className="text-red-400">{fetchError}</p>
        <button
          onClick={() => navigate('/')}
          className="text-sm text-[var(--temper-accent)] hover:underline"
        >
          Back to runs
        </button>
      </div>
    );
  }

  // Show execution view as soon as we have any execution data
  // (partial snapshots during running, or full data when complete)
  if (execution) {
    return (
      <ExecutionView
        key={`${runId}-${execution.status}`}
        execution={execution}
        onClose={() => navigate('/')}
      />
    );
  }

  // No execution data yet — show loading/waiting state
  const isActive = runStatus === 'running' || runStatus === 'claimed' || runStatus === 'pending';
  const isFailed = runStatus === 'failed';

  return (
    <div className="flex flex-col h-full bg-[var(--temper-bg)]">
      <header className="flex items-center gap-4 bg-gray-900 px-4 py-3 border-b border-gray-700/60 shrink-0">
        <button
          onClick={() => navigate('/')}
          className="text-gray-400 hover:text-gray-200 transition-colors"
        >
          <ArrowLeft className="w-5 h-5" />
        </button>
        <span className="text-sm text-gray-400">
          {runId?.slice(0, 8)}
        </span>
        {runStatus && (
          <span className={`text-xs font-medium px-2 py-0.5 rounded border ${
            isFailed ? 'bg-red-900/50 text-red-400 border-red-700/50' :
            runStatus === 'running' ? 'bg-blue-900/50 text-blue-400 border-blue-700/50' :
            runStatus === 'claimed' ? 'bg-blue-900/50 text-blue-400 border-blue-700/50' :
            runStatus === 'completed' ? 'bg-emerald-900/50 text-emerald-400 border-emerald-700/50' :
            'bg-yellow-900/50 text-yellow-400 border-yellow-700/50'
          }`}>
            {runStatus}
          </span>
        )}
      </header>
      <div className="flex-1 flex items-center justify-center">
        <div className="flex flex-col items-center gap-3 max-w-md px-4 text-center">
          {isActive ? (
            <>
              <div className="w-8 h-8 border-2 border-[var(--temper-accent)] border-t-transparent rounded-full animate-spin" />
              <span className="text-sm text-[var(--temper-text-muted)]">
                Pipeline is {runStatus}...
              </span>
              <span className="text-xs text-[var(--temper-text-dim)]">
                Execution view will appear as stages complete
              </span>
            </>
          ) : isFailed ? (
            <>
              <span className="text-3xl">&#x2717;</span>
              <span className="text-sm text-red-400">Pipeline failed</span>
              {runError && (
                <span className="text-xs text-red-400/70 font-mono">{runError}</span>
              )}
            </>
          ) : (
            <>
              <div className="skeleton h-8 w-8 rounded-full" />
              <span className="text-sm text-[var(--temper-text-muted)]">Loading...</span>
            </>
          )}
        </div>
      </div>
    </div>
  );
}

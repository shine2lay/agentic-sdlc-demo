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
  const [error, setError] = useState<string | null>(null);
  const pollRef = useRef<ReturnType<typeof setInterval>>(undefined);

  const loadRun = useCallback(async (id: string) => {
    try {
      const run = await fetchRun(id);
      setRunStatus(run.status);
      const result = run.result as Record<string, unknown> | null;
      if (result?.execution) {
        setExecution(result.execution as WorkflowExecution);
        return true; // done — stop polling
      }
      return false; // no execution yet
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load');
      return true; // stop polling on error
    }
  }, []);

  useEffect(() => {
    if (!runId) return;

    setExecution(null);
    setRunStatus(null);
    setError(null);

    // Initial fetch
    loadRun(runId).then((done) => {
      if (done) return;
      // Poll for running/pending runs until execution is available
      pollRef.current = setInterval(async () => {
        const finished = await loadRun(runId);
        if (finished && pollRef.current) {
          clearInterval(pollRef.current);
          pollRef.current = undefined;
        }
      }, POLL_INTERVAL_MS);
    });

    return () => {
      if (pollRef.current) {
        clearInterval(pollRef.current);
        pollRef.current = undefined;
      }
    };
  }, [runId, loadRun]);

  if (error) {
    return (
      <div className="flex flex-col items-center justify-center h-full gap-4 text-[var(--temper-text-muted)]">
        <p className="text-red-400">{error}</p>
        <button
          onClick={() => navigate('/')}
          className="text-sm text-[var(--temper-accent)] hover:underline"
        >
          Back to runs
        </button>
      </div>
    );
  }

  if (!execution) {
    const isActive = runStatus === 'running' || runStatus === 'claimed' || runStatus === 'pending';
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
              runStatus === 'running' ? 'bg-blue-900/50 text-blue-400 border-blue-700/50' :
              runStatus === 'claimed' ? 'bg-blue-900/50 text-blue-400 border-blue-700/50' :
              'bg-yellow-900/50 text-yellow-400 border-yellow-700/50'
            }`}>
              {runStatus}
            </span>
          )}
        </header>
        <div className="flex-1 flex items-center justify-center">
          <div className="flex flex-col items-center gap-3">
            {isActive ? (
              <>
                <div className="w-8 h-8 border-2 border-[var(--temper-accent)] border-t-transparent rounded-full animate-spin" />
                <span className="text-sm text-[var(--temper-text-muted)]">
                  Pipeline is {runStatus}... waiting for execution data
                </span>
                <span className="text-xs text-[var(--temper-text-dim)]">
                  Auto-refreshing every {POLL_INTERVAL_MS / 1000}s
                </span>
              </>
            ) : (
              <>
                <div className="skeleton h-8 w-8 rounded-full" />
                <span className="text-sm text-[var(--temper-text-muted)]">Loading execution...</span>
              </>
            )}
          </div>
        </div>
      </div>
    );
  }

  // key={runId} forces full remount when switching between runs
  return (
    <ExecutionView
      key={runId}
      execution={execution}
      onClose={() => navigate('/')}
    />
  );
}

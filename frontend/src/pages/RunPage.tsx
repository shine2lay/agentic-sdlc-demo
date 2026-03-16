import { useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { fetchRun } from '../api';
import { ExecutionView } from '../execution/ExecutionView';
import type { WorkflowExecution } from '../execution/types';

export function RunPage() {
  const { runId } = useParams<{ runId: string }>();
  const navigate = useNavigate();
  const [execution, setExecution] = useState<WorkflowExecution | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!runId) return;
    let active = true;

    setExecution(null);
    setError(null);

    fetchRun(runId)
      .then((run) => {
        if (!active) return;
        const result = run.result as Record<string, unknown> | null;
        if (result?.execution) {
          setExecution(result.execution as WorkflowExecution);
        } else {
          setError('Execution details not available yet');
        }
      })
      .catch((err) => {
        if (active) setError(err instanceof Error ? err.message : 'Failed to load');
      });

    return () => { active = false; };
  }, [runId]);

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
    return (
      <div className="flex flex-col h-full bg-[var(--temper-bg)]">
        <div className="bg-[var(--temper-panel)] px-4 py-3 border-b border-[var(--temper-border)] shrink-0">
          <div className="skeleton h-6 w-48" />
        </div>
        <div className="flex items-center gap-6 bg-[var(--temper-panel)]/50 px-4 py-2 border-b border-[var(--temper-border)] shrink-0">
          {Array.from({ length: 6 }).map((_, i) => (
            <div key={i} className="skeleton h-4 w-20" />
          ))}
        </div>
        <div className="flex-1 flex items-center justify-center">
          <div className="flex flex-col items-center gap-3">
            <div className="skeleton h-8 w-8 rounded-full" />
            <span className="text-sm text-[var(--temper-text-muted)]">Loading execution...</span>
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

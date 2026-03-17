import { useState, useEffect } from 'react';
import { ArrowLeft, Info } from 'lucide-react';
import { useExecutionStore } from '../../store';
import { StatusBadge } from '../shared/StatusBadge';
import { formatDuration, elapsedSeconds, cn } from '../../utils';

const DURATION_TICK_MS = 1000;

interface WorkflowHeaderProps {
  onClose: () => void;
  isLive?: boolean;
}

export function WorkflowHeader({ onClose, isLive }: WorkflowHeaderProps) {
  const workflow = useExecutionStore((s) => s.workflow);
  const select = useExecutionStore((s) => s.select);

  const [elapsed, setElapsed] = useState(0);
  const [errorExpanded, setErrorExpanded] = useState(false);

  const isRunning = workflow?.status === 'running';

  useEffect(() => {
    if (!isRunning || !workflow?.start_time) return;

    setElapsed(elapsedSeconds(workflow.start_time));
    const id = setInterval(() => {
      setElapsed(elapsedSeconds(workflow.start_time));
    }, DURATION_TICK_MS);

    return () => clearInterval(id);
  }, [isRunning, workflow?.start_time]);

  const displayDuration = isRunning
    ? formatDuration(elapsed)
    : formatDuration(workflow?.duration_seconds);

  return (
    <>
      <header className="flex items-center gap-4 bg-gray-900 px-4 py-3 border-b border-gray-700/60 shrink-0">
        <button
          onClick={onClose}
          className="text-gray-400 hover:text-gray-200 transition-colors shrink-0"
          aria-label="Back to workflow list"
        >
          <ArrowLeft className="w-5 h-5" />
        </button>

        <h1 className="text-lg font-semibold text-gray-100 truncate">
          {workflow?.workflow_name ?? 'Loading...'}
        </h1>

        <button
          onClick={() => workflow && select('workflow', workflow.id)}
          className="text-gray-400 hover:text-gray-200 transition-colors shrink-0"
          aria-label="Workflow details"
        >
          <Info className="w-4 h-4" />
        </button>

        {workflow && <StatusBadge status={workflow.status} />}

        <span
          className={cn(
            'text-sm font-mono',
            workflow?.status === 'failed'
              ? 'text-red-400'
              : workflow?.status === 'completed'
                ? 'text-emerald-400'
                : 'text-gray-400',
          )}
        >
          {displayDuration}
        </span>

        {/* Live polling indicator — pushed to the right */}
        {isLive && (
          <div className="ml-auto flex items-center gap-1.5 text-[11px] text-blue-400/70">
            <span className="w-1.5 h-1.5 rounded-full bg-blue-400 animate-pulse" />
            live
          </div>
        )}
      </header>

      {workflow?.status === 'failed' && workflow?.error_message && (
        <div
          onClick={() => setErrorExpanded(!errorExpanded)}
          className={cn(
            'bg-red-950/50 border-b border-red-900/50 px-4 py-2 text-sm text-red-400 cursor-pointer hover:bg-red-950/70 shrink-0',
            !errorExpanded && 'truncate',
          )}
          role="button"
          tabIndex={0}
          onKeyDown={(e) => {
            if (e.key === 'Enter' || e.key === ' ') setErrorExpanded(!errorExpanded);
          }}
        >
          {workflow.error_message}
        </div>
      )}
    </>
  );
}

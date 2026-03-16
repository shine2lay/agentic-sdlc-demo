import { useEffect, useRef } from 'react';
import { X } from 'lucide-react';
import { useExecutionStore } from '../../store';
import { ErrorBoundary } from '../shared/ErrorBoundary';
import { WorkflowPanel } from './WorkflowPanel';
import { StagePanel } from './StagePanel';
import { AgentPanel } from './AgentPanel';
import { LLMCallPanel } from './LLMCallPanel';
import { ToolCallPanel } from './ToolCallPanel';

const SHEET_TITLES: Record<string, string> = {
  workflow: 'Workflow Details',
  stage: 'Stage Details',
  agent: 'Agent Details',
  llmCall: 'LLM Call Inspector',
  toolCall: 'Tool Call Inspector',
};

export function DetailSheet() {
  const selection = useExecutionStore((s) => s.selection);
  const clearSelection = useExecutionStore((s) => s.clearSelection);
  const open = selection !== null;
  const panelRef = useRef<HTMLDivElement>(null);

  // Close on Escape key
  useEffect(() => {
    if (!open) return;
    function handleKeyDown(e: KeyboardEvent) {
      if (e.key === 'Escape') clearSelection();
    }
    document.addEventListener('keydown', handleKeyDown);
    return () => document.removeEventListener('keydown', handleKeyDown);
  }, [open, clearSelection]);

  // Focus first focusable element when panel opens
  useEffect(() => {
    if (!open || !panelRef.current) return;
    const firstFocusable = panelRef.current.querySelector<HTMLElement>(
      'button, [tabindex]:not([tabindex="-1"])',
    );
    firstFocusable?.focus();
  }, [open, selection?.type]);

  return (
    <>
      {/* Backdrop */}
      {open && (
        <div
          className="fixed inset-0 z-40 bg-black/40"
          aria-hidden="true"
          onClick={clearSelection}
        />
      )}

      {/* Slide-over panel */}
      <div
        ref={panelRef}
        role="dialog"
        aria-modal="true"
        aria-label={selection ? SHEET_TITLES[selection.type] ?? 'Details' : 'Details'}
        className={[
          'fixed inset-y-0 right-0 z-50 flex flex-col',
          'w-full sm:w-[70vw] sm:max-w-[70vw]',
          'bg-gray-900 border-l border-gray-700 shadow-2xl',
          'overflow-y-auto',
          'transition-transform duration-300 ease-in-out',
          open ? 'translate-x-0' : 'translate-x-full',
        ].join(' ')}
      >
        {/* Panel header */}
        <div className="flex items-center justify-between px-4 py-3 border-b border-gray-700 sticky top-0 z-10 bg-gray-900 shrink-0">
          <h2 className="text-sm font-semibold text-gray-200">
            {selection ? SHEET_TITLES[selection.type] ?? 'Details' : 'Details'}
          </h2>
          <button
            onClick={clearSelection}
            className="p-1 rounded text-gray-500 hover:text-gray-200 hover:bg-gray-700 transition-colors"
            aria-label="Close panel"
          >
            <X className="size-4" />
          </button>
        </div>

        {/* Panel content */}
        <div className="flex-1 min-h-0">
          {selection?.type === 'workflow' && (
            <ErrorBoundary>
              <WorkflowPanel />
            </ErrorBoundary>
          )}
          {selection?.type === 'toolCall' && (
            <ErrorBoundary>
              <ToolCallPanel toolCallId={selection.id} />
            </ErrorBoundary>
          )}
          {selection?.type === 'llmCall' && (
            <ErrorBoundary>
              <LLMCallPanel llmCallId={selection.id} />
            </ErrorBoundary>
          )}
          {selection?.type === 'agent' && (
            <ErrorBoundary>
              <AgentPanel agentId={selection.id} />
            </ErrorBoundary>
          )}
          {selection?.type === 'stage' && (
            <ErrorBoundary>
              <StagePanel stageId={selection.id} />
            </ErrorBoundary>
          )}
        </div>
      </div>
    </>
  );
}

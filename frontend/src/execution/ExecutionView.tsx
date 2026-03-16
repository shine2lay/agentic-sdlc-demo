import { useEffect, useMemo, useState } from 'react';
import { ReactFlowProvider } from '@xyflow/react';
import { useExecutionStore } from './store';
import { WorkflowHeader } from './components/layout/WorkflowHeader';
import { SummaryBar } from './components/layout/SummaryBar';
import { ViewTabs } from './components/layout/ViewTabs';
import { EventLogPanel } from './components/layout/EventLogPanel';
import { LLMCallsTable } from './components/layout/LLMCallsTable';
import { DagView } from './components/dag/DagView';
import { TimelineView } from './components/timeline/TimelineView';
import { DetailSheet } from './components/panels/DetailSheet';
import { ErrorBoundary } from './components/shared/ErrorBoundary';
import type { WorkflowExecution } from './types';

function LoadingSkeleton() {
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

interface ExecutionViewProps {
  execution: WorkflowExecution;
  onClose: () => void;
}

export function ExecutionView({ execution, onClose }: ExecutionViewProps) {
  const workflow = useExecutionStore((s) => s.workflow);
  const stages = useExecutionStore((s) => s.stages);
  const eventLog = useExecutionStore((s) => s.eventLog);
  const llmCalls = useExecutionStore((s) => s.llmCalls);
  const applySnapshot = useExecutionStore((s) => s.applySnapshot);
  const reset = useExecutionStore((s) => s.reset);

  const [activeTab, setActiveTab] = useState(() => {
    return localStorage.getItem('sdlc-active-tab') ?? 'dag';
  });

  // Apply execution data to the store
  useEffect(() => {
    applySnapshot(execution);
    return () => reset();
  }, [execution, applySnapshot, reset]);

  // Persist active tab
  useEffect(() => {
    localStorage.setItem('sdlc-active-tab', activeTab);
  }, [activeTab]);

  const filteredEventCount = useMemo(
    () => eventLog.length,
    [eventLog],
  );

  if (!workflow) {
    return <LoadingSkeleton />;
  }

  return (
    <ReactFlowProvider>
      <div className="flex flex-col h-full bg-[var(--temper-bg)]">
        <WorkflowHeader onClose={onClose} />
        <SummaryBar />

        <ViewTabs
          activeTab={activeTab}
          onTabChange={setActiveTab}
          stageCount={stages.size}
          eventCount={filteredEventCount}
          llmCallCount={llmCalls.size}
          dagContent={
            <ErrorBoundary>
              <div className="relative w-full h-full">
                <DagView />
              </div>
            </ErrorBoundary>
          }
          timelineContent={<ErrorBoundary><TimelineView /></ErrorBoundary>}
          eventLogContent={<ErrorBoundary><EventLogPanel /></ErrorBoundary>}
          llmCallsContent={<ErrorBoundary><LLMCallsTable /></ErrorBoundary>}
        />
        <DetailSheet />
      </div>
    </ReactFlowProvider>
  );
}

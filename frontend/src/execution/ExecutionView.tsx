import { useEffect, useState } from 'react';
import { ReactFlowProvider } from '@xyflow/react';
import { useExecutionStore } from '@/execution/store';
import { WorkflowHeader } from '@/execution/components/layout/WorkflowHeader';
import { WorkflowSummaryBar } from '@/execution/components/layout/WorkflowSummaryBar';
import { ViewTabs } from '@/execution/components/layout/ViewTabs';
import { EventLogPanel } from '@/execution/components/layout/EventLogPanel';
import { LLMCallsTable } from '@/execution/components/layout/LLMCallsTable';
import { CheckpointPanel } from '@/execution/components/layout/CheckpointPanel';
import { ExecutionDAG } from '@/execution/components/dag/ExecutionDAG';
import { TimelineChart } from '@/execution/components/timeline/TimelineChart';
import { DetailSheet } from '@/execution/components/panels/DetailSheet';
import { ErrorBoundary } from '@/execution/components/shared/ErrorBoundary';

interface ExecutionViewProps {
  execution: Record<string, unknown>;
  onClose?: () => void;
  isLive?: boolean;
}

export default function ExecutionView({ execution }: ExecutionViewProps) {
  const applySnapshot = useExecutionStore((s) => s.applySnapshot);
  const workflow = useExecutionStore((s) => s.workflow);
  const selection = useExecutionStore((s) => s.selection);
  const reset = useExecutionStore((s) => s.reset);

  const [activeTab, setActiveTab] = useState(() =>
    localStorage.getItem('sdlc-active-tab') || 'dag'
  );

  useEffect(() => {
    if (execution) applySnapshot(execution as any);
  }, [execution, applySnapshot]);

  useEffect(() => () => reset(), [reset]);
  useEffect(() => { localStorage.setItem('sdlc-active-tab', activeTab); }, [activeTab]);

  if (!workflow) {
    return (
      <div className="flex flex-col h-full bg-temper-bg">
        <div className="flex-1 flex items-center justify-center">
          <span className="text-sm text-temper-text-muted">Loading execution data...</span>
        </div>
      </div>
    );
  }

  return (
    <ErrorBoundary>
      <div className="flex flex-col h-full bg-temper-bg overflow-hidden">
        <WorkflowHeader />
        <WorkflowSummaryBar />
        <ViewTabs
          activeTab={activeTab}
          onTabChange={setActiveTab}
          dagContent={<ReactFlowProvider><ExecutionDAG /></ReactFlowProvider>}
          timelineContent={<TimelineChart />}
          eventLogContent={<EventLogPanel />}
          llmCallsContent={<LLMCallsTable />}
          checkpointContent={<CheckpointPanel onSwitchTab={setActiveTab} />}
        />
        {selection && <DetailSheet />}
      </div>
    </ErrorBoundary>
  );
}

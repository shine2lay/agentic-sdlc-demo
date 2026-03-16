import { useMemo } from 'react';
import { useExecutionStore } from '../../store';
import { CollapsibleSection } from '../shared/CollapsibleSection';
import { JsonViewer } from '../shared/JsonViewer';
import { MetricCell } from '../shared/MetricCell';
import { StatusBadge } from '../shared/StatusBadge';
import { formatDuration, formatTimestamp, formatTokens, formatCost, formatBytes } from '../../utils';

export function WorkflowPanel() {
  const workflow = useExecutionStore((s) => s.workflow);
  const stages = useExecutionStore((s) => s.stages);
  const toolCalls = useExecutionStore((s) => s.toolCalls);
  const select = useExecutionStore((s) => s.select);

  const toolAnalytics = useMemo(() => {
    const stats = new Map<string, { count: number; failed: number; totalDuration: number; approvalCount: number }>();
    for (const [, tc] of toolCalls) {
      const name = tc.tool_name;
      const existing = stats.get(name) ?? { count: 0, failed: 0, totalDuration: 0, approvalCount: 0 };
      existing.count++;
      if (tc.status === 'failed') existing.failed++;
      existing.totalDuration += tc.duration_seconds ?? 0;
      if (tc.approval_required) existing.approvalCount++;
      stats.set(name, existing);
    }
    return Array.from(stats.entries())
      .map(([name, s]) => ({ name, ...s, avgDuration: s.totalDuration / s.count }))
      .sort((a, b) => b.count - a.count);
  }, [toolCalls]);

  if (!workflow) {
    return (
      <div className="flex flex-col items-center justify-center p-8 gap-2">
        <span className="text-gray-500 text-sm">No workflow data</span>
      </div>
    );
  }

  const inputSize = workflow.input_data
    ? formatBytes(new Blob([JSON.stringify(workflow.input_data)]).size)
    : null;
  const outputSize = workflow.output_data
    ? formatBytes(new Blob([JSON.stringify(workflow.output_data)]).size)
    : null;

  return (
    <div className="flex flex-col gap-4 p-4">
      {/* Header */}
      <div className="flex items-center gap-3">
        <h3 className="text-lg font-semibold text-gray-100">
          {workflow.workflow_name}
        </h3>
        <StatusBadge status={workflow.status} />
      </div>

      {/* Metrics grid */}
      <div className="grid grid-cols-2 gap-3">
        <MetricCell label="Start Time" value={formatTimestamp(workflow.start_time)} />
        <MetricCell label="End Time" value={formatTimestamp(workflow.end_time)} />
        <MetricCell label="Total Tokens" value={formatTokens(workflow.total_tokens)} />
        <MetricCell label="Total Cost" value={formatCost(workflow.total_cost_usd)} />
        <MetricCell label="LLM Calls" value={String(workflow.total_llm_calls ?? 0)} />
        <MetricCell label="Tool Calls" value={String(workflow.total_tool_calls ?? 0)} />
      </div>

      {/* Error */}
      {workflow.status === 'failed' && workflow.error_message && (
        <div className="rounded-md bg-red-950/40 border border-red-900/50 p-3 text-sm text-red-400">
          {workflow.error_message}
        </div>
      )}

      {/* Stage breakdown */}
      {stages.size > 0 && (
        <>
          <hr className="border-gray-700" />
          <div className="flex flex-col gap-2">
            <span className="text-sm font-medium text-gray-400">Stage Breakdown</span>
            <div className="flex flex-col gap-1">
              {Array.from(stages.values()).map((stage) => (
                <button
                  key={stage.id}
                  onClick={() => select('stage', stage.id)}
                  className="flex items-center justify-between rounded-md bg-gray-800 p-2 text-xs hover:bg-gray-700 transition-colors"
                >
                  <span className="flex items-center gap-2">
                    <StatusBadge status={stage.status} />
                    <span className="text-gray-200 font-medium">
                      {stage.stage_name ?? stage.name ?? stage.id}
                    </span>
                  </span>
                  <span className="text-gray-500">
                    {formatDuration(stage.duration_seconds)}
                  </span>
                </button>
              ))}
            </div>
          </div>
        </>
      )}

      {/* Tool Analytics */}
      {toolAnalytics.length > 0 && (
        <CollapsibleSection title="Tool Analytics">
          <div className="flex flex-col gap-1 mt-1">
            {toolAnalytics.map((t) => (
              <div
                key={t.name}
                className="flex items-center justify-between rounded-md bg-gray-800 p-2 text-xs"
              >
                <span className="text-gray-200 font-medium">{t.name}</span>
                <div className="flex items-center gap-3 text-gray-500">
                  <span>{t.count} calls</span>
                  {t.failed > 0 && <span className="text-red-400">{t.failed} failed</span>}
                  <span>avg {formatDuration(t.avgDuration)}</span>
                  {t.approvalCount > 0 && (
                    <span className="text-amber-400">{t.approvalCount} approval</span>
                  )}
                </div>
              </div>
            ))}
          </div>
        </CollapsibleSection>
      )}

      <hr className="border-gray-700" />

      {/* Input / Output */}
      <CollapsibleSection title={`Input Data${inputSize ? ` (${inputSize})` : ''}`}>
        <JsonViewer data={workflow.input_data} />
      </CollapsibleSection>

      <CollapsibleSection title={`Output Data${outputSize ? ` (${outputSize})` : ''}`}>
        <JsonViewer data={workflow.output_data} />
      </CollapsibleSection>

      {/* Workflow Config */}
      {(workflow.workflow_config ?? workflow.workflow_config_snapshot) && (
        <CollapsibleSection title="Workflow Config">
          <JsonViewer data={workflow.workflow_config ?? workflow.workflow_config_snapshot} />
        </CollapsibleSection>
      )}
    </div>
  );
}

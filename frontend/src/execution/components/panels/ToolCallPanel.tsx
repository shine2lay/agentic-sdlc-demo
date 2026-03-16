import { useExecutionStore } from '../../store';
import { StatusBadge } from '../shared/StatusBadge';
import { CollapsibleSection } from '../shared/CollapsibleSection';
import { JsonViewer } from '../shared/JsonViewer';
import { MetricCell } from '../shared/MetricCell';
import { CopyButton } from '../shared/CopyButton';
import { formatDuration, formatTimestamp, categorizeError } from '../../utils';

interface ToolCallPanelProps {
  toolCallId: string;
}

export function ToolCallPanel({ toolCallId }: ToolCallPanelProps) {
  const toolCall = useExecutionStore((s) => s.toolCalls.get(toolCallId));
  const select = useExecutionStore((s) => s.select);
  const agents = useExecutionStore((s) => s.agents);
  const stages = useExecutionStore((s) => s.stages);

  if (!toolCall) {
    return (
      <div className="p-4 text-sm text-gray-500">Tool call not found.</div>
    );
  }

  const parentAgent = toolCall.agent_execution_id
    ? agents.get(toolCall.agent_execution_id)
    : undefined;
  const parentStageId = parentAgent?.stage_execution_id ?? parentAgent?.stage_id;
  const parentStage = parentStageId ? stages.get(parentStageId) : undefined;

  return (
    <div className="flex flex-col gap-4 p-4">
      {/* Breadcrumb */}
      <div className="flex items-center gap-1 text-xs flex-wrap">
        {parentStage && (
          <>
            <button
              onClick={() => select('stage', parentStageId!)}
              className="text-blue-400 hover:underline"
            >
              {parentStage.stage_name ?? parentStage.name ?? parentStageId}
            </button>
            <span className="text-gray-600">&gt;</span>
          </>
        )}
        {toolCall.agent_execution_id && (
          <>
            <button
              onClick={() => select('agent', toolCall.agent_execution_id!)}
              className="text-blue-400 hover:underline"
            >
              {parentAgent?.agent_name ?? parentAgent?.name ?? toolCall.agent_execution_id}
            </button>
            <span className="text-gray-600">&gt;</span>
          </>
        )}
        <span className="text-gray-500">{toolCall.tool_name}</span>
      </div>

      {/* Header */}
      <div className="flex flex-wrap items-center gap-2">
        <h3 className="text-lg font-semibold text-gray-100">
          {toolCall.tool_name}
        </h3>
        <StatusBadge status={toolCall.status} />
        {toolCall.safety_checks_applied != null && (
          <span className="inline-flex items-center px-2 py-0.5 rounded text-xs border border-gray-600 bg-gray-800 text-gray-400">
            safety checked
          </span>
        )}
        {toolCall.approval_required && (
          <span className="inline-flex items-center px-2 py-0.5 rounded text-xs border border-amber-900/50 bg-amber-950/30 text-amber-400">
            Approval Required
          </span>
        )}
      </div>

      {/* Metrics */}
      <div className="grid grid-cols-2 gap-3">
        <MetricCell label="Duration" value={formatDuration(toolCall.duration_seconds)} />
        <MetricCell label="Start Time" value={formatTimestamp(toolCall.start_time)} />
        <MetricCell label="End Time" value={formatTimestamp(toolCall.end_time)} />
      </div>

      {/* Error */}
      {toolCall.status === 'failed' && toolCall.error_message && (() => {
        const { type, retryable } = categorizeError(toolCall.error_message);
        return (
          <div className="rounded-md bg-red-950/40 border border-red-900/50 p-3 text-sm text-red-400">
            <div className="flex items-center gap-2 mb-1">
              <span className="text-xs font-medium px-1.5 py-0.5 rounded bg-red-950 border border-red-900/50">
                {type}
              </span>
              {retryable && <span className="text-xs text-amber-400">Retryable</span>}
            </div>
            {toolCall.error_message}
          </div>
        );
      })()}

      <hr className="border-gray-700" />

      {/* Input Parameters */}
      <CollapsibleSection title="Input Parameters" defaultOpen>
        {toolCall.input_params ? (
          <>
            <JsonViewer data={toolCall.input_params} />
            <CopyButton
              text={JSON.stringify(toolCall.input_params, null, 2)}
              className="mt-1"
            />
          </>
        ) : (
          <p className="mt-1 text-xs text-gray-500">No input parameters</p>
        )}
      </CollapsibleSection>

      {/* Output */}
      <CollapsibleSection title="Output" defaultOpen>
        {toolCall.output_data != null ? (
          <>
            <JsonViewer data={toolCall.output_data} />
            <CopyButton
              text={
                typeof toolCall.output_data === 'string'
                  ? toolCall.output_data
                  : JSON.stringify(toolCall.output_data, null, 2)
              }
              className="mt-1"
            />
          </>
        ) : (
          <p className="mt-1 text-xs text-gray-500">No output data</p>
        )}
      </CollapsibleSection>

      {/* Safety checks */}
      {toolCall.safety_checks_applied != null && (
        <CollapsibleSection title="Safety Checks">
          <JsonViewer data={toolCall.safety_checks_applied} />
        </CollapsibleSection>
      )}
    </div>
  );
}

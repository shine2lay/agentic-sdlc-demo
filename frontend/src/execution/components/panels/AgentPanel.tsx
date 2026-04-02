import { useMemo } from 'react';
import { useExecutionStore } from '../../store';
import { StatusBadge } from '../shared/StatusBadge';
import { CollapsibleSection } from '../shared/CollapsibleSection';
import { JsonViewer } from '../shared/JsonViewer';
import { MetricCell } from '../shared/MetricCell';
import { MarkdownDisplay } from '../shared/MarkdownDisplay';
import { CopyButton } from '../shared/CopyButton';
import { formatDuration, formatTimestamp, formatTokens, formatCost, categorizeError } from '../../utils';

interface AgentPanelProps {
  agentId: string;
}

export function AgentPanel({ agentId }: AgentPanelProps) {
  const agent = useExecutionStore((s) => s.agents.get(agentId));
  const select = useExecutionStore((s) => s.select);
  const stages = useExecutionStore((s) => s.stages);

  const resolvedStageId = useMemo(() => {
    if (!agent) return undefined;
    const direct = agent.stage_execution_id ?? agent.stage_id;
    if (direct) return direct;
    for (const [stageId, stage] of Array.from(stages)) {
      if (stage.agents?.some((a) => a.id === agentId)) {
        return stageId;
      }
    }
    return undefined;
  }, [agent, stages, agentId]);

  if (!agent) {
    return (
      <div className="flex flex-col items-center justify-center p-8 gap-2">
        <span className="text-gray-500 text-sm">Agent not found</span>
      </div>
    );
  }

  const config = agent.agent_config_snapshot?.agent;
  const totalTokens = Math.max(agent.total_tokens, 1);
  const promptPct = (agent.prompt_tokens / totalTokens) * 100;
  const completionPct = (agent.completion_tokens / totalTokens) * 100;

  return (
    <div className="flex flex-col gap-4 p-4">
      {/* Breadcrumb */}
      {resolvedStageId && (
        <button
          onClick={() => select('stage', resolvedStageId)}
          className="text-xs text-blue-400 hover:underline self-start"
        >
          &larr; Back to Stage
        </button>
      )}

      {/* Header */}
      <div className="flex flex-wrap items-center gap-2">
        <h3 className="text-lg font-semibold text-gray-100">
          {agent.agent_name ?? agent.name ?? agentId}
        </h3>
        <StatusBadge status={agent.status} />
        {config?.provider && config?.model && (
          <span className="inline-flex items-center px-2 py-0.5 rounded text-xs border border-gray-600 bg-gray-800 text-gray-400">
            {config.provider}/{config.model}
          </span>
        )}
        {config?.type && config.type !== 'standard' && (
          <span className="inline-flex items-center px-2 py-0.5 rounded text-xs border border-gray-600 bg-gray-800 text-gray-400">
            {config.type}
          </span>
        )}
        {agent.role && (
          <span className="inline-flex items-center px-2 py-0.5 rounded text-xs border border-gray-600 bg-gray-800 text-gray-400">
            {agent.role}
          </span>
        )}
      </div>

      {/* Metrics grid — token/cost/call counts */}
      <div className="grid grid-cols-3 gap-2">
        <MetricCell label="Prompt Tokens" value={formatTokens(agent.prompt_tokens)} compact />
        <MetricCell label="Completion Tokens" value={formatTokens(agent.completion_tokens)} compact />
        <MetricCell label="Total Tokens" value={formatTokens(agent.total_tokens)} compact />
        <MetricCell label="Cost" value={formatCost(agent.estimated_cost_usd)} compact />
        <MetricCell label="Duration" value={formatDuration(agent.duration_seconds)} compact />
        <MetricCell label="LLM Calls" value={String(agent.total_llm_calls)} compact />
        <MetricCell label="Tool Calls" value={String(agent.total_tool_calls)} compact />
        {agent.confidence_score != null && (
          <MetricCell
            label="Confidence"
            value={`${(agent.confidence_score * 100).toFixed(1)}%`}
            compact
          />
        )}
      </div>

      {/* Timestamps */}
      <div className="grid grid-cols-2 gap-2">
        <MetricCell label="Start Time" value={formatTimestamp(agent.start_time)} compact />
        <MetricCell label="End Time" value={formatTimestamp(agent.end_time)} compact />
      </div>

      {/* Token distribution bar */}
      {agent.total_tokens > 0 && (
        <div className="flex flex-col gap-1">
          <span className="text-xs text-gray-500">Token Distribution</span>
          <div className="flex h-3 w-full overflow-hidden rounded-full bg-gray-800">
            <div
              className="bg-violet-500 transition-all"
              style={{ width: `${promptPct}%` }}
            />
            <div
              className="bg-sky-500 transition-all"
              style={{ width: `${completionPct}%` }}
            />
          </div>
          <div className="flex gap-3 text-xs text-gray-600">
            <span className="flex items-center gap-1">
              <span className="inline-block size-2 rounded-full bg-violet-500" />
              Prompt {formatTokens(agent.prompt_tokens)}
            </span>
            <span className="flex items-center gap-1">
              <span className="inline-block size-2 rounded-full bg-sky-500" />
              Completion {formatTokens(agent.completion_tokens)}
            </span>
          </div>
        </div>
      )}

      {/* Error */}
      {agent.error_message && (() => {
        const { type, retryable } = categorizeError(agent.error_message);
        return (
          <div className="rounded-md bg-red-950/40 border border-red-900/50 p-3 text-sm text-red-400">
            <div className="flex items-center gap-2 mb-1">
              <span className="text-xs font-medium px-1.5 py-0.5 rounded bg-red-950 border border-red-900/50">
                {type}
              </span>
              {retryable && <span className="text-xs text-amber-400">Retryable</span>}
            </div>
            {agent.error_message}
          </div>
        );
      })()}

      <hr className="border-gray-700" />

      {/* Collapsible sections */}
      <CollapsibleSection title="Input Data">
        <JsonViewer data={agent.input_data} />
      </CollapsibleSection>

      <CollapsibleSection title="Output">
        {agent.output ? (
          <>
            <MarkdownDisplay content={agent.output} className="mt-1 max-h-64 overflow-auto" />
            <CopyButton text={agent.output} className="mt-1" />
          </>
        ) : (
          <JsonViewer data={agent.output_data} />
        )}
      </CollapsibleSection>

      {agent.reasoning && (
        <CollapsibleSection title="Reasoning">
          <MarkdownDisplay content={agent.reasoning} className="mt-1 max-h-64 overflow-auto" />
          <CopyButton text={agent.reasoning} className="mt-1" />
        </CollapsibleSection>
      )}

      {config && (
        <CollapsibleSection title="Agent Config">
          <JsonViewer data={agent.agent_config_snapshot} />
        </CollapsibleSection>
      )}

      {(config?.inputs || config?.outputs) && (
        <CollapsibleSection title="Declared I/O">
          {config?.inputs && (
            <div className="mb-2">
              <span className="text-[10px] font-medium text-gray-500 uppercase tracking-wide block mb-1">
                Inputs
              </span>
              <div className="rounded-md border border-gray-700 bg-gray-800 overflow-hidden">
                <table className="w-full text-xs">
                  <tbody>
                    {Object.entries(config.inputs).map(([name, decl]) => (
                      <tr
                        key={name}
                        className="border-b border-gray-700/50 last:border-b-0"
                      >
                        <td className="px-3 py-1 text-gray-200 font-medium">{name}</td>
                        <td className="px-3 py-1 text-gray-400 font-mono">{(decl as any).type}</td>
                        <td className="px-3 py-1 text-gray-600">
                          {(decl as any).required ? 'required' : 'optional'}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}
          {config?.outputs && (
            <div>
              <span className="text-[10px] font-medium text-gray-500 uppercase tracking-wide block mb-1">
                Outputs
              </span>
              <div className="rounded-md border border-gray-700 bg-gray-800 overflow-hidden">
                <table className="w-full text-xs">
                  <tbody>
                    {Object.entries(config.outputs).map(([name, decl]) => (
                      <tr
                        key={name}
                        className="border-b border-gray-700/50 last:border-b-0"
                      >
                        <td className="px-3 py-1 text-gray-200 font-medium">{name}</td>
                        <td className="px-3 py-1 text-gray-400 font-mono">{(decl as any).type}</td>
                        <td className="px-3 py-1 text-gray-600">{(decl as any).description ?? ''}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}
        </CollapsibleSection>
      )}

      <hr className="border-gray-700" />

      {/* LLM calls list */}
      {agent.llm_calls && agent.llm_calls.length > 0 && (
        <div className="flex flex-col gap-2">
          <span className="text-sm font-medium text-gray-400">LLM Calls</span>
          {agent.llm_calls.map((llm) => (
            <button
              key={llm.id}
              onClick={() => select('llmCall', llm.id)}
              className="flex items-center justify-between rounded-md px-3 py-2 text-sm text-left hover:bg-gray-800 transition-colors"
            >
              <span className="text-xs text-gray-300 truncate">
                {llm.model ?? llm.llm_call_id ?? llm.id}
              </span>
              <StatusBadge status={llm.status} />
            </button>
          ))}
        </div>
      )}

      {/* Tool calls list */}
      {agent.tool_calls && agent.tool_calls.length > 0 && (
        <div className="flex flex-col gap-2">
          <span className="text-sm font-medium text-gray-400">Tool Calls</span>
          {agent.tool_calls.map((tool) => (
            <button
              key={tool.id}
              onClick={() => select('toolCall', tool.id)}
              className="flex items-center justify-between rounded-md px-3 py-2 text-sm text-left hover:bg-gray-800 transition-colors"
            >
              <span className="text-xs text-gray-300">{tool.tool_name}</span>
              <StatusBadge status={tool.status} />
            </button>
          ))}
        </div>
      )}
    </div>
  );
}

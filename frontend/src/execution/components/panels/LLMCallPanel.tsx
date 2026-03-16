import { useExecutionStore } from '../../store';
import { StatusBadge } from '../shared/StatusBadge';
import { CollapsibleSection } from '../shared/CollapsibleSection';
import { MetricCell } from '../shared/MetricCell';
import { MarkdownDisplay } from '../shared/MarkdownDisplay';
import { CopyButton } from '../shared/CopyButton';
import { formatTimestamp, formatTokens, formatCost, formatBytes, categorizeError } from '../../utils';

interface LLMCallPanelProps {
  llmCallId: string;
}

function PromptDisplay({ prompt }: { prompt: unknown }) {
  if (prompt == null) {
    return <p className="text-xs text-gray-500">No prompt data</p>;
  }

  if (Array.isArray(prompt)) {
    return (
      <div className="mt-1 flex flex-col gap-2">
        {prompt.map((msg, i) => {
          const role =
            typeof msg === 'object' && msg !== null
              ? (msg as Record<string, unknown>).role
              : undefined;
          const content =
            typeof msg === 'object' && msg !== null
              ? (msg as Record<string, unknown>).content
              : String(msg);
          return (
            <div key={i} className="rounded-md bg-gray-800 p-2">
              {role != null && (
                <span className="mb-1 block text-xs font-medium text-blue-400">
                  {String(role)}
                </span>
              )}
              <pre className="text-xs text-gray-300 whitespace-pre-wrap">
                {typeof content === 'string'
                  ? content
                  : JSON.stringify(content, null, 2)}
              </pre>
            </div>
          );
        })}
      </div>
    );
  }

  return (
    <pre className="mt-1 max-h-64 overflow-auto rounded-md bg-gray-800 p-3 text-xs text-gray-300 whitespace-pre-wrap">
      {typeof prompt === 'string' ? prompt : JSON.stringify(prompt, null, 2)}
    </pre>
  );
}

function promptToString(prompt: unknown): string {
  if (prompt == null) return '';
  if (typeof prompt === 'string') return prompt;
  return JSON.stringify(prompt, null, 2);
}

function TokenBar({
  promptTokens,
  completionTokens,
  totalTokens,
}: {
  promptTokens: number;
  completionTokens: number;
  totalTokens: number;
}) {
  const total = Math.max(totalTokens, 1);
  const promptPct = (promptTokens / total) * 100;
  const completionPct = (completionTokens / total) * 100;

  return (
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
          Prompt {formatTokens(promptTokens)}
        </span>
        <span className="flex items-center gap-1">
          <span className="inline-block size-2 rounded-full bg-sky-500" />
          Completion {formatTokens(completionTokens)}
        </span>
      </div>
    </div>
  );
}

export function LLMCallPanel({ llmCallId }: LLMCallPanelProps) {
  const llmCall = useExecutionStore((s) => s.llmCalls.get(llmCallId));
  const select = useExecutionStore((s) => s.select);
  const agents = useExecutionStore((s) => s.agents);
  const stages = useExecutionStore((s) => s.stages);

  if (!llmCall) {
    return (
      <div className="p-4 text-sm text-gray-500">LLM call not found.</div>
    );
  }

  const parentAgent = llmCall.agent_execution_id
    ? agents.get(llmCall.agent_execution_id)
    : undefined;
  const parentStageId = parentAgent?.stage_execution_id ?? parentAgent?.stage_id;
  const parentStage = parentStageId ? stages.get(parentStageId) : undefined;

  const latencyDisplay =
    llmCall.latency_ms != null
      ? `${llmCall.latency_ms}ms`
      : llmCall.duration_seconds != null
        ? `${(llmCall.duration_seconds * 1000).toFixed(0)}ms`
        : '-';

  const promptStr = promptToString(llmCall.prompt);
  const promptSize = promptStr ? formatBytes(new Blob([promptStr]).size) : null;

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
        {llmCall.agent_execution_id && (
          <>
            <button
              onClick={() => select('agent', llmCall.agent_execution_id!)}
              className="text-blue-400 hover:underline"
            >
              {parentAgent?.agent_name ?? parentAgent?.name ?? llmCall.agent_execution_id}
            </button>
            <span className="text-gray-600">&gt;</span>
          </>
        )}
        <span className="text-gray-500">
          {llmCall.provider && llmCall.model
            ? `${llmCall.provider}/${llmCall.model}`
            : llmCall.model ?? 'LLM Call'}
        </span>
      </div>

      {/* Header */}
      <div className="flex flex-wrap items-center gap-2">
        <h3 className="text-lg font-semibold text-gray-100">
          {llmCall.provider && llmCall.model
            ? `${llmCall.provider}/${llmCall.model}`
            : llmCall.model ?? 'LLM Call'}
        </h3>
        <StatusBadge status={llmCall.status} />
      </div>

      {/* Metrics */}
      <div className="grid grid-cols-2 gap-3">
        <MetricCell label="Latency" value={latencyDisplay} />
        <MetricCell label="Total Tokens" value={formatTokens(llmCall.total_tokens)} />
        <MetricCell label="Prompt Tokens" value={formatTokens(llmCall.prompt_tokens)} />
        <MetricCell label="Completion Tokens" value={formatTokens(llmCall.completion_tokens)} />
        <MetricCell label="Cost" value={formatCost(llmCall.estimated_cost_usd)} />
        {llmCall.tool_calls_made != null && (
          <MetricCell label="Tool Calls Made" value={String(llmCall.tool_calls_made)} />
        )}
        {promptSize && <MetricCell label="Prompt Size" value={promptSize} />}
        <MetricCell label="Start Time" value={formatTimestamp(llmCall.start_time)} />
        <MetricCell label="End Time" value={formatTimestamp(llmCall.end_time)} />
      </div>

      {/* Token bar */}
      {llmCall.total_tokens > 0 && (
        <TokenBar
          promptTokens={llmCall.prompt_tokens}
          completionTokens={llmCall.completion_tokens}
          totalTokens={llmCall.total_tokens}
        />
      )}

      {/* Error */}
      {llmCall.status === 'failed' && llmCall.error_message && (() => {
        const { type, retryable } = categorizeError(llmCall.error_message);
        return (
          <div className="rounded-md bg-red-950/40 border border-red-900/50 p-3 text-sm text-red-400">
            <div className="flex items-center gap-2 mb-1">
              <span className="text-xs font-medium px-1.5 py-0.5 rounded bg-red-950 border border-red-900/50">
                {type}
              </span>
              {retryable && <span className="text-xs text-amber-400">Retryable</span>}
            </div>
            {llmCall.error_message}
          </div>
        );
      })()}

      <hr className="border-gray-700" />

      {/* Prompt */}
      <CollapsibleSection title="Prompt" defaultOpen>
        <PromptDisplay prompt={llmCall.prompt} />
        <CopyButton text={promptStr} className="mt-1" />
      </CollapsibleSection>

      {/* Response */}
      <CollapsibleSection title="Response" defaultOpen>
        {llmCall.response ? (
          <>
            <MarkdownDisplay content={llmCall.response} className="mt-1 max-h-96 overflow-auto" />
            <CopyButton text={llmCall.response} className="mt-1" />
          </>
        ) : (
          <p className="mt-1 text-xs text-gray-500">No response data</p>
        )}
      </CollapsibleSection>
    </div>
  );
}

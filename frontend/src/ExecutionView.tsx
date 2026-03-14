import { useEffect, useState } from 'react';
import { fetchExecution, type WorkflowExecution, type StageExecution, type AgentExecution } from './temperApi';

function formatDuration(seconds: number | null): string {
  if (seconds == null) return '-';
  if (seconds < 1) return `${Math.round(seconds * 1000)}ms`;
  if (seconds < 60) return `${seconds.toFixed(1)}s`;
  return `${Math.floor(seconds / 60)}m ${Math.round(seconds % 60)}s`;
}

function formatTokens(n: number): string {
  if (n === 0) return '-';
  if (n < 1000) return String(n);
  return `${(n / 1000).toFixed(1)}k`;
}

function StatusDot({ status }: { status: string }) {
  return <span className={`exec-status-dot ${status}`} />;
}

function AgentRow({ agent }: { agent: AgentExecution }) {
  const [expanded, setExpanded] = useState(false);

  return (
    <div className="agent-row">
      <div className="agent-header" onClick={() => setExpanded(!expanded)}>
        <div className="agent-left">
          <StatusDot status={agent.status} />
          <span className="agent-name">{agent.agent_name}</span>
        </div>
        <div className="agent-stats">
          {agent.total_tokens > 0 && <span className="stat">{formatTokens(agent.total_tokens)} tok</span>}
          {agent.num_llm_calls > 0 && <span className="stat">{agent.num_llm_calls} llm</span>}
          {agent.num_tool_calls > 0 && <span className="stat">{agent.num_tool_calls} tool</span>}
          <span className="stat">{formatDuration(agent.duration_seconds)}</span>
          <span className="expand-icon">{expanded ? '\u25B4' : '\u25BE'}</span>
        </div>
      </div>
      {expanded && (
        <div className="agent-detail">
          {agent.error_message && (
            <div className="error-block">{agent.error_message}</div>
          )}
          {agent.output_data && (
            <div className="output-block">
              <div className="output-label">Output</div>
              <pre className="output-pre">{typeof agent.output_data === 'string' ? agent.output_data.slice(0, 2000) : JSON.stringify(agent.output_data, null, 2).slice(0, 2000)}</pre>
            </div>
          )}
          {agent.llm_calls.length > 0 && (
            <div className="calls-section">
              <div className="output-label">LLM Calls ({agent.llm_calls.length})</div>
              {agent.llm_calls.map((call) => (
                <div key={call.id} className="call-row">
                  <span className="call-model">{call.model}</span>
                  <span className="stat">{call.prompt_tokens}+{call.completion_tokens} tok</span>
                  <span className="stat">{call.latency_ms}ms</span>
                  <StatusDot status={call.status} />
                </div>
              ))}
            </div>
          )}
          {agent.tool_executions.length > 0 && (
            <div className="calls-section">
              <div className="output-label">Tool Calls ({agent.tool_executions.length})</div>
              {agent.tool_executions.map((call) => (
                <div key={call.id} className="call-row">
                  <span className="call-model">{call.tool_name}</span>
                  <span className="stat">{formatDuration(call.duration_seconds)}</span>
                  <StatusDot status={call.status} />
                </div>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  );
}

function StageRow({ stage, index }: { stage: StageExecution; index: number }) {
  const [expanded, setExpanded] = useState(false);
  const totalTokens = stage.agents.reduce((sum, a) => sum + a.total_tokens, 0);

  return (
    <div className={`stage-row ${stage.status}`}>
      <div className="stage-header" onClick={() => setExpanded(!expanded)}>
        <div className="stage-left">
          <span className="stage-index">{index + 1}</span>
          <StatusDot status={stage.status} />
          <span className="stage-name">{stage.stage_name}</span>
        </div>
        <div className="stage-stats">
          {totalTokens > 0 && <span className="stat">{formatTokens(totalTokens)} tok</span>}
          <span className="stat">{formatDuration(stage.duration_seconds)}</span>
          <span className={`stage-badge ${stage.status}`}>{stage.status}</span>
          <span className="expand-icon">{expanded ? '\u25B4' : '\u25BE'}</span>
        </div>
      </div>
      {expanded && (
        <div className="stage-detail">
          {stage.error_message && (
            <div className="error-block">{stage.error_message}</div>
          )}
          {stage.agents.map((agent) => (
            <AgentRow key={agent.id} agent={agent} />
          ))}
        </div>
      )}
    </div>
  );
}

export default function ExecutionView({ executionId, onClose }: { executionId: string; onClose: () => void }) {
  const [execution, setExecution] = useState<WorkflowExecution | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let active = true;
    let interval: ReturnType<typeof setInterval>;

    const load = () => {
      fetchExecution(executionId)
        .then((data) => { if (active) setExecution(data); })
        .catch((err) => { if (active) setError(err.message); });
    };

    load();
    // Poll while running
    interval = setInterval(load, 3000);

    return () => { active = false; clearInterval(interval); };
  }, [executionId]);

  // Stop polling when terminal
  useEffect(() => {
    if (execution && ['completed', 'failed', 'halted', 'timeout'].includes(execution.status)) {
      // one final fetch, then stop
    }
  }, [execution?.status]);

  if (error) {
    return (
      <div className="execution-view">
        <div className="exec-header">
          <button className="back-button" onClick={onClose}>&larr; Back</button>
          <span className="exec-error">Failed to load execution: {error}</span>
        </div>
      </div>
    );
  }

  if (!execution) {
    return (
      <div className="execution-view">
        <div className="exec-header">
          <button className="back-button" onClick={onClose}>&larr; Back</button>
          <span className="exec-loading">Loading execution...</span>
        </div>
      </div>
    );
  }

  const isTerminal = ['completed', 'failed', 'halted', 'timeout'].includes(execution.status);

  return (
    <div className="execution-view">
      <div className="exec-header">
        <button className="back-button" onClick={onClose}>&larr; Back</button>
        <div className="exec-title">
          <span className="exec-workflow-name">{execution.workflow_name}</span>
          <span className={`run-status ${execution.status}`}>{execution.status}</span>
          {!isTerminal && <span className="exec-live-dot" />}
        </div>
      </div>

      <div className="exec-summary">
        <div className="summary-item">
          <span className="summary-label">Duration</span>
          <span className="summary-value">{formatDuration(execution.duration_seconds)}</span>
        </div>
        <div className="summary-item">
          <span className="summary-label">Tokens</span>
          <span className="summary-value">{formatTokens(execution.total_tokens)}</span>
        </div>
        <div className="summary-item">
          <span className="summary-label">Stages</span>
          <span className="summary-value">{execution.stages.length}</span>
        </div>
        <div className="summary-item">
          <span className="summary-label">ID</span>
          <span className="summary-value mono">{execution.id.slice(0, 12)}</span>
        </div>
      </div>

      {execution.error_message && (
        <div className="error-block exec-error-block">{execution.error_message}</div>
      )}

      <div className="section-title">Pipeline Stages</div>
      <div className="stages-list">
        {execution.stages.map((stage, i) => (
          <StageRow key={stage.id} stage={stage} index={i} />
        ))}
      </div>
    </div>
  );
}

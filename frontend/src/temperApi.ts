import { fetchRun } from './api';

export interface LLMCall {
  id: string;
  model: string;
  provider: string;
  prompt_tokens: number;
  completion_tokens: number;
  total_tokens: number;
  latency_ms: number;
  status: string;
  response?: string;
}

export interface ToolCall {
  id: string;
  tool_name: string;
  input_params: Record<string, unknown>;
  output_data: Record<string, unknown>;
  status: string;
  duration_seconds: number;
}

export interface AgentExecution {
  id: string;
  agent_name: string;
  status: string;
  start_time: string | null;
  end_time: string | null;
  duration_seconds: number | null;
  total_tokens: number;
  num_llm_calls: number;
  num_tool_calls: number;
  output_data: string | null;
  error_message: string | null;
  llm_calls: LLMCall[];
  tool_executions: ToolCall[];
}

export interface StageExecution {
  id: string;
  stage_name: string;
  status: string;
  start_time: string | null;
  end_time: string | null;
  duration_seconds: number | null;
  input_data: Record<string, unknown> | null;
  output_data: string | null;
  error_message: string | null;
  agents: AgentExecution[];
}

export interface WorkflowExecution {
  id: string;
  workflow_name: string;
  workflow_version: string;
  status: string;
  start_time: string | null;
  end_time: string | null;
  duration_seconds: number | null;
  total_tokens: number;
  total_cost_usd: number;
  total_llm_calls: number;
  total_tool_calls: number;
  error_message: string | null;
  stages: StageExecution[];
}

export async function fetchExecution(runId: string): Promise<WorkflowExecution> {
  // Execution data is embedded in the run's result.execution field
  const run = await fetchRun(runId);
  const result = run.result as Record<string, unknown> | null;
  if (!result?.execution) {
    throw new Error('Execution details not available yet');
  }
  return result.execution as WorkflowExecution;
}

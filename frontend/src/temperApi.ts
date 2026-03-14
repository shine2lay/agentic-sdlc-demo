const TEMPER_API_URL = import.meta.env.VITE_TEMPER_API_URL || 'http://localhost:8421';

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

export async function fetchExecution(executionId: string): Promise<WorkflowExecution> {
  const res = await fetch(`${TEMPER_API_URL}/api/workflows/${executionId}`);
  if (!res.ok) throw new Error(`Failed to fetch execution: ${res.status}`);
  return res.json();
}

/**
 * Zustand store for static workflow execution data.
 * Loads a full snapshot from the REST API and flattens it into Maps for O(1) lookups.
 * No WebSocket or streaming state — data is fetched once (or re-fetched on demand).
 */
import { create } from 'zustand';
import { immer } from 'zustand/middleware/immer';
import { enableMapSet } from 'immer';
import { MAX_EVENT_LOG_SIZE } from './constants';
import type {
  WorkflowExecution,
  StageExecution,
  AgentExecution,
  LLMCall,
  ToolCall,
  Selection,
  EventLogEntry,
} from './types';

enableMapSet();

interface ExecutionState {
  workflow: WorkflowExecution | null;
  stages: Map<string, StageExecution>;
  agents: Map<string, AgentExecution>;
  llmCalls: Map<string, LLMCall>;
  toolCalls: Map<string, ToolCall>;
  selection: Selection | null;
  eventLog: EventLogEntry[];
  expandedStages: Set<string>;
  stageDetailId: string | null;

  applySnapshot: (workflow: WorkflowExecution) => void;
  reset: () => void;
  select: (type: Selection['type'], id: string) => void;
  clearSelection: () => void;
  toggleStageExpanded: (stageName: string) => void;
  openStageDetail: (stageId: string) => void;
  closeStageDetail: () => void;
}

/**
 * Build a full chronological event log from a completed workflow snapshot.
 * Used on load from REST API when no prior diff state exists.
 */
function _buildSnapshotEvents(workflow: WorkflowExecution): EventLogEntry[] {
  const events: EventLogEntry[] = [];

  if (workflow.start_time) {
    events.push({
      timestamp: workflow.start_time,
      event_type: 'workflow_start',
      label: workflow.workflow_name,
      data: { execution_id: workflow.id, status: workflow.status },
    });
  }

  for (const stage of workflow.stages ?? []) {
    const stageLabel = stage.stage_name ?? stage.name ?? stage.id;

    if (stage.start_time) {
      events.push({
        timestamp: stage.start_time,
        event_type: 'stage_start',
        label: stageLabel,
        data: { stage_id: stage.id, status: stage.status },
      });
    }

    for (const agent of stage.agents ?? []) {
      const agentLabel = agent.agent_name ?? agent.name ?? agent.id;

      if (agent.start_time) {
        events.push({
          timestamp: agent.start_time,
          event_type: 'agent_start',
          label: agentLabel,
          data: { agent_id: agent.id, stage_id: stage.id, status: agent.status },
        });
      }

      for (const llm of agent.llm_calls ?? []) {
        if (llm.start_time) {
          events.push({
            timestamp: llm.start_time,
            event_type: 'llm_call',
            label: llm.model ?? llm.provider ?? '',
            data: { llm_call_id: llm.id, agent_id: agent.id },
          });
        }
      }

      for (const tool of agent.tool_calls ?? []) {
        if (tool.start_time) {
          events.push({
            timestamp: tool.start_time,
            event_type: 'tool_call',
            label: tool.tool_name ?? '',
            data: { tool_execution_id: tool.id, agent_id: agent.id },
          });
        }
      }

      if (agent.end_time) {
        events.push({
          timestamp: agent.end_time,
          event_type: 'agent_end',
          label: agentLabel,
          data: { agent_id: agent.id, stage_id: stage.id, status: agent.status },
        });
      }
    }

    if (stage.end_time) {
      events.push({
        timestamp: stage.end_time,
        event_type: 'stage_end',
        label: stageLabel,
        data: { stage_id: stage.id, status: stage.status },
      });
    }
  }

  if (workflow.end_time) {
    events.push({
      timestamp: workflow.end_time,
      event_type: 'workflow_end',
      label: workflow.workflow_name,
      data: { execution_id: workflow.id, status: workflow.status },
    });
  }

  events.sort((a, b) => a.timestamp.localeCompare(b.timestamp));
  return events;
}

export const useExecutionStore = create<ExecutionState>()(
  immer((set) => ({
    workflow: null,
    stages: new Map(),
    agents: new Map(),
    llmCalls: new Map(),
    toolCalls: new Map(),
    selection: null,
    eventLog: [],
    expandedStages: new Set(),
    stageDetailId: null,

    applySnapshot: (workflow) =>
      set((state) => {
        // Clear selection when a new workflow loads to avoid stale selection state
        state.selection = null;

        // Build full event log from the snapshot
        const snapshotEvents = _buildSnapshotEvents(workflow);
        state.eventLog = snapshotEvents.slice(-MAX_EVENT_LOG_SIZE);

        state.workflow = workflow;
        state.stages = new Map();
        state.agents = new Map();
        state.llmCalls = new Map();
        state.toolCalls = new Map();

        for (const stage of workflow.stages ?? []) {
          state.stages.set(stage.id, stage);
          for (const agent of stage.agents ?? []) {
            state.agents.set(agent.id, agent);
            for (const llm of agent.llm_calls ?? []) {
              state.llmCalls.set(llm.id, llm);
            }
            for (const tool of agent.tool_calls ?? []) {
              state.toolCalls.set(tool.id, tool);
            }
          }
        }
      }),

    reset: () =>
      set((state) => {
        state.workflow = null;
        state.stages = new Map();
        state.agents = new Map();
        state.llmCalls = new Map();
        state.toolCalls = new Map();
        state.eventLog = [];
        state.selection = null;
        state.expandedStages = new Set();
        state.stageDetailId = null;
      }),

    select: (type, id) =>
      set((state) => {
        state.selection = { type, id };
      }),

    clearSelection: () =>
      set((state) => {
        state.selection = null;
      }),

    toggleStageExpanded: (stageName) =>
      set((state) => {
        if (state.expandedStages.has(stageName)) {
          state.expandedStages.delete(stageName);
        } else {
          state.expandedStages.add(stageName);
        }
      }),

    openStageDetail: (stageId) =>
      set((state) => {
        state.stageDetailId = stageId;
      }),

    closeStageDetail: () =>
      set((state) => {
        state.stageDetailId = null;
      }),
  })),
);

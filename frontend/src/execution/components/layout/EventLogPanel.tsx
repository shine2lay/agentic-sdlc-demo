import { useRef, useEffect, useState, useCallback, useMemo } from 'react';
import { useExecutionStore } from '../../store';
import { formatTimestamp, cn } from '../../utils';
import type { SelectionType } from '../../types';

const SEARCH_DEBOUNCE_MS = 300;

const EVENT_TYPE_STYLES: Record<string, string> = {
  stage: 'bg-[#42a5f5]/20 text-[#42a5f5] border border-[#42a5f5]/30',
  agent: 'bg-[#66bb6a]/20 text-[#66bb6a] border border-[#66bb6a]/30',
  llm: 'bg-[#ab47bc]/20 text-[#ab47bc] border border-[#ab47bc]/30',
  tool: 'bg-[#ffa726]/20 text-[#ffa726] border border-[#ffa726]/30',
  workflow: 'bg-[#4fc3f7]/20 text-[#4fc3f7] border border-[#4fc3f7]/30',
};

const FILTER_CATEGORIES = ['all', 'workflow', 'stage', 'agent', 'llm', 'tool'] as const;

function eventStyle(eventType: string): string {
  const prefix = eventType.split('_')[0];
  return EVENT_TYPE_STYLES[prefix] ?? EVENT_TYPE_STYLES.workflow;
}

/** Map event_type to a SelectionType + entity ID, or null if not selectable */
function resolveSelection(
  eventType: string,
  data?: Record<string, unknown>,
): { type: SelectionType; id: string } | null {
  if (!data) return null;
  const prefix = eventType.split('_')[0];

  switch (prefix) {
    case 'stage': {
      const id = (data.stage_id ?? data.id) as string | undefined;
      return id ? { type: 'stage', id } : null;
    }
    case 'agent': {
      const id = (data.agent_id ?? data.id) as string | undefined;
      return id ? { type: 'agent', id } : null;
    }
    case 'llm': {
      const id = (data.llm_call_id ?? data.id) as string | undefined;
      return id ? { type: 'llmCall', id } : null;
    }
    case 'tool': {
      const id = (data.tool_execution_id ?? data.id) as string | undefined;
      return id ? { type: 'toolCall', id } : null;
    }
    default:
      return null;
  }
}

export function EventLogPanel() {
  const eventLog = useExecutionStore((s) => s.eventLog);
  const select = useExecutionStore((s) => s.select);
  const bottomRef = useRef<HTMLDivElement>(null);
  const containerRef = useRef<HTMLDivElement>(null);
  const [filter, setFilter] = useState<string | null>(null);
  const [searchInput, setSearchInput] = useState('');
  const [searchText, setSearchText] = useState('');
  const [isAtBottom, setIsAtBottom] = useState(false);
  const [newEvents, setNewEvents] = useState(0);

  // Debounce search input to avoid expensive re-filtering on every keystroke
  useEffect(() => {
    const timer = setTimeout(() => setSearchText(searchInput), SEARCH_DEBOUNCE_MS);
    return () => clearTimeout(timer);
  }, [searchInput]);

  const handleScroll = useCallback(() => {
    const el = containerRef.current;
    if (!el) return;
    const atBottom = el.scrollHeight - el.scrollTop - el.clientHeight < 30;
    setIsAtBottom(atBottom);
    if (atBottom) setNewEvents(0);
  }, []);

  // Auto-scroll only when user has scrolled to the bottom themselves
  useEffect(() => {
    if (isAtBottom) {
      bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
    } else {
      setNewEvents((n) => n + 1);
    }
  }, [eventLog.length]); // eslint-disable-line react-hooks/exhaustive-deps -- intentional: only on new events

  const handleClick = useCallback(
    (eventType: string, data?: Record<string, unknown>) => {
      const sel = resolveSelection(eventType, data);
      if (sel) select(sel.type, sel.id);
    },
    [select],
  );

  const handleKeyActivate = useCallback(
    (e: React.KeyboardEvent, eventType: string, data?: Record<string, unknown>) => {
      if (e.key === 'Enter' || e.key === ' ') {
        e.preventDefault();
        handleClick(eventType, data);
      }
    },
    [handleClick],
  );

  const scrollToBottom = useCallback(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
    setNewEvents(0);
  }, []);

  const categoryCounts = useMemo(() => {
    const counts: Record<string, number> = { all: eventLog.length };
    for (const e of eventLog) {
      const prefix = e.event_type.split('_')[0];
      counts[prefix] = (counts[prefix] ?? 0) + 1;
    }
    return counts;
  }, [eventLog]);

  const filtered = useMemo(() => {
    return eventLog
      .filter((e) => e.event_type !== 'llm_stream_batch')
      .filter((e) => !filter || e.event_type.startsWith(filter))
      .filter(
        (e) =>
          !searchText ||
          e.label.toLowerCase().includes(searchText.toLowerCase()) ||
          e.event_type.includes(searchText.toLowerCase()),
      );
  }, [eventLog, filter, searchText]);

  if (eventLog.length === 0) {
    return (
      <div className="flex-1 flex flex-col items-center justify-center text-gray-500 gap-2">
        <span className="text-2xl">&#x1F4CB;</span>
        <span className="text-sm">No events yet</span>
        <span className="text-xs text-gray-600">Events will appear here as the workflow executes</span>
      </div>
    );
  }

  return (
    <div className="flex-1 flex flex-col min-h-0">
      {/* Filter chips + search */}
      <div className="flex items-center gap-2 px-4 py-2 border-b border-gray-700/30 shrink-0 flex-wrap">
        {FILTER_CATEGORIES.map((f) => (
          <button
            key={f}
            onClick={() => setFilter(f === 'all' ? null : f)}
            className={cn(
              'px-2 py-0.5 rounded text-xs transition-colors',
              filter === f || (f === 'all' && !filter)
                ? 'bg-blue-500/20 text-blue-400'
                : 'text-gray-500 hover:text-gray-200',
            )}
          >
            {f}
            {categoryCounts[f] != null && (
              <span className="ml-1 text-[10px] opacity-60">({categoryCounts[f]})</span>
            )}
          </button>
        ))}
        <input
          type="text"
          placeholder="Search events..."
          value={searchInput}
          onChange={(e) => setSearchInput(e.target.value)}
          className="px-2 py-0.5 rounded text-xs bg-gray-800 border border-gray-700 text-gray-200 placeholder:text-gray-600 focus:outline-none focus:ring-1 focus:ring-blue-500 w-full sm:w-40"
        />
        <span className="ml-auto text-xs text-gray-500" aria-live="polite">
          {filtered.length} events
        </span>
      </div>

      {/* Event list */}
      <div
        ref={containerRef}
        onScroll={handleScroll}
        className="flex-1 overflow-y-auto px-4 py-2 space-y-1 min-h-0 relative"
        role="log"
        aria-label="Event log"
      >
        {!isAtBottom && newEvents > 0 && (
          <button
            onClick={scrollToBottom}
            className="sticky top-0 z-20 w-full bg-blue-500/10 border-b border-blue-500/30 px-3 py-1 text-xs text-blue-400 text-center hover:bg-blue-500/20 transition-colors"
          >
            {newEvents} new event{newEvents !== 1 ? 's' : ''} below
          </button>
        )}
        {filtered.map((entry, idx) => {
          const sel = resolveSelection(entry.event_type, entry.data);
          return (
            <div
              key={idx}
              className={cn(
                'flex items-center gap-3 py-1 text-sm border-b border-gray-700/30 last:border-0',
                sel && 'cursor-pointer hover:bg-gray-800/50',
              )}
              onClick={sel ? () => handleClick(entry.event_type, entry.data) : undefined}
              onKeyDown={sel ? (e) => handleKeyActivate(e, entry.event_type, entry.data) : undefined}
              role={sel ? 'button' : undefined}
              tabIndex={sel ? 0 : undefined}
            >
              <span className="font-mono text-xs text-gray-500 shrink-0 w-28">
                {formatTimestamp(entry.timestamp)}
              </span>
              <span
                className={cn(
                  'inline-flex items-center px-1.5 py-0.5 rounded text-xs shrink-0',
                  eventStyle(entry.event_type),
                )}
              >
                {entry.event_type}
              </span>
              <span className="text-gray-300 truncate">{entry.label}</span>
            </div>
          );
        })}
        <div ref={bottomRef} />
      </div>
    </div>
  );
}

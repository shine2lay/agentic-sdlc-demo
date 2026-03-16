import { useState, useEffect, useCallback } from 'react';
import { cn } from '../../utils';

const TAB_STORAGE_KEY = 'sdlc-demo-active-tab';

interface ViewTabsProps {
  dagContent: React.ReactNode;
  timelineContent: React.ReactNode;
  eventLogContent: React.ReactNode;
  llmCallsContent: React.ReactNode;
  activeTab?: string;
  onTabChange?: (tab: string) => void;
  stageCount?: number;
  eventCount?: number;
  llmCallCount?: number;
}

function CountBadge({ count }: { count?: number }) {
  if (count == null || count === 0) return null;
  return (
    <span className="ml-1 text-[9px] font-mono opacity-60 tabular-nums">{count}</span>
  );
}

const TABS = [
  { value: 'dag', label: 'DAG', shortcut: '1' },
  { value: 'timeline', label: 'Timeline', shortcut: '2' },
  { value: 'eventlog', label: 'Event Log', shortcut: '3' },
  { value: 'llmcalls', label: 'LLM Calls', shortcut: '4' },
] as const;

export function ViewTabs({
  dagContent,
  timelineContent,
  eventLogContent,
  llmCallsContent,
  activeTab: controlledTab,
  onTabChange,
  stageCount,
  eventCount,
  llmCallCount,
}: ViewTabsProps) {
  const [internalTab, setInternalTab] = useState(() => {
    return localStorage.getItem(TAB_STORAGE_KEY) ?? 'dag';
  });

  const activeTab = controlledTab ?? internalTab;

  const handleChange = useCallback(
    (tab: string) => {
      setInternalTab(tab);
      onTabChange?.(tab);
    },
    [onTabChange],
  );

  useEffect(() => {
    localStorage.setItem(TAB_STORAGE_KEY, activeTab);
  }, [activeTab]);

  return (
    <div className="flex-1 flex flex-col min-h-0">
      {/* Tab bar */}
      <div className="flex items-end gap-0.5 px-4 pt-2 border-b border-gray-700/60 shrink-0 bg-gray-900/30">
        {TABS.map((tab) => {
          const isActive = activeTab === tab.value;
          return (
            <button
              key={tab.value}
              onClick={() => handleChange(tab.value)}
              className={cn(
                'px-4 py-2 text-sm font-medium border-b-2 transition-colors',
                isActive
                  ? 'border-blue-500 text-blue-400'
                  : 'border-transparent text-gray-400 hover:text-gray-200 hover:border-gray-600',
              )}
            >
              {tab.label}
              {tab.value === 'dag' && <CountBadge count={stageCount} />}
              {tab.value === 'eventlog' && <CountBadge count={eventCount} />}
              {tab.value === 'llmcalls' && <CountBadge count={llmCallCount} />}
              <span className="ml-1.5 text-[10px] opacity-40 hidden sm:inline">{tab.shortcut}</span>
            </button>
          );
        })}
      </div>

      {/* Tab content */}
      <div className="flex-1 min-h-0">
        {activeTab === 'dag' && dagContent}
        {activeTab === 'timeline' && timelineContent}
        {activeTab === 'eventlog' && eventLogContent}
        {activeTab === 'llmcalls' && llmCallsContent}
      </div>
    </div>
  );
}

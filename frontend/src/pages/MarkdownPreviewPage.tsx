import { useState, useEffect, useMemo } from 'react';
import { useQuery } from '@tanstack/react-query';
import { fetchMarkdownPreviewConfig } from '../api';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';

export function MarkdownPreviewPage() {
  const { data: config, isLoading, isError } = useQuery({
    queryKey: ['markdown-preview-config'],
    queryFn: fetchMarkdownPreviewConfig,
  });

  const [markdown, setMarkdown] = useState('');
  const [debouncedMarkdown, setDebouncedMarkdown] = useState('');
  const [initialized, setInitialized] = useState(false);

  useEffect(() => {
    if (config && !initialized) {
      setMarkdown(config.default_markdown);
      setDebouncedMarkdown(config.default_markdown);
      setInitialized(true);
    }
  }, [config, initialized]);

  useEffect(() => {
    const ms = config?.debounce_ms ?? 200;
    const timer = setTimeout(() => setDebouncedMarkdown(markdown), ms);
    return () => clearTimeout(timer);
  }, [markdown, config?.debounce_ms]);

  if (isLoading) return <div className="p-8 text-center text-[var(--temper-text-muted)]">Loading...</div>;
  if (isError || !config) return <div className="p-8 text-center text-red-400">Failed to load config.</div>;

  return (
    <div className="flex flex-col h-full overflow-hidden">
      <h1 className="text-2xl font-bold text-[var(--temper-text)] p-4 pb-2 text-center">{config.title}</h1>
      <div className="flex flex-1 min-h-0 p-4 pt-2 gap-4 flex-col md:flex-row">
        <div className="flex-1 min-h-0 flex flex-col min-w-0">
          <label className="text-sm font-medium text-[var(--temper-text-muted)] mb-1">Editor</label>
          <textarea
            className="flex-1 w-full resize-none p-3 bg-[var(--temper-panel)] border border-[var(--temper-border)] rounded text-[var(--temper-text)] font-mono text-sm focus:outline-none focus:border-[var(--temper-accent)]"
            value={markdown}
            onChange={e => setMarkdown(e.target.value)}
            placeholder={config.editor_placeholder}
          />
        </div>
        <div className="flex-1 min-h-0 flex flex-col min-w-0">
          <label className="text-sm font-medium text-[var(--temper-text-muted)] mb-1">Preview</label>
          <div className="flex-1 overflow-auto p-3 bg-[var(--temper-panel)] border border-[var(--temper-border)] rounded prose prose-invert max-w-none">
            <ReactMarkdown remarkPlugins={[remarkGfm]}>{debouncedMarkdown}</ReactMarkdown>
          </div>
        </div>
      </div>
    </div>
  );
}

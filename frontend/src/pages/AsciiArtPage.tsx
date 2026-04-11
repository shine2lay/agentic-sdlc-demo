import { useState, useEffect } from 'react';
import { useQuery } from '@tanstack/react-query';
import { fetchAsciiArtConfig, generateAsciiArt, AsciiArtResponse } from '../api';

export function AsciiArtPage() {
  const { data: config, isLoading, isError } = useQuery({
    queryKey: ['ascii-art-config'],
    queryFn: fetchAsciiArtConfig,
  });

  const [text, setText] = useState('');
  const [result, setResult] = useState<AsciiArtResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [initialized, setInitialized] = useState(false);

  useEffect(() => {
    if (config && !initialized) {
      setText(config.default_text);
      setInitialized(true);
    }
  }, [config, initialized]);

  useEffect(() => {
    if (!initialized) return;

    const trimmed = text.trim();
    if (!trimmed) {
      setResult(null);
      setError(null);
      return;
    }

    const timer = setTimeout(async () => {
      setLoading(true);
      setError(null);
      try {
        const res = await generateAsciiArt(text);
        setResult(res);
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to generate ASCII art');
      } finally {
        setLoading(false);
      }
    }, 300);

    return () => clearTimeout(timer);
  }, [text, initialized]);

  if (isLoading) return <div className="p-8 text-center text-[var(--temper-text-muted)]">Loading...</div>;
  if (isError || !config) return <div className="p-8 text-center text-red-400">Failed to load config.</div>;

  return (
    <div className="flex flex-col h-full overflow-hidden">
      <h1 className="text-2xl font-bold text-[var(--temper-text)] p-4 pb-2 text-center">{config.title}</h1>
      <div className="flex flex-col flex-1 min-h-0 p-4 pt-2 gap-4">
        <div>
          <input
            type="text"
            maxLength={config.max_length}
            value={text}
            onChange={e => setText(e.target.value)}
            className="w-full p-3 bg-[var(--temper-panel)] border border-[var(--temper-border)] rounded text-[var(--temper-text)] font-mono focus:outline-none focus:border-[var(--temper-accent)]"
            placeholder="Enter text..."
          />
          <p className="text-[var(--temper-text-muted)] text-sm mt-1">Supported: {config.supported_characters}</p>
        </div>
        {error && <p className="text-red-400 text-sm">{error}</p>}
        {loading && <p className="text-[var(--temper-text-muted)] text-sm">Generating...</p>}
        <pre className="overflow-x-auto bg-[var(--temper-panel)] border border-[var(--temper-border)] rounded p-4 font-mono text-sm text-[var(--temper-text)] whitespace-pre leading-tight">
          {result?.art || ''}
        </pre>
      </div>
    </div>
  );
}

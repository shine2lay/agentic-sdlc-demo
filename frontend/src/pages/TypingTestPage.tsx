import { useState, useEffect, useRef, useCallback } from 'react';
import { useQuery } from '@tanstack/react-query';
import { fetchTypingTestConfig, calculateTypingSpeed, TypingTestResult } from '../api';

export function TypingTestPage() {
  const { data: config, isLoading, error } = useQuery({
    queryKey: ['typing-test-config'],
    queryFn: fetchTypingTestConfig,
  });

  const [sentence, setSentence] = useState('');
  const [typed, setTyped] = useState('');
  const [status, setStatus] = useState<'idle' | 'running' | 'finished'>('idle');
  const [startTime, setStartTime] = useState<number | null>(null);
  const [elapsedMs, setElapsedMs] = useState(0);
  const [result, setResult] = useState<TypingTestResult | null>(null);
  const intervalRef = useRef<number | null>(null);

  useEffect(() => {
    if (config && !sentence) {
      setSentence(config.sentences[Math.floor(Math.random() * config.sentences.length)]);
    }
  }, [config, sentence]);

  useEffect(() => {
    return () => {
      if (intervalRef.current) clearInterval(intervalRef.current);
    };
  }, []);

  const handleChange = useCallback((e: React.ChangeEvent<HTMLTextAreaElement>) => {
    const value = e.target.value;
    if (status === 'finished') return;

    let currentStartTime = startTime;

    if (status === 'idle') {
      const now = Date.now();
      currentStartTime = now;
      setStartTime(now);
      setStatus('running');
      intervalRef.current = window.setInterval(() => {
        setElapsedMs(Date.now() - now);
      }, 100);
    }

    setTyped(value);

    if (value.length >= sentence.length && status !== 'finished') {
      if (intervalRef.current) {
        clearInterval(intervalRef.current);
        intervalRef.current = null;
      }
      setStatus('finished');
      const elapsed = (Date.now() - (currentStartTime || Date.now())) / 1000;
      calculateTypingSpeed(sentence, value, elapsed).then(setResult).catch(console.error);
    }
  }, [status, sentence, startTime]);

  const handleTryAgain = useCallback(() => {
    if (intervalRef.current) {
      clearInterval(intervalRef.current);
      intervalRef.current = null;
    }
    setTyped('');
    setStatus('idle');
    setStartTime(null);
    setElapsedMs(0);
    setResult(null);
    if (config) {
      setSentence(config.sentences[Math.floor(Math.random() * config.sentences.length)]);
    }
  }, [config]);

  if (isLoading) {
    return <div className="flex items-center justify-center h-full text-[var(--temper-text)]">Loading...</div>;
  }

  if (error) {
    return <div className="flex items-center justify-center h-full text-red-500">Failed to load typing test config.</div>;
  }

  return (
    <div className="flex flex-col items-center justify-center h-full gap-6 p-6 bg-[var(--temper-bg)]">
      <h1 className="text-3xl font-bold text-[var(--temper-text)]">{config?.title}</h1>

      <div className="max-w-2xl w-full bg-[var(--temper-panel)] rounded-lg p-6 border border-[var(--temper-border)]">
        <div className="mb-4 font-mono text-lg leading-relaxed">
          {sentence.split('').map((char, i) => {
            let color = 'text-[var(--temper-text-muted)]';
            if (i < typed.length) {
              color = typed[i] === char ? 'text-green-500' : 'text-red-500';
            }
            return <span key={i} className={color}>{char}</span>;
          })}
        </div>

        <textarea
          className="w-full p-3 rounded border border-[var(--temper-border)] bg-[var(--temper-bg)] text-[var(--temper-text)] font-mono resize-none"
          rows={3}
          value={typed}
          onChange={handleChange}
          onPaste={(e) => e.preventDefault()}
          disabled={status === 'finished'}
          placeholder="Start typing here..."
        />

        <div className="mt-3 text-sm text-[var(--temper-text-muted)]">
          Elapsed: {(elapsedMs / 1000).toFixed(1)}s
        </div>

        {result && (
          <div className="mt-4 p-4 rounded bg-[var(--temper-bg)] border border-[var(--temper-border)]">
            <p className="text-xl font-bold text-[var(--temper-accent)]">{result.wpm} WPM</p>
            <p className="text-[var(--temper-text)]">Accuracy: {result.accuracy}%</p>
            <p className="text-[var(--temper-text)]">Time: {result.elapsed_seconds.toFixed(1)}s</p>
            <p className="text-[var(--temper-text-muted)] text-sm">
              {result.correct_chars} / {result.total_chars} correct characters
            </p>
          </div>
        )}

        {status === 'finished' && (
          <button
            onClick={handleTryAgain}
            className="mt-4 px-4 py-2 bg-[var(--temper-accent)] text-white rounded hover:opacity-90"
          >
            Try Again
          </button>
        )}
      </div>
    </div>
  );
}

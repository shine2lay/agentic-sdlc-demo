import { useState, useEffect, useRef, useCallback } from 'react';
import { useQuery } from '@tanstack/react-query';
import { fetchCountdownTimerConfig } from '../api';

export function TimerPage() {
  const { data: config, isLoading, isError } = useQuery({
    queryKey: ['countdown-timer-config'],
    queryFn: fetchCountdownTimerConfig,
  });

  const [minutes, setMinutes] = useState(0);
  const [seconds, setSeconds] = useState(0);
  const [status, setStatus] = useState<'idle' | 'running' | 'paused' | 'finished'>('idle');
  const [remainingMs, setRemainingMs] = useState(0);
  const endTimeRef = useRef<number | null>(null);
  const intervalRef = useRef<number | null>(null);

  useEffect(() => {
    if (config) {
      setMinutes(config.default_minutes);
      setSeconds(config.default_seconds);
      setRemainingMs((config.default_minutes * 60 + config.default_seconds) * 1000);
    }
  }, [config]);

  useEffect(() => {
    return () => {
      if (intervalRef.current) clearInterval(intervalRef.current);
    };
  }, []);

  const startTimer = useCallback(() => {
    if (intervalRef.current) clearInterval(intervalRef.current);
    const ms = status === 'paused' ? remainingMs : (minutes * 60 + seconds) * 1000;
    if (ms <= 0) return;
    endTimeRef.current = Date.now() + ms;
    setStatus('running');
    intervalRef.current = window.setInterval(() => {
      const left = endTimeRef.current! - Date.now();
      if (left <= 0) {
        setRemainingMs(0);
        setStatus('finished');
        if (intervalRef.current) clearInterval(intervalRef.current);
      } else {
        setRemainingMs(left);
      }
    }, 100);
  }, [minutes, seconds, remainingMs, status]);

  const stopTimer = useCallback(() => {
    if (intervalRef.current) clearInterval(intervalRef.current);
    setStatus('paused');
  }, []);

  const resetTimer = useCallback(() => {
    if (intervalRef.current) clearInterval(intervalRef.current);
    endTimeRef.current = null;
    setStatus('idle');
    setRemainingMs((minutes * 60 + seconds) * 1000);
  }, [minutes, seconds]);

  if (isLoading) return <div className="flex items-center justify-center h-full text-[var(--temper-text)]">Loading...</div>;
  if (isError || !config) return <div className="flex items-center justify-center h-full text-red-500">Failed to load timer config</div>;

  const displayMin = Math.floor(remainingMs / 60000);
  const displaySec = Math.floor((remainingMs % 60000) / 1000);
  const formatted = `${String(displayMin).padStart(2, '0')}:${String(displaySec).padStart(2, '0')}`;

  const timeColor = status === 'running' ? '#22c55e' : status === 'paused' ? '#eab308' : status === 'finished' ? '#ef4444' : 'var(--temper-text)';
  const totalDuration = (minutes * 60 + seconds) * 1000;

  return (
    <div className="flex flex-col h-full overflow-hidden">
      <h1 className="text-2xl font-bold text-[var(--temper-text)] p-4 pb-2 text-center">{config.title}</h1>
      <div className="flex flex-col items-center gap-4 p-4 pt-2">
        <div className="flex gap-4 items-end">
          <label className="flex flex-col text-[var(--temper-text-muted)] text-sm">
            Minutes
            <input
              type="number"
              min={0}
              max={99}
              value={minutes}
              disabled={status === 'running'}
              onChange={(e) => {
                const v = Math.max(0, Math.min(99, parseInt(e.target.value) || 0));
                setMinutes(v);
                if (status === 'idle') setRemainingMs((v * 60 + seconds) * 1000);
              }}
              className="mt-1 w-20 px-2 py-1 rounded bg-[var(--temper-panel)] border border-[var(--temper-border)] text-[var(--temper-text)] text-center"
            />
          </label>
          <label className="flex flex-col text-[var(--temper-text-muted)] text-sm">
            Seconds
            <input
              type="number"
              min={0}
              max={59}
              value={seconds}
              disabled={status === 'running'}
              onChange={(e) => {
                const v = Math.max(0, Math.min(59, parseInt(e.target.value) || 0));
                setSeconds(v);
                if (status === 'idle') setRemainingMs((minutes * 60 + v) * 1000);
              }}
              className="mt-1 w-20 px-2 py-1 rounded bg-[var(--temper-panel)] border border-[var(--temper-border)] text-[var(--temper-text)] text-center"
            />
          </label>
        </div>
        <div className="text-6xl font-mono" style={{ color: timeColor }}>{formatted}</div>
        <div className="flex gap-3">
          <button
            disabled={status === 'running' || totalDuration === 0}
            onClick={startTimer}
            className="px-4 py-2 rounded bg-[var(--temper-accent)] text-white disabled:opacity-50 disabled:cursor-not-allowed"
          >
            Start
          </button>
          <button
            disabled={status !== 'running'}
            onClick={stopTimer}
            className="px-4 py-2 rounded bg-[var(--temper-accent)] text-white disabled:opacity-50 disabled:cursor-not-allowed"
          >
            Stop
          </button>
          <button
            disabled={status === 'idle'}
            onClick={resetTimer}
            className="px-4 py-2 rounded bg-[var(--temper-accent)] text-white disabled:opacity-50 disabled:cursor-not-allowed"
          >
            Reset
          </button>
        </div>
      </div>
    </div>
  );
}

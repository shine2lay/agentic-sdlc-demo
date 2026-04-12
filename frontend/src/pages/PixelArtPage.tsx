import { useState, useRef, useCallback, useEffect } from 'react';
import { useQuery } from '@tanstack/react-query';
import { fetchPixelArtConfig } from '../api';

export function PixelArtPage() {
  const { data: config, isLoading, isError } = useQuery({
    queryKey: ['pixel-art-config'],
    queryFn: fetchPixelArtConfig,
  });

  const [grid, setGrid] = useState<string[]>(() => Array(256).fill('#ffffff'));
  const [selectedColor, setSelectedColor] = useState<string>('#000000');
  const [initialized, setInitialized] = useState(false);
  const isDrawing = useRef(false);

  useEffect(() => {
    if (config && !initialized) {
      setGrid(Array(config.grid_size * config.grid_size).fill(config.default_color));
      setSelectedColor(config.palette_colors[0] || '#000000');
      setInitialized(true);
    }
  }, [config, initialized]);

  const paintCell = useCallback((index: number) => {
    setGrid(prev => {
      const next = [...prev];
      next[index] = selectedColor;
      return next;
    });
  }, [selectedColor]);

  if (isLoading) return <div className="p-8 text-center text-[var(--temper-text-muted)]">Loading...</div>;
  if (isError || !config) return <div className="p-8 text-center text-red-400">Failed to load config.</div>;

  return (
    <div className="flex flex-col h-full overflow-hidden">
      <h1 className="text-2xl font-bold text-[var(--temper-text)] p-4 pb-2 text-center">{config.title}</h1>
      <div className="flex flex-col items-center gap-4 p-4 pt-2">
        <div className="flex gap-2 flex-wrap justify-center">
          {config.palette_colors.map(c => (
            <button
              key={c}
              onClick={() => setSelectedColor(c)}
              style={{ backgroundColor: c }}
              aria-label={`Select color ${c}`}
              className={`w-8 h-8 rounded border-2 ${c === selectedColor ? 'ring-2 ring-offset-2 ring-[var(--temper-accent)]' : 'border-[var(--temper-border)]'}`}
            />
          ))}
        </div>
        <div
          style={{
            display: 'grid',
            gridTemplateColumns: `repeat(${config.grid_size}, ${config.pixel_size_px}px)`,
            gap: config.show_gridlines ? `${config.grid_line_width_px}px` : '0px',
            backgroundColor: config.show_gridlines ? config.grid_line_color : 'transparent',
          }}
          onMouseUp={() => { isDrawing.current = false; }}
          onMouseLeave={() => { isDrawing.current = false; }}
          onDragStart={e => e.preventDefault()}
          className="select-none"
        >
          {grid.map((cellColor, index) => (
            <div
              key={index}
              style={{
                width: config.pixel_size_px,
                height: config.pixel_size_px,
                backgroundColor: cellColor,
              }}
              className="cursor-crosshair select-none"
              onMouseDown={() => { isDrawing.current = true; paintCell(index); }}
              onMouseEnter={() => { if (isDrawing.current) paintCell(index); }}
            />
          ))}
        </div>
        <button
          onClick={() => setGrid(Array(config.grid_size * config.grid_size).fill(config.default_color))}
          className="px-4 py-2 rounded bg-[var(--temper-accent)] text-white hover:opacity-90"
        >
          Clear
        </button>
      </div>
    </div>
  );
}

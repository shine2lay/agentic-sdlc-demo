import { useState, useEffect } from 'react';
import { useQuery } from '@tanstack/react-query';
import { fetchColorPickerConfig } from '../api';

const hexToRgb = (hex: string): { r: number; g: number; b: number } => {
  const result = /^#([a-f\d]{2})([a-f\d]{2})([a-f\d]{2})$/i.exec(hex);
  return result ? { r: parseInt(result[1], 16), g: parseInt(result[2], 16), b: parseInt(result[3], 16) } : { r: 0, g: 0, b: 0 };
};

const rgbToHsl = (r: number, g: number, b: number): { h: number; s: number; l: number } => {
  r /= 255; g /= 255; b /= 255;
  const max = Math.max(r, g, b), min = Math.min(r, g, b);
  let h = 0, s = 0;
  const l = (max + min) / 2;
  if (max !== min) {
    const d = max - min;
    s = l > 0.5 ? d / (2 - max - min) : d / (max + min);
    switch (max) {
      case r: h = ((g - b) / d + (g < b ? 6 : 0)) / 6; break;
      case g: h = ((b - r) / d + 2) / 6; break;
      case b: h = ((r - g) / d + 4) / 6; break;
    }
  }
  return { h: Math.round(h * 360), s: Math.round(s * 100), l: Math.round(l * 100) };
};

export function ColorPickerPage() {
  const { data: config, isLoading, isError } = useQuery({
    queryKey: ['color-picker-config'],
    queryFn: fetchColorPickerConfig,
  });

  const [color, setColor] = useState('#000000');
  const [initialized, setInitialized] = useState(false);

  useEffect(() => {
    if (config && !initialized) {
      setColor(config.default_color);
      setInitialized(true);
    }
  }, [config, initialized]);

  if (isLoading) return <div className="p-8 text-center text-[var(--temper-text-muted)]">Loading...</div>;
  if (isError || !config) return <div className="p-8 text-center text-red-400">Failed to load config.</div>;

  const rgb = hexToRgb(color);
  const hsl = rgbToHsl(rgb.r, rgb.g, rgb.b);

  return (
    <div className="flex flex-col h-full overflow-hidden">
      <h1 className="text-2xl font-bold text-[var(--temper-text)] p-4 pb-2 text-center">{config.title}</h1>
      <div className="flex flex-col items-center gap-4 p-4 pt-2">
        <input type="color" value={color} onChange={e => setColor(e.target.value)} className="w-20 h-20 cursor-pointer" />
        <div className="flex gap-2 flex-wrap justify-center">
          {config.preset_colors.map(swatch => (
            <button
              key={swatch}
              onClick={() => setColor(swatch)}
              style={{ backgroundColor: swatch }}
              aria-label={`Select color ${swatch}`}
              className="w-8 h-8 rounded border border-[var(--temper-border)]"
            />
          ))}
        </div>
        {config.show_preview && (
          <div style={{ backgroundColor: color }} className="w-32 h-32 rounded border border-[var(--temper-border)]" />
        )}
        <div className="flex flex-col gap-2 text-[var(--temper-text)]">
          {config.formats.includes('hex') && <div><span className="font-medium">HEX:</span> {color.toUpperCase()}</div>}
          {config.formats.includes('rgb') && <div><span className="font-medium">RGB:</span> rgb({rgb.r}, {rgb.g}, {rgb.b})</div>}
          {config.formats.includes('hsl') && <div><span className="font-medium">HSL:</span> hsl({hsl.h}, {hsl.s}%, {hsl.l}%)</div>}
        </div>
      </div>
    </div>
  );
}

import { useQuery } from '@tanstack/react-query';
import { useState, useEffect } from 'react';
import { fetchPaletteConfig, fetchPaletteGenerate, PaletteGenerateResult } from '../api';

export function PalettePage() {
  const { data: config, isLoading, isError } = useQuery({
    queryKey: ['palette-config'],
    queryFn: fetchPaletteConfig,
  });

  const [palette, setPalette] = useState<PaletteGenerateResult | null>(null);
  const [isGenerating, setIsGenerating] = useState(false);
  const [copiedIndex, setCopiedIndex] = useState<number | null>(null);

  const generatePalette = async () => {
    setIsGenerating(true);
    try {
      const result = await fetchPaletteGenerate();
      setPalette(result);
    } finally {
      setIsGenerating(false);
    }
  };

  useEffect(() => {
    generatePalette();
  }, []);

  const copyHex = (hex: string, index: number) => {
    navigator.clipboard.writeText(hex);
    setCopiedIndex(index);
    setTimeout(() => setCopiedIndex(null), 1500);
  };

  if (isLoading) return <div className="p-8 text-center text-[var(--temper-text-muted)]">Loading...</div>;
  if (isError || !config) return <div className="p-8 text-center text-red-400">Failed to load config.</div>;

  return (
    <div className="max-w-4xl mx-auto p-8">
      <h1 className="text-3xl font-bold mb-2 text-[var(--temper-text)]">{config.title}</h1>
      <p className="text-[var(--temper-text-muted)] mb-6">{config.description}</p>

      <button
        onClick={generatePalette}
        disabled={isGenerating}
        className="bg-[var(--temper-accent)] text-white px-6 py-2 rounded-lg font-medium hover:opacity-90 disabled:opacity-50 mb-6"
      >
        {isGenerating ? 'Generating...' : 'Generate Palette'}
      </button>

      {palette && (
        <>
          <p className="text-sm text-[var(--temper-text-muted)] mb-4">
            Harmony: <span className="font-medium text-[var(--temper-text)]">{palette.harmony}</span>
            {' · '}Seed hue: <span className="font-medium text-[var(--temper-text)]">{palette.seed_hue}°</span>
          </p>

          <div className="flex gap-4">
            {palette.colors.map((color, i) => (
              <div key={i} className="flex-1 min-w-0">
                <div
                  className="rounded-lg mb-2"
                  style={{ backgroundColor: color.hex, minHeight: 120 }}
                />
                <button
                  onClick={() => copyHex(color.hex, i)}
                  className="text-sm font-mono text-[var(--temper-text)] hover:text-[var(--temper-accent)] cursor-pointer bg-transparent border-none p-0"
                >
                  {copiedIndex === i ? 'Copied!' : color.hex}
                </button>
                <p className="text-xs text-[var(--temper-text-muted)] mt-1">{color.rgb}</p>
                <p className="text-xs text-[var(--temper-text-muted)]">{color.hsl}</p>
              </div>
            ))}
          </div>
        </>
      )}
    </div>
  );
}

import { Routes, Route } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import { HomePage } from './pages/HomePage';
import { RunPage } from './pages/RunPage';
import { TicTacToePage } from './pages/TicTacToePage';
import { MarkdownPreviewPage } from './pages/MarkdownPreviewPage';
import { ColorPickerPage } from './pages/ColorPickerPage';
import { fetchVersion } from './api';

export default function App() {
  const { data: versionInfo } = useQuery({
    queryKey: ['version'],
    queryFn: fetchVersion,
    staleTime: Infinity,
    retry: false,
  });

  return (
    <div className="flex flex-col h-screen">
      <main className="flex-1 min-h-0">
        <Routes>
          <Route path="/" element={<HomePage />} />
          <Route path="/runs/:runId" element={<RunPage />} />
          <Route path="/games/tictactoe" element={<TicTacToePage />} />
          <Route path="/tools/markdown" element={<MarkdownPreviewPage />} />
          <Route path="/tools/colors" element={<ColorPickerPage />} />
        </Routes>
      </main>
      <footer className="bg-[var(--temper-panel)] border-t border-[var(--temper-border)] text-[var(--temper-text-muted)] text-sm py-2 text-center">
        <p>
          Built with{' '}
          <a href="https://claude.ai" target="_blank" rel="noopener noreferrer" className="text-[var(--temper-accent)] hover:underline">Claude</a>
          {' · '}
          Powered by{' '}
          <a href="https://github.com/shine2lay/temper-ai" target="_blank" rel="noopener noreferrer" className="text-[var(--temper-accent)] hover:underline">Temper AI</a>
          {' · '}
          <a href="https://github.com/shine2lay/agentic-sdlc-demo" target="_blank" rel="noopener noreferrer" className="text-[var(--temper-accent)] hover:underline">Source</a>
          {' · '}<a href="/games/tictactoe" className="text-[var(--temper-accent)] hover:underline">Tic-Tac-Toe</a>
          {' · '}<a href="/tools/markdown" className="text-[var(--temper-accent)] hover:underline">Markdown</a>
          {' · '}<a href="/tools/colors" className="text-[var(--temper-accent)] hover:underline">Colors</a>
        </p>
        {versionInfo?.version && (
          <p className="text-xs mt-1 text-[var(--temper-text-muted)]">
            v{versionInfo.version}
          </p>
        )}
      </footer>
    </div>
  );
}

import { Routes, Route } from 'react-router-dom';
import { HomePage } from './pages/HomePage';
import { RunPage } from './pages/RunPage';

export default function App() {
  return (
    <div className="flex flex-col h-screen">
      <main className="flex-1 min-h-0">
        <Routes>
          <Route path="/" element={<HomePage />} />
          <Route path="/runs/:runId" element={<RunPage />} />
        </Routes>
      </main>
      <footer className="bg-[var(--temper-panel)] border-t border-[var(--temper-border)] text-[var(--temper-text-muted)] text-sm py-2 text-center">
        <p>
          The code for this website is hosted at{' '}
          <a
            href="https://github.com/shine2lay/agentic-sdlc-demo"
            target="_blank"
            rel="noopener noreferrer"
            className="text-[var(--temper-accent)] hover:underline"
          >
            GitHub
          </a>
        </p>
      </footer>
    </div>
  );
}

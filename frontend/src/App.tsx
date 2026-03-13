import { useEffect, useState } from 'react';
import { fetchHealth, fetchRuns, type Run } from './api';
import './App.css';

function App() {
  const [health, setHealth] = useState<string>('loading');
  const [runs, setRuns] = useState<Run[]>([]);

  useEffect(() => {
    fetchHealth()
      .then(() => setHealth('ok'))
      .catch(() => setHealth('error'));

    fetchRuns()
      .then((data) => setRuns(data.runs))
      .catch(() => {});

    const interval = setInterval(() => {
      fetchRuns()
        .then((data) => setRuns(data.runs))
        .catch(() => {});
    }, 5000);

    return () => clearInterval(interval);
  }, []);

  return (
    <div className="app">
      <div className="header">
        <h1>Agentic SDLC</h1>
        <div className="health-badge">
          <span className={`status-dot ${health}`} />
          {health === 'ok' ? 'API connected' : health === 'error' ? 'API unreachable' : 'Connecting...'}
        </div>
      </div>

      <div className="section-title">Runs</div>

      {runs.length === 0 ? (
        <div className="empty-state">
          No runs yet. Worker will pick up pending runs automatically.
        </div>
      ) : (
        <div className="runs-list">
          {runs.map((run) => (
            <div key={run.id} className="run-card">
              <div className="run-info">
                <span className="run-workflow">{run.workflow}</span>
                <span className="run-meta">
                  {run.id.slice(0, 8)} &middot; {new Date(run.created_at).toLocaleString()}
                </span>
              </div>
              <span className={`run-status ${run.status}`}>{run.status}</span>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

export default App;

import { useEffect, useState } from 'react';
import { fetchHealth, fetchRuns, submitSuggestion, type Run } from './api';
import './App.css';

function App() {
  const [health, setHealth] = useState<string>('loading');
  const [runs, setRuns] = useState<Run[]>([]);
  const [suggestion, setSuggestion] = useState('');
  const [submitState, setSubmitState] = useState<'idle' | 'submitting' | 'success' | 'error'>('idle');
  const [submitMessage, setSubmitMessage] = useState('');

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

  const handleSubmit = async () => {
    if (!suggestion.trim()) return;
    setSubmitState('submitting');
    setSubmitMessage('');
    try {
      const result = await submitSuggestion(suggestion);
      setSubmitState('success');
      setSubmitMessage(result.message);
      setSuggestion('');
      setTimeout(() => setSubmitState('idle'), 5000);
    } catch (err) {
      setSubmitState('error');
      setSubmitMessage(err instanceof Error ? err.message : 'Something went wrong');
      setTimeout(() => setSubmitState('idle'), 5000);
    }
  };

  return (
    <div className="app">
      <div className="header">
        <h1>Agentic SDLC</h1>
        <div className="health-badge">
          <span className={`status-dot ${health}`} />
          {health === 'ok' ? 'API connected' : health === 'error' ? 'API unreachable' : 'Connecting...'}
        </div>
      </div>

      <div className="suggest-section">
        <div className="section-title">Suggest a Feature</div>
        <div className="suggest-box">
          <textarea
            className="suggest-input"
            placeholder="Describe a feature or change you'd like to see..."
            value={suggestion}
            onChange={(e) => setSuggestion(e.target.value)}
            rows={3}
            disabled={submitState === 'submitting'}
          />
          <button
            className="suggest-button"
            onClick={handleSubmit}
            disabled={!suggestion.trim() || submitState === 'submitting'}
          >
            {submitState === 'submitting' ? 'Submitting...' : 'Submit'}
          </button>
        </div>
        {submitMessage && (
          <div className={`suggest-feedback ${submitState}`}>
            {submitMessage}
          </div>
        )}
      </div>

      <div className="section-title">Runs</div>

      {runs.length === 0 ? (
        <div className="empty-state">
          No runs yet. Submit a suggestion to kick off the pipeline.
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

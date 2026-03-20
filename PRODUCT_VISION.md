# Agentic SDLC Demo — Product Vision

## What This Is

A live demonstration of autonomous multi-agent software development. Users
submit feature suggestions through a web form, and an AI-powered pipeline
automatically validates, plans, implements, tests, and deploys the changes
— with zero human intervention.

The product itself is intentionally simple (a FastAPI API + React dashboard).
The value is in the pipeline that builds it, not the app itself.

## North Star

**Show that AI agents can autonomously ship working code to production,
safely and reliably.**

Every suggestion that passes validation should result in working code
deployed to a live Heroku app — or a clear explanation of why it couldn't
be done. The pipeline should never break the app, never ship inappropriate
content, and never require manual cleanup.

## What the App Does

- **Homepage**: Suggestion form + runs list showing pipeline history
- **Execution View**: DAG visualization of the pipeline stages, with
  agent details, LLM calls, tool calls, and timing
- **API**: Collection of simple utility endpoints (dice, coin-flip,
  countdown, reverse, palindrome, etc.) added by the pipeline itself
- **Pipeline Dashboard**: Real-time progress as stages complete

## What Suggestions Should Build Toward

Good suggestions make the app more useful, interesting, or polished
as a demo. They should be things you'd want to show someone to
demonstrate "look, AI agents built this."

### Encouraged

- New API endpoints that do something interesting or useful
  (math, text processing, data generation, utilities)
- Visual improvements to the homepage or execution view
  (better layout, colors, typography, status indicators)
- Informational additions (tooltips, descriptions, help text)
- Fun but professional features (random facts, word games, converters)

### Discouraged (but not auto-rejected)

- Purely cosmetic changes with no visible impact
- Endpoints that duplicate existing functionality
- Changes that only make sense with additional context the pipeline can't have

### Not Allowed

- Changes to infrastructure (database, deployment, dependencies, config)
- Removal or modification of existing endpoints or features
- External service integrations (APIs, databases, auth providers)
- Content that is inappropriate, offensive, political, or controversial
- Anything that exposes system internals (env vars, file system, secrets)
- Changes that require new packages not already installed

## Technical Boundaries

### Can Be Modified
- `server/routes.py` — add new endpoints here
- `frontend/src/pages/` — homepage and run page components
- `frontend/src/index.css` — global styles
- `frontend/src/execution/` — execution view components

### Must Not Be Modified
- `server/app.py` — FastAPI app setup
- `server/database.py` — database configuration
- `server/models.py` — data models
- `server/websocket.py` — WebSocket handler
- `requirements.txt` — Python dependencies
- `package.json` — Node dependencies
- `Procfile` — Heroku process config
- `README.md` — project documentation

### Must Not Be Broken
- `GET /api/health` must return `{"status": "ok"}` (Heroku health check)
- `GET /api/runs` must return the runs list (frontend polls this)
- `GET /api/runs/{id}` must return full run data (execution view)
- `POST /api/suggest` must accept suggestions (core product flow)
- The app must start with `uvicorn server.app:app`
- All existing endpoints must keep their current signatures and responses

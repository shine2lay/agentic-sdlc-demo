"""Agentic SDLC Demo — API server.

Single dyno serves both the API and the frontend static build.
In dev mode, the Vite dev server proxies /api and /ws to this server.
"""

from __future__ import annotations

import os
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from server.database import init_db
from server.routes import router
from server.websocket import ws_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield


app = FastAPI(title="Agentic SDLC Demo", version="0.1.0", lifespan=lifespan)

cors_origins = os.getenv("CORS_ORIGINS", "http://localhost:5173").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router, prefix="/api")
app.include_router(ws_router)

# Serve frontend static build if it exists (production).
# Mount AFTER API routes so /api and /ws take priority.
static_dir = Path(__file__).resolve().parent.parent / "frontend" / "dist"
if static_dir.is_dir():
    # Serve static assets (JS, CSS, images)
    app.mount("/assets", StaticFiles(directory=str(static_dir / "assets")), name="assets")

    # SPA catch-all: serve index.html for any non-API route
    @app.get("/{full_path:path}")
    async def spa_fallback(request: Request, full_path: str):
        # If the path maps to an actual file in dist, serve it
        file_path = static_dir / full_path
        if file_path.is_file():
            return FileResponse(str(file_path))
        # Otherwise serve index.html for client-side routing
        return FileResponse(str(static_dir / "index.html"))

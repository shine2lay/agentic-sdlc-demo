"""REST API routes."""

from __future__ import annotations

import json
import random
import uuid
from datetime import UTC, datetime
from typing import Any, List

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlmodel import Session, func, select

from server.database import get_session
from server.models import Run, RunEvent

router = APIRouter()

SDLC_WORKFLOW = "sdlc_deploy_test"


def calculate_duration(started_at: datetime | None, completed_at: datetime | None) -> float | None:
    """Calculate duration in seconds between started_at and completed_at."""
    if started_at and completed_at:
        return (completed_at - started_at).total_seconds()
    return None


def extract_total_tokens(result: dict | None) -> int | None:
    """Extract total_tokens from execution result if available."""
    if not result:
        return None
    execution = result.get("execution")
    if execution and isinstance(execution, dict):
        return execution.get("total_tokens")
    return None


def extract_workflow_output(result: dict | None) -> dict | None:
    """Extract workflow_output from execution result if available."""
    if not result:
        return None
    execution = result.get("execution")
    if execution and isinstance(execution, dict):
        return execution.get("workflow_output")
    return None


# ── Request/Response models ───────────────────────────────────────

class CreateRunRequest(BaseModel):
    workflow: str
    inputs: dict[str, Any] = {}


class CreateRunResponse(BaseModel):
    id: str
    status: str = "pending"


class SuggestRequest(BaseModel):
    suggestion: str


class ClaimRequest(BaseModel):
    worker_id: str


class CompleteRequest(BaseModel):
    status: str  # completed | failed
    result: dict[str, Any] | None = None
    error: str | None = None


class TypewriterLine(BaseModel):
    text: str
    css_class: str


class TypewriterConfigResponse(BaseModel):
    enabled: bool
    lines: List[TypewriterLine]
    speed_ms: int
    start_delay_ms: int


class BackToTopConfigResponse(BaseModel):
    enabled: bool
    scroll_threshold_px: int
    position_right_px: int
    position_bottom_px: int
    size_px: int
    bg_color: str
    hover_bg_color: str
    icon_color: str
    border_radius: str
    transition_ms: int
    scroll_behavior: str


class ParallaxConfigResponse(BaseModel):
    enabled: bool
    speed_factor: float
    max_offset_px: int
    direction: str
    easing: str


class SparkleConfigResponse(BaseModel):
    enabled: bool
    particle_count: int
    duration_ms: int
    spread_px: int
    colors: List[str]
    repeat_interval_ms: int
    size_px: int
    target: str


class GradientBorderConfigResponse(BaseModel):
    enabled: bool
    colors: List[str]
    angle_deg: int
    animation_duration_ms: int
    border_width_px: int
    border_radius: str
    target: str


class TicTacToeConfigResponse(BaseModel):
    board_size: int
    player_symbols: List[str]
    player_colors: List[str]
    winning_length: int
    empty_cell: str
    title: str


class SuggestionsCountResponse(BaseModel):
    total_suggestions: int
    poll_interval_ms: int


class MarkdownPreviewConfigResponse(BaseModel):
    title: str
    default_markdown: str
    editor_placeholder: str
    debounce_ms: int


class ColorPickerConfigResponse(BaseModel):
    title: str
    default_color: str
    formats: List[str]
    show_preview: bool
    preset_colors: List[str]


class BounceButtonConfigResponse(BaseModel):
    enabled: bool
    scale_start: float
    scale_peak: float
    duration_ms: int
    easing: str
    iteration_count: int
    delay_ms: int
    debounce_ms: int
    skip_initial_render: bool
    respect_reduced_motion: bool
    target: str


class ProgrammingJokeResponse(BaseModel):
    joke: str
    category: str


PROGRAMMING_JOKES = [
    {"joke": "Why do programmers prefer dark mode? Because light attracts bugs.", "category": "general"},
    {"joke": "There are only 10 types of people in the world: those who understand binary and those who don't.", "category": "general"},
    {"joke": "A SQL query walks into a bar, walks up to two tables, and asks: Can I join you?", "category": "databases"},
    {"joke": "Why do Java developers wear glasses? Because they can't C#.", "category": "languages"},
    {"joke": "How many programmers does it take to change a light bulb? None, that's a hardware problem.", "category": "general"},
    {"joke": "The best thing about a Boolean is that even if you're wrong, you're only off by a bit.", "category": "general"},
    {"joke": "A programmer's wife tells him: Go to the store and buy a gallon of milk. If they have eggs, get a dozen. He comes back with 12 gallons of milk.", "category": "general"},
    {"joke": "Why was the JavaScript developer sad? Because he didn't Node how to Express himself.", "category": "javascript"},
    {"joke": "What's a programmer's favorite hangout place? Foo Bar.", "category": "general"},
    {"joke": "To understand what recursion is, you must first understand recursion.", "category": "general"},
    {"joke": "There are two hard things in computer science: cache invalidation, naming things, and off-by-one errors.", "category": "general"},
    {"joke": "It works on my machine. Then we'll ship your machine.", "category": "devops"},
]


# ── Utility endpoints ──────────────────────────────────────────────

@router.get("/health")
def health():
    return {"status": "ok"}


@router.get("/version")
def version():
    return {"version": "0.4.0", "deployed_by": "agentic-sdlc"}


@router.get("/typewriter-config", response_model=TypewriterConfigResponse)
def get_typewriter_config():
    """Return configuration for the homepage typewriter animation."""
    return {
        "enabled": True,
        "lines": [
            {"text": "Describe a change.", "css_class": ""},
            {"text": "Watch AI build it.", "css_class": "accent"},
        ],
        "speed_ms": 80,
        "start_delay_ms": 300,
    }


@router.get("/back-to-top-config", response_model=BackToTopConfigResponse)
def get_back_to_top_config():
    """Return configuration for the back-to-top button UI component."""
    return {
        "enabled": True,
        "scroll_threshold_px": 400,
        "position_right_px": 32,
        "position_bottom_px": 32,
        "size_px": 44,
        "bg_color": "#6366f1",
        "hover_bg_color": "#4f46e5",
        "icon_color": "#ffffff",
        "border_radius": "50%",
        "transition_ms": 200,
        "scroll_behavior": "smooth",
    }


@router.get("/parallax-config", response_model=ParallaxConfigResponse)
def get_parallax_config():
    """Return configuration for the hero section parallax scroll effect."""
    return {
        "enabled": True,
        "speed_factor": 0.3,
        "max_offset_px": 120,
        "direction": "up",
        "easing": "ease-out",
    }


@router.get("/sparkle-config", response_model=SparkleConfigResponse)
def get_sparkle_config():
    """Return configuration for the sparkle animation on the shipped count."""
    return {
        "enabled": True,
        "particle_count": 6,
        "duration_ms": 1200,
        "spread_px": 18,
        "colors": ["#fbbf24", "#f59e0b", "#d97706", "#ffffff"],
        "repeat_interval_ms": 4000,
        "size_px": 6,
        "target": "shipped",
    }


@router.get("/gradient-border-config", response_model=GradientBorderConfigResponse)
def get_gradient_border_config():
    """Return configuration for the gradient border animation on the suggestion input box."""
    return {
        "enabled": True,
        "colors": ["#6366f1", "#8b5cf6", "#ec4899", "#6366f1"],
        "angle_deg": 135,
        "animation_duration_ms": 6000,
        "border_width_px": 2,
        "border_radius": "0.5rem",
        "target": "suggest-input",
    }


@router.get("/tictactoe-config", response_model=TicTacToeConfigResponse)
def get_tictactoe_config():
    """Return configuration for the tic-tac-toe game."""
    return {
        "board_size": 3,
        "player_symbols": ["X", "O"],
        "player_colors": ["#6366f1", "#ec4899"],
        "winning_length": 3,
        "empty_cell": "",
        "title": "Tic-Tac-Toe",
    }


@router.get("/suggestions-count", response_model=SuggestionsCountResponse)
def get_suggestions_count(session: Session = Depends(get_session)):
    """Return the total number of suggestions processed."""
    count = session.exec(
        select(func.count(Run.id)).where(Run.workflow == SDLC_WORKFLOW)
    ).one()
    return {"total_suggestions": count, "poll_interval_ms": 10000}


@router.get("/markdown-preview-config", response_model=MarkdownPreviewConfigResponse)
def get_markdown_preview_config():
    """Return configuration for the markdown preview tool."""
    return {
        "title": "Markdown Preview",
        "default_markdown": "# Hello\n\nStart typing markdown here...\n\n- Supports **bold** and *italic*\n- Lists and headings\n- Code blocks and more",
        "editor_placeholder": "Type your markdown here...",
        "debounce_ms": 200,
    }


@router.get("/color-picker-config", response_model=ColorPickerConfigResponse)
def get_color_picker_config():
    """Return configuration for the color picker tool."""
    return {
        "title": "Color Picker",
        "default_color": "#6366f1",
        "formats": ["hex", "rgb", "hsl"],
        "show_preview": True,
        "preset_colors": ["#ef4444", "#f97316", "#eab308", "#22c55e", "#3b82f6", "#8b5cf6", "#ec4899", "#ffffff", "#000000"],
    }


@router.get("/programming-joke", response_model=ProgrammingJokeResponse)
def get_programming_joke():
    """Return a random programming joke."""
    return random.choice(PROGRAMMING_JOKES)


@router.get("/bounce-button-config", response_model=BounceButtonConfigResponse)
def get_bounce_button_config():
    """Return configuration for the gentle bounce animation on the submit button when it becomes enabled."""
    return {
        "enabled": True,
        "scale_start": 1.0,
        "scale_peak": 1.07,
        "duration_ms": 600,
        "easing": "cubic-bezier(0.34, 1.56, 0.64, 1)",
        "iteration_count": 2,
        "delay_ms": 100,
        "debounce_ms": 300,
        "skip_initial_render": True,
        "respect_reduced_motion": True,
        "target": "submit-button",
    }


# ── Suggestion endpoint ───────────────────────────────────────────

@router.post("/suggest")
def suggest(body: SuggestRequest, session: Session = Depends(get_session)):
    """Submit a feature suggestion. Creates a pending run for the worker."""
    if not body.suggestion.strip():
        raise HTTPException(status_code=400, detail="Suggestion cannot be empty")
    run = Run(
        id=str(uuid.uuid4()),
        workflow=SDLC_WORKFLOW,
        inputs=json.dumps({"task_description": body.suggestion}),
    )
    session.add(run)
    session.commit()
    return {
        "status": "submitted",
        "run_id": run.id,
        "message": "Your suggestion has been submitted. A worker will pick it up shortly.",
    }


# ── Worker endpoints ──────────────────────────────────────────────

@router.post("/runs/{run_id}/claim")
def claim_run(run_id: str, body: ClaimRequest, session: Session = Depends(get_session)):
    """Worker claims a pending run."""
    run = session.get(Run, run_id)
    if not run:
        raise HTTPException(status_code=404, detail="Run not found")
    if run.status != "pending":
        raise HTTPException(status_code=409, detail=f"Run is already {run.status}")
    run.status = "claimed"
    run.worker_id = body.worker_id
    run.started_at = datetime.now(UTC)
    session.add(run)
    session.commit()
    return {"status": "claimed", "run_id": run.id}


@router.put("/runs/{run_id}/status")
def update_run_status(
    run_id: str, body: CompleteRequest, session: Session = Depends(get_session)
):
    """Worker updates run status (running, completed, failed)."""
    run = session.get(Run, run_id)
    if not run:
        raise HTTPException(status_code=404, detail="Run not found")
    run.status = body.status
    if body.result is not None:
        run.result = json.dumps(body.result)
    if body.error is not None:
        run.error = body.error
    if body.status in ("completed", "failed"):
        run.completed_at = datetime.now(UTC)
    session.add(run)
    session.commit()
    return {"status": run.status, "run_id": run.id}


# ── Run CRUD ──────────────────────────────────────────────────────

@router.post("/runs", response_model=CreateRunResponse)
def create_run(body: CreateRunRequest, session: Session = Depends(get_session)):
    run = Run(
        id=str(uuid.uuid4()),
        workflow=body.workflow,
        inputs=json.dumps(body.inputs),
    )
    session.add(run)
    session.commit()
    return CreateRunResponse(id=run.id, status=run.status)


@router.get("/runs")
def list_runs(
    status: str | None = Query(None),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    session: Session = Depends(get_session),
):
    query = select(Run).order_by(Run.created_at.desc()).offset(offset).limit(limit)
    if status:
        query = query.where(Run.status == status)
    runs = session.exec(query).all()
    return {
        "runs": [
            {
                "id": r.id,
                "workflow": r.workflow,
                "status": r.status,
                "inputs": r.get_inputs(),
                "created_at": r.created_at.isoformat(),
                "started_at": r.started_at.isoformat() if r.started_at else None,
                "completed_at": r.completed_at.isoformat() if r.completed_at else None,
                "error": r.error,
                "has_result": r.result is not None,
                "duration_seconds": calculate_duration(r.started_at, r.completed_at),
                "total_tokens": extract_total_tokens(r.get_result()),
                "workflow_output": extract_workflow_output(r.get_result()),
            }
            for r in runs
        ],
        "total": len(runs),
    }


@router.get("/runs/{run_id}")
def get_run(run_id: str, session: Session = Depends(get_session)):
    run = session.get(Run, run_id)
    if not run:
        raise HTTPException(status_code=404, detail="Run not found")
    return {
        "id": run.id,
        "workflow": run.workflow,
        "status": run.status,
        "inputs": run.get_inputs(),
        "result": run.get_result(),
        "error": run.error,
        "worker_id": run.worker_id,
        "created_at": run.created_at.isoformat(),
        "started_at": run.started_at.isoformat() if run.started_at else None,
        "completed_at": run.completed_at.isoformat() if run.completed_at else None,
    }


@router.get("/runs/{run_id}/events")
def get_run_events(
    run_id: str,
    limit: int = Query(200, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    session: Session = Depends(get_session),
):
    run = session.get(Run, run_id)
    if not run:
        raise HTTPException(status_code=404, detail="Run not found")
    query = (
        select(RunEvent)
        .where(RunEvent.run_id == run_id)
        .order_by(RunEvent.created_at)
        .offset(offset)
        .limit(limit)
    )
    events = session.exec(query).all()
    return {
        "events": [
            {
                "id": e.id,
                "event_type": e.event_type,
                "data": json.loads(e.data) if e.data else {},
                "created_at": e.created_at.isoformat(),
            }
            for e in events
        ],
        "total": len(events),
    }

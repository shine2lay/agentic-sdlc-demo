"""REST API routes."""

from __future__ import annotations

import json
import math
import random
import sys
import time
import uuid
from datetime import UTC, datetime
from typing import Any, List

import fastapi
import psutil
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlmodel import Session, select

from server.database import get_session
from server.models import Run, RunEvent

router = APIRouter()

START_TIME = time.time()


def is_prime(n: int) -> bool:
    """Check if a number is prime."""
    if n < 2:
        return False
    if n == 2:
        return True
    if n % 2 == 0:
        return False
    for i in range(3, int(math.sqrt(n)) + 1, 2):
        if n % i == 0:
            return False
    return True


def is_palindrome(text: str) -> tuple[bool, str]:
    """Check if a string is a palindrome.
    
    Normalizes the input by converting to lowercase and removing 
    non-alphanumeric characters, then compares with its reverse.
    Returns a tuple of (is_palindrome, cleaned_text).
    """
    cleaned = ''.join(c.lower() for c in text if c.isalnum())
    return cleaned == cleaned[::-1], cleaned


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


def classify_run_outcome(run: Run) -> str:
    """Classify a run into an outcome category matching frontend getOutcome() logic."""
    if run.status in ("running", "claimed"):
        return "running"
    if run.status == "pending":
        return "pending"
    if run.status == "failed":
        return "failed"
    if run.status == "completed":
        workflow_output = extract_workflow_output(run.get_result())
        if workflow_output is not None and workflow_output.get("result", "") in ("REJECT", "reject"):
            return "rejected"
        return "deployed"
    return "pending"


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


class PipelineStatsResponse(BaseModel):
    completed: int
    failed: int
    total: int


class PipelineStage(BaseModel):
    name: str
    description: str


class PipelineStagesResponse(BaseModel):
    stages: List[PipelineStage]


class TypewriterLine(BaseModel):
    text: str
    css_class: str


class TypewriterConfigResponse(BaseModel):
    lines: List[TypewriterLine]
    speed_ms: int
    start_delay_ms: int


class DotGridConfigResponse(BaseModel):
    dot_size_px: float
    dot_spacing_px: int
    dot_color: str
    dot_opacity: float


class RunCountsResponse(BaseModel):
    all: int
    deployed: int
    rejected: int
    failed: int
    running: int
    pending: int


class StatusBorderConfigResponse(BaseModel):
    border_width_px: int
    border_radius_px: int
    border_side: str
    colors: dict


class FadeInConfigResponse(BaseModel):
    duration_ms: int
    delay_ms: int
    easing: str
    translate_y_px: int
    stagger_ms: int
    initial_opacity: float


class CheckmarkConfigResponse(BaseModel):
    size_px: int
    stroke_color: str
    stroke_width_px: int
    animation_duration_ms: int
    display_duration_ms: int
    easing: str


class SkeletonConfigResponse(BaseModel):
    rows: int
    row_height_px: int
    shimmer_duration_ms: int
    border_radius_px: int
    gap_px: int
    base_color: str
    shimmer_color: str
    shimmer_angle_deg: int


# ── Utility endpoints ──────────────────────────────────────────────

@router.get("/health")
def health():
    return {"status": "ok"}


@router.get("/version")
def version():
    return {"version": "0.4.0", "deployed_by": "agentic-sdlc"}


@router.get("/server-info")
def server_info():
    return {
        "python_version": sys.version.split()[0],
        "fastapi_version": fastapi.__version__,
        "note": "Version info for demo purposes only",
    }


@router.get("/stats")
def stats(session: Session = Depends(get_session)):
    total_runs = session.exec(select(Run)).all()
    return {"total_runs": len(total_runs), "status": "healthy"}


@router.get("/pipeline-stats", response_model=PipelineStatsResponse)
def pipeline_stats(session: Session = Depends(get_session)):
    all_runs = session.exec(select(Run)).all()
    completed = sum(1 for run in all_runs if run.status == "completed")
    failed = sum(1 for run in all_runs if run.status == "failed")
    return {"completed": completed, "failed": failed, "total": completed + failed}


@router.get("/run-counts", response_model=RunCountsResponse)
def run_counts(session: Session = Depends(get_session)):
    """Return count badges for filter tabs: all, deployed, rejected, failed, running, pending."""
    runs = session.exec(select(Run)).all()
    counts = {"all": 0, "deployed": 0, "rejected": 0, "failed": 0, "running": 0, "pending": 0}
    for run in runs:
        outcome = classify_run_outcome(run)
        counts[outcome] += 1
        counts["all"] += 1
    return RunCountsResponse(**counts)


@router.get("/status")
def status():
    uptime = int(time.time() - START_TIME)
    return {"status": "operational", "uptime_seconds": uptime}


@router.get("/metrics")
def metrics():
    return {
        "cpu_percent": psutil.cpu_percent(),
        "memory_used_mb": psutil.virtual_memory().used / 1024 / 1024,
    }


@router.get("/countdown")
def countdown(from_: int = Query(default=10, ge=1)):
    """Returns a countdown array from the given number to 1."""
    return list(range(from_, 0, -1))


@router.get("/dice")
def roll_dice():
    """Roll a six-sided die and return the result."""
    return {"value": random.randint(1, 6)}


@router.get("/coin-flip")
def coin_flip():
    """Flip a coin and return heads or tails randomly."""
    return {"result": random.choice(["heads", "tails"])}


@router.get("/is-prime")
def check_prime(n: int = Query(..., ge=0, description="Number to check for primality")):
    """Check if a number is prime."""
    return {"n": n, "is_prime": is_prime(n)}


@router.get("/reverse")
def reverse_text(text: str = Query(..., description="Text to reverse")):
    """Reverse the provided text and return both original and reversed versions."""
    return {"original": text, "reversed": text[::-1]}


@router.get("/palindrome")
def check_palindrome(text: str = Query(..., description="Text to check for palindrome")):
    """Check if the provided text is a palindrome.
    
    Returns whether the text reads the same forwards and backwards,
    ignoring case and non-alphanumeric characters, along with the cleaned text.
    """
    is_pal, cleaned_text = is_palindrome(text)
    return {"text": text, "is_palindrome": is_pal, "cleaned_text": cleaned_text}


@router.get("/word-count")
def count_words(text: str = Query(..., description="Text to count words in")):
    """Count the number of words in the provided text.
    
    Words are separated by whitespace. Multiple consecutive spaces are treated as a single separator.
    """
    word_count = len(text.split())
    return {"text": text, "word_count": word_count}


@router.get("/pipeline-stages", response_model=PipelineStagesResponse)
def get_pipeline_stages():
    """Return the list of SDLC pipeline stages with their descriptions."""
    stages = [
        PipelineStage(name="clone", description="Clone the repository"),
        PipelineStage(name="branch", description="Create a new feature branch"),
        PipelineStage(name="code_change", description="Make the code changes"),
        PipelineStage(name="commit", description="Commit the changes"),
        PipelineStage(name="push", description="Push to remote and merge"),
    ]
    return {"stages": stages}


@router.get("/typewriter-config", response_model=TypewriterConfigResponse)
def get_typewriter_config():
    """Return configuration for the homepage typewriter animation."""
    return {
        "lines": [
            {"text": "Describe a change.", "css_class": ""},
            {"text": "Watch AI build it.", "css_class": "accent"},
        ],
        "speed_ms": 80,
        "start_delay_ms": 300,
    }


@router.get("/dot-grid-config", response_model=DotGridConfigResponse)
def get_dot_grid_config():
    """Return configuration for the page background dot grid pattern."""
    return {
        "dot_size_px": 1.5,
        "dot_spacing_px": 24,
        "dot_color": "#7dd3fc",
        "dot_opacity": 0.08,
    }


@router.get("/status-border-config", response_model=StatusBorderConfigResponse)
def get_status_border_config():
    """Return color mapping for run card left border by outcome status."""
    return {
        "border_width_px": 3,
        "border_radius_px": 2,
        "border_side": "left",
        "colors": {
            "deployed": "#22c55e",
            "rejected": "#f59e0b",
            "failed": "#ef4444",
            "running": "#3b82f6",
            "pending": "#6b7280",
        },
    }


@router.get("/fade-in-config", response_model=FadeInConfigResponse)
def get_fade_in_config():
    """Return configuration for run card fade-in animation on first appearance."""
    return {
        "duration_ms": 400,
        "delay_ms": 0,
        "easing": "ease-out",
        "translate_y_px": 12,
        "stagger_ms": 60,
        "initial_opacity": 0.0,
    }


@router.get("/checkmark-config", response_model=CheckmarkConfigResponse)
def get_checkmark_config():
    """Return configuration for the suggestion submit success checkmark animation."""
    return {
        "size_px": 48,
        "stroke_color": "#22c55e",
        "stroke_width_px": 3,
        "animation_duration_ms": 600,
        "display_duration_ms": 1500,
        "easing": "ease-out",
    }


@router.get("/skeleton-config", response_model=SkeletonConfigResponse)
def get_skeleton_config():
    """Return configuration for the shimmer loading skeleton shown while runs are being fetched."""
    return {
        "rows": 8,
        "row_height_px": 72,
        "shimmer_duration_ms": 1500,
        "border_radius_px": 8,
        "gap_px": 12,
        "base_color": "#1e293b",
        "shimmer_color": "#334155",
        "shimmer_angle_deg": 90,
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
                # Only include whether result exists, not the full data
                # (execution snapshots are 2-3MB each — use GET /runs/{id} for full data)
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

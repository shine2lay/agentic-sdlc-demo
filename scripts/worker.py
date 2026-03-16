"""DB-connected poller — reads pending runs from Heroku Postgres, executes via temper-ai.

Usage (standalone):
    DATABASE_URL=postgres://... python scripts/worker.py

Usage (Docker):
    Launched automatically by entrypoint.sh
"""

from __future__ import annotations

import json
import os
import platform
import time
from datetime import UTC, datetime

import httpx
from sqlmodel import Field, Session, SQLModel, create_engine, select


# ── Run model (mirrors server/models.py) ──────────────────────────


class Run(SQLModel, table=True):
    __tablename__ = "runs"

    id: str = Field(primary_key=True)
    workflow: str
    status: str = "pending"
    inputs: str = "{}"
    result: str | None = None
    error: str | None = None
    worker_id: str | None = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    started_at: datetime | None = None
    completed_at: datetime | None = None


# ── Config ────────────────────────────────────────────────────────


def _fix_db_url(url: str) -> str:
    """Heroku uses postgres:// but SQLAlchemy needs postgresql://."""
    if url.startswith("postgres://"):
        url = url.replace("postgres://", "postgresql://", 1)
    if "sslmode" not in url:
        sep = "&" if "?" in url else "?"
        url += f"{sep}sslmode=require"
    return url


DATABASE_URL = _fix_db_url(os.environ["DATABASE_URL"])
TEMPER_API_URL = os.getenv("TEMPER_API_URL", "http://localhost:8421")
TEMPER_API_TOKEN = os.getenv("TEMPER_API_TOKEN", "dev-token")
POLL_INTERVAL = int(os.getenv("POLL_INTERVAL", "10"))
WORKER_ID = os.getenv("WORKER_ID", platform.node())
SDLC_REPO_URL = os.getenv("SDLC_REPO_URL", "git@github.com:shine2lay/agentic-sdlc-demo.git")

engine = create_engine(DATABASE_URL)


# ── Helpers ───────────────────────────────────────────────────────


def log(msg: str) -> None:
    print(f"[{time.strftime('%H:%M:%S')}] {msg}", flush=True)


def get_pending_runs() -> list[dict]:
    with Session(engine) as session:
        runs = session.exec(select(Run).where(Run.status == "pending")).all()
        return [{"id": r.id, "workflow": r.workflow, "inputs": r.inputs} for r in runs]


def claim_run(run_id: str) -> bool:
    with Session(engine) as session:
        run = session.get(Run, run_id)
        if not run or run.status != "pending":
            return False
        run.status = "claimed"
        run.worker_id = WORKER_ID
        run.started_at = datetime.now(UTC)
        session.add(run)
        session.commit()
        return True


def update_run(
    run_id: str,
    status: str,
    result: dict | None = None,
    error: str | None = None,
) -> None:
    with Session(engine) as session:
        run = session.get(Run, run_id)
        if not run:
            return
        run.status = status
        if result is not None:
            run.result = json.dumps(result)
        if error is not None:
            run.error = error
        if status in ("completed", "failed"):
            run.completed_at = datetime.now(UTC)
        session.add(run)
        session.commit()


# ── Pipeline execution ────────────────────────────────────────────


def start_pipeline(client: httpx.Client, workflow: str, inputs: dict) -> str:
    resp = client.post(
        f"{TEMPER_API_URL}/api/runs",
        json={"workflow": workflow, "inputs": inputs},
        headers={"Authorization": f"Bearer {TEMPER_API_TOKEN}"},
    )
    resp.raise_for_status()
    return resp.json()["execution_id"]


def poll_pipeline(client: httpx.Client, execution_id: str) -> dict:
    while True:
        resp = client.get(
            f"{TEMPER_API_URL}/api/runs/{execution_id}",
            headers={"Authorization": f"Bearer {TEMPER_API_TOKEN}"},
        )
        resp.raise_for_status()
        data = resp.json()
        if data.get("status") in ("completed", "failed"):
            return data
        time.sleep(15)


def fetch_execution_snapshot(client: httpx.Client, execution_id: str) -> dict | None:
    """Fetch full execution details (stages, agents, calls) from temper-ai."""
    try:
        resp = client.get(f"{TEMPER_API_URL}/api/workflows/{execution_id}")
        if resp.status_code == 200:
            return resp.json()
    except Exception as e:
        log(f"  Warning: failed to fetch execution snapshot: {e}")
    return None


def get_recent_runs_summary(exclude_id: str, limit: int = 10) -> str:
    """Fetch recent runs and format as context for the duplicate check agent."""
    with Session(engine) as session:
        runs = session.exec(
            select(Run)
            .where(Run.id != exclude_id)
            .where(Run.status.in_(["completed", "running", "claimed"]))  # type: ignore[union-attr]
            .order_by(Run.created_at.desc())  # type: ignore[union-attr]
            .limit(limit)
        ).all()

    if not runs:
        return "No recent runs."

    lines = []
    for r in runs:
        inputs_data = json.loads(r.inputs) if r.inputs else {}
        task = inputs_data.get("task_description", "(no description)")
        lines.append(
            f"- [{r.id[:8]}] status={r.status} | {r.created_at:%Y-%m-%d %H:%M} | {task[:120]}"
        )
    return "\n".join(lines)


def process_run(run_id: str, workflow: str, inputs: dict) -> None:
    task = inputs.get("task_description", "")
    if not task:
        log(f"  Run {run_id[:8]} has no task_description")
        update_run(run_id, "failed", error="No task_description in inputs")
        return

    # Inject repo_url if not provided
    if "repo_url" not in inputs:
        inputs["repo_url"] = SDLC_REPO_URL

    # Inject recent runs for duplicate detection
    if "recent_runs" not in inputs:
        inputs["recent_runs"] = get_recent_runs_summary(run_id)

    update_run(run_id, "running")
    log(f"  Task: {task[:80]}...")

    try:
        with httpx.Client(timeout=60.0) as client:
            execution_id = start_pipeline(client, workflow, inputs)
            log(f"  Pipeline started: {execution_id}")

            result = poll_pipeline(client, execution_id)
            status = result.get("status", "unknown")
            log(f"  Pipeline finished: {status}")

            # Fetch full execution snapshot for the frontend
            snapshot = fetch_execution_snapshot(client, execution_id)

            run_result: dict = {
                "execution_id": execution_id,
                "pipeline_result": result.get("result"),
            }
            if snapshot:
                run_result["execution"] = snapshot

            if status == "completed":
                update_run(run_id, "completed", result=run_result)
            else:
                update_run(run_id, "failed",
                    result=run_result,
                    error=result.get("error_message", "Pipeline failed"),
                )
    except Exception as e:
        log(f"  Error: {e}")
        update_run(run_id, "failed", error=str(e))


# ── Main loop ─────────────────────────────────────────────────────


def main() -> None:
    log(f"Worker '{WORKER_ID}' starting")
    log(f"  Temper: {TEMPER_API_URL}")
    log(f"  Poll interval: {POLL_INTERVAL}s")

    while True:
        try:
            pending = get_pending_runs()
            if pending:
                log(f"Found {len(pending)} pending run(s)")
                for run_data in pending:
                    run_id = run_data["id"]
                    if claim_run(run_id):
                        log(f"Claimed run {run_id[:8]}")
                        inputs = json.loads(run_data["inputs"]) if run_data["inputs"] else {}
                        process_run(run_id, run_data["workflow"], inputs)
                    else:
                        log(f"Run {run_id[:8]} already claimed")
        except KeyboardInterrupt:
            log("Shutting down")
            break
        except Exception as e:
            log(f"Poll error: {e}")

        time.sleep(POLL_INTERVAL)


if __name__ == "__main__":
    main()

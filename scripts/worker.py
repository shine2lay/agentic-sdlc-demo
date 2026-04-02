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
SDLC_APP_URL = os.getenv("SDLC_APP_URL", "https://agentic-sdlc-demo-bdff250d08f2.herokuapp.com")
HEROKU_API_KEY = os.getenv("HEROKU_API_KEY", "")
HEROKU_APP_NAME = os.getenv("HEROKU_APP_NAME", "agentic-sdlc-demo")
HEROKU_GIT_URL = os.getenv("HEROKU_GIT_URL", "https://git.heroku.com/agentic-sdlc-demo.git")

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
    )
    resp.raise_for_status()
    return resp.json()["execution_id"]


def poll_pipeline(
    client: httpx.Client,
    execution_id: str,
    heroku_run_id: str | None = None,
) -> dict:
    """Poll temper-ai until the pipeline finishes.

    When *heroku_run_id* is provided, partial execution snapshots are
    written back to the Heroku DB every poll cycle so the frontend can
    show live progress (stages completing one by one).
    """
    while True:
        # v0.1: use /api/workflows/{id} for both status and snapshot
        snapshot = fetch_execution_snapshot(client, execution_id)
        if not snapshot:
            time.sleep(15)
            continue

        status = snapshot.get("status", "running")

        # Write partial execution snapshot to Heroku DB
        if heroku_run_id:
            partial_result = {
                "execution_id": execution_id,
                "execution": snapshot,
            }
            update_run(heroku_run_id, "running", result=partial_result)

        if status in ("completed", "failed"):
            return {"status": status, "execution": snapshot}
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
    """Fetch recent runs and format as context for the duplicate check agent.

    Includes deployed status so the agent knows whether the change actually
    landed. Runs where push failed or was skipped are marked as not-deployed
    so they don't block retries.
    """
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
        # Check if the code was actually deployed
        deployed = "unknown"
        if r.result:
            result_data = json.loads(r.result) if isinstance(r.result, str) else r.result
            push_status = _extract_push_status(result_data)
            if push_status == "success":
                deployed = "deployed"
            elif push_status in ("failed", "skipped"):
                deployed = "not-deployed"
        elif r.status == "running":
            deployed = "in-progress"
        lines.append(
            f"- [{r.id[:8]}] status={r.status} deployed={deployed} | {r.created_at:%Y-%m-%d %H:%M} | {task[:120]}"
        )
    return "\n".join(lines)


def _get_node_structured(node: dict) -> dict:
    """Extract structured output from a v0.1 node.

    In v0.1, structured output lives on the agent, not the node.
    For agent nodes: node.agent.structured_output
    For stage nodes: check each agent in node.agents
    Falls back to JSON-parsing the agent's text output.
    """
    # Agent node (single agent)
    agent = node.get("agent")
    if agent:
        structured = agent.get("structured_output")
        if structured and isinstance(structured, dict):
            return structured
        # Fallback: try parsing agent output as JSON
        output = agent.get("output", "")
        if output:
            try:
                parsed = json.loads(output)
                if isinstance(parsed, dict):
                    return parsed
            except (json.JSONDecodeError, TypeError):
                pass

    # Stage node (multiple agents) — check each
    for a in node.get("agents") or []:
        structured = a.get("structured_output")
        if structured and isinstance(structured, dict):
            return structured

    return {}


def _get_nodes(result_data: dict) -> list[dict]:
    """Get nodes from execution data. Supports both v0.1 (nodes) and old (stages)."""
    exec_data = result_data.get("execution", {})
    return exec_data.get("nodes", exec_data.get("stages", []))


def _get_node_name(node: dict) -> str:
    """Get node name. Supports both v0.1 (name) and old (stage_name)."""
    return node.get("name", node.get("stage_name", ""))


def _extract_push_status(result_data: dict) -> str:
    """Extract push_status from the LAST git_push node."""
    if not result_data.get("execution"):
        return "unknown"
    result = "unknown"
    for node in _get_nodes(result_data):
        if _get_node_name(node) == "sdlc_git_push":
            structured = _get_node_structured(node)
            if structured.get("push_status"):
                result = structured["push_status"]
    return result


def _extract_stage_field(result_data: dict, stage_name: str, field: str) -> str:
    """Extract a structured output field from the LAST occurrence of a node."""
    result = ""
    for node in _get_nodes(result_data):
        if _get_node_name(node) == stage_name:
            structured = _get_node_structured(node)
            val = structured.get(field, "")
            if val:
                result = val
    return result


def _extract_rejection_reason(result_data: dict) -> str | None:
    """Check if the pipeline completed but the suggestion was rejected."""
    if not result_data.get("execution"):
        return None

    for node in _get_nodes(result_data):
        name = _get_node_name(node)
        structured = _get_node_structured(node)

        if name == "sdlc_validate":
            verdict = structured.get("validation_result", "")
            if verdict == "REJECT":
                reason = structured.get("reason", "Suggestion did not pass validation")
                return f"Rejected: {reason}"

        if name == "sdlc_duplicate_check":
            verdict = structured.get("duplicate_check", "")
            if verdict == "FAIL":
                reason = structured.get("reason", "Duplicate of a previous run")
                return f"Duplicate: {reason}"

    return None


def process_run(run_id: str, workflow: str, inputs: dict) -> None:
    task = inputs.get("task_description", "")
    if not task:
        log(f"  Run {run_id[:8]} has no task_description")
        update_run(run_id, "failed", error="No task_description in inputs")
        return

    # Inject repo_url and app_url if not provided
    if "repo_url" not in inputs:
        inputs["repo_url"] = SDLC_REPO_URL
    if "app_url" not in inputs:
        inputs["app_url"] = SDLC_APP_URL
    if "heroku_api_key" not in inputs:
        inputs["heroku_api_key"] = HEROKU_API_KEY
    if "heroku_app_name" not in inputs:
        inputs["heroku_app_name"] = HEROKU_APP_NAME
    if "heroku_git_url" not in inputs:
        inputs["heroku_git_url"] = HEROKU_GIT_URL

    # Inject recent runs for duplicate detection
    if "recent_runs" not in inputs:
        inputs["recent_runs"] = get_recent_runs_summary(run_id)

    update_run(run_id, "running")
    log(f"  Task: {task[:80]}...")

    try:
        with httpx.Client(timeout=60.0) as client:
            execution_id = start_pipeline(client, workflow, inputs)
            log(f"  Pipeline started: {execution_id}")

            result = poll_pipeline(client, execution_id, heroku_run_id=run_id)
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

            # 1. Check if the suggestion was rejected (validate/duplicate gate)
            rejection = _extract_rejection_reason(run_result) if snapshot else None
            if rejection:
                log(f"  {rejection}")
                update_run(run_id, "failed", result=run_result, error=rejection)
            # 2. Check if the code was pushed and deploy verified
            elif status == "completed":
                push_status = _extract_push_status(run_result) if snapshot else "unknown"
                verify_result = _extract_stage_field(run_result, "sdlc_verify_deploy", "verify_result")

                if push_status == "success" and verify_result == "FAIL":
                    details = _extract_stage_field(run_result, "sdlc_verify_deploy", "verify_details")
                    log(f"  Deploy verification failed: {details}")
                    update_run(run_id, "failed",
                        result=run_result,
                        error=f"Deploy verification failed: {details}",
                    )
                elif push_status == "success":
                    update_run(run_id, "completed", result=run_result)
                elif push_status in ("failed", "skipped"):
                    log(f"  Pipeline completed but push {push_status}")
                    update_run(run_id, "failed",
                        result=run_result,
                        error=f"Pipeline completed but git push {push_status}",
                    )
                else:
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

#!/usr/bin/env python3
"""Local SDLC worker — polls Heroku for pending suggestions, runs them via temper-ai.

Usage:
    python scripts/worker.py

Environment:
    HEROKU_API_URL   — Heroku app URL (default: https://agentic-sdlc-demo-bdff250d08f2.herokuapp.com)
    TEMPER_API_URL   — Local temper-ai URL (default: http://localhost:8420)
    TEMPER_API_TOKEN — Temper API token (default: dev-token)
    POLL_INTERVAL    — Seconds between polls (default: 10)
    WORKER_ID        — Unique worker identifier (default: hostname)
"""

from __future__ import annotations

import os
import platform
import time

import httpx

HEROKU_API_URL = os.getenv(
    "HEROKU_API_URL",
    "https://agentic-sdlc-demo-bdff250d08f2.herokuapp.com",
)
TEMPER_API_URL = os.getenv("TEMPER_API_URL", "http://localhost:8420")
TEMPER_API_TOKEN = os.getenv("TEMPER_API_TOKEN", "dev-token")
POLL_INTERVAL = int(os.getenv("POLL_INTERVAL", "10"))
WORKER_ID = os.getenv("WORKER_ID", platform.node())
SDLC_REPO_URL = "git@github.com:shine2lay/agentic-sdlc-demo.git"


def log(msg: str) -> None:
    ts = time.strftime("%H:%M:%S")
    print(f"[{ts}] {msg}")


def poll_pending_runs(client: httpx.Client) -> list[dict]:
    """Fetch pending runs from Heroku."""
    resp = client.get(f"{HEROKU_API_URL}/api/runs", params={"status": "pending"})
    resp.raise_for_status()
    return resp.json().get("runs", [])


def claim_run(client: httpx.Client, run_id: str) -> bool:
    """Claim a pending run. Returns True if claimed successfully."""
    resp = client.post(
        f"{HEROKU_API_URL}/api/runs/{run_id}/claim",
        json={"worker_id": WORKER_ID},
    )
    if resp.status_code == 409:
        return False  # already claimed
    resp.raise_for_status()
    return True


def update_run_status(
    client: httpx.Client,
    run_id: str,
    status: str,
    result: dict | None = None,
    error: str | None = None,
) -> None:
    """Update run status on Heroku."""
    body: dict = {"status": status}
    if result is not None:
        body["result"] = result
    if error is not None:
        body["error"] = error
    resp = client.put(f"{HEROKU_API_URL}/api/runs/{run_id}/status", json=body)
    resp.raise_for_status()


def start_pipeline(client: httpx.Client, task_description: str) -> str:
    """Start the SDLC pipeline on local temper-ai. Returns execution_id."""
    resp = client.post(
        f"{TEMPER_API_URL}/api/runs",
        json={
            "workflow": "sdlc_deploy_test",
            "inputs": {
                "repo_url": SDLC_REPO_URL,
                "task_description": task_description,
            },
        },
        headers={"Authorization": f"Bearer {TEMPER_API_TOKEN}"},
    )
    resp.raise_for_status()
    return resp.json()["execution_id"]


def poll_pipeline(client: httpx.Client, execution_id: str) -> dict:
    """Poll temper-ai until the pipeline completes. Returns the final state."""
    while True:
        resp = client.get(
            f"{TEMPER_API_URL}/api/runs/{execution_id}",
            headers={"Authorization": f"Bearer {TEMPER_API_TOKEN}"},
        )
        resp.raise_for_status()
        data = resp.json()
        status = data.get("status", "unknown")
        if status in ("completed", "failed"):
            return data
        time.sleep(15)


def process_run(client: httpx.Client, run: dict) -> None:
    """Process a single run: start pipeline, wait, report results."""
    run_id = run["id"]
    inputs = run.get("inputs", {})
    task = inputs.get("task_description", "")

    if not task:
        log(f"  Run {run_id[:8]} has no task_description, marking failed")
        update_run_status(client, run_id, "failed", error="No task_description in inputs")
        return

    # Mark as running
    update_run_status(client, run_id, "running")
    log(f"  Task: {task[:80]}...")

    try:
        # Start pipeline on local temper-ai
        execution_id = start_pipeline(client, task)
        log(f"  Pipeline started: {execution_id}")

        # Wait for completion
        result = poll_pipeline(client, execution_id)
        pipeline_status = result.get("status", "unknown")
        log(f"  Pipeline finished: {pipeline_status}")

        if pipeline_status == "completed":
            update_run_status(
                client,
                run_id,
                "completed",
                result={
                    "execution_id": execution_id,
                    "pipeline_status": pipeline_status,
                    "pipeline_result": result.get("result"),
                },
            )
        else:
            update_run_status(
                client,
                run_id,
                "failed",
                result={"execution_id": execution_id},
                error=result.get("error_message", "Pipeline failed"),
            )
    except Exception as e:
        log(f"  Error: {e}")
        update_run_status(client, run_id, "failed", error=str(e))


def main() -> None:
    log(f"Worker '{WORKER_ID}' starting")
    log(f"  Heroku: {HEROKU_API_URL}")
    log(f"  Temper: {TEMPER_API_URL}")
    log(f"  Poll interval: {POLL_INTERVAL}s")

    client = httpx.Client(timeout=60.0)

    while True:
        try:
            pending = poll_pending_runs(client)
            if pending:
                log(f"Found {len(pending)} pending run(s)")
                for run in pending:
                    run_id = run["id"]
                    if claim_run(client, run_id):
                        log(f"Claimed run {run_id[:8]}")
                        process_run(client, run)
                    else:
                        log(f"Run {run_id[:8]} already claimed, skipping")
        except httpx.HTTPError as e:
            log(f"Poll error: {e}")
        except KeyboardInterrupt:
            log("Shutting down")
            break

        time.sleep(POLL_INTERVAL)


if __name__ == "__main__":
    main()

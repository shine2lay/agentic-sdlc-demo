#!/usr/bin/env python3
"""Reset the Agentic SDLC demo to a clean state.

What it does:
  1. Wipes all runs and events from the SDLC database (Heroku Postgres)
  2. Wipes all events and checkpoints from the temper worker database (local Postgres)
  3. Resets the codebase to the stable-baseline tag (GitHub + Heroku)

Usage:
  python scripts/reset_demo.py              # interactive — asks for confirmation
  python scripts/reset_demo.py --yes        # skip confirmation
  python scripts/reset_demo.py --db-only    # wipe databases only, no code reset

Prerequisites:
  - DATABASE_URL env var (Heroku Postgres) or heroku CLI authenticated
  - Worker Postgres running on localhost:5434
"""

from __future__ import annotations

import os
import subprocess
import sys

from sqlalchemy import text
from sqlmodel import Session, create_engine


HEROKU_APP = os.getenv("HEROKU_APP_NAME", "agentic-sdlc-demo")
WORKER_DB_URL = os.getenv(
    "TEMPER_DATABASE_URL", "postgresql://temper:temper@localhost:5434/temper"
)


def get_sdlc_db_url() -> str:
    """Get the SDLC database URL from env or Heroku CLI."""
    url = os.getenv("DATABASE_URL", "")
    if not url:
        print("DATABASE_URL not set, fetching from Heroku...")
        try:
            result = subprocess.run(
                ["heroku", "config:get", "DATABASE_URL", "--app", HEROKU_APP],
                capture_output=True, text=True, check=True,
            )
            url = result.stdout.strip()
        except (subprocess.CalledProcessError, FileNotFoundError):
            print("ERROR: Could not get DATABASE_URL. Set it or authenticate heroku CLI.")
            sys.exit(1)
    return url.replace("postgres://", "postgresql://", 1)


def count_rows(engine, table: str) -> int:
    try:
        with Session(engine) as s:
            return s.exec(text(f"SELECT count(*) FROM {table}")).scalar() or 0
    except Exception:
        return -1


def wipe_tables(engine, tables: list[str], label: str) -> None:
    with Session(engine) as s:
        for table in tables:
            s.exec(text(f"DELETE FROM {table}"))
        s.commit()
    print(f"  {label}: wiped {', '.join(tables)}")


def reset_codebase() -> None:
    """Reset GitHub and Heroku to stable-baseline tag."""
    # Check tag exists
    result = subprocess.run(
        ["git", "rev-parse", "stable-baseline"], capture_output=True, text=True
    )
    if result.returncode != 0:
        print("  No stable-baseline tag found. Skipping code reset.")
        print("  Create one: git tag -a stable-baseline -m 'Clean state'")
        return

    tag_sha = result.stdout.strip()
    head_sha = subprocess.run(
        ["git", "rev-parse", "HEAD"], capture_output=True, text=True
    ).stdout.strip()

    if tag_sha == head_sha:
        print("  Already at stable-baseline, no reset needed.")
        return

    print(f"  Resetting to stable-baseline ({tag_sha[:8]})...")

    # Reset local
    subprocess.run(["git", "reset", "--hard", "stable-baseline"], check=True)
    print("  Local repo reset.")

    # Force push to GitHub
    try:
        subprocess.run(
            ["git", "push", "origin", "main", "--force"],
            check=True, capture_output=True, text=True,
        )
        print("  GitHub reset.")
    except subprocess.CalledProcessError as e:
        print(f"  GitHub push failed: {e.stderr[:200]}")

    # Force push to Heroku
    try:
        subprocess.run(
            ["git", "push", "heroku", "main", "--force"],
            check=True, capture_output=True, text=True,
        )
        print("  Heroku reset.")
    except subprocess.CalledProcessError as e:
        print(f"  Heroku push failed: {e.stderr[:200]}")


def main() -> None:
    skip_confirm = "--yes" in sys.argv
    db_only = "--db-only" in sys.argv

    if "--help" in sys.argv or "-h" in sys.argv:
        print(__doc__)
        sys.exit(0)

    sdlc_url = get_sdlc_db_url()
    sdlc_engine = create_engine(sdlc_url, echo=False)
    worker_engine = create_engine(WORKER_DB_URL, echo=False)

    print()
    print("+" + "=" * 44 + "+")
    print("|       AGENTIC SDLC DEMO RESET            |")
    print("+" + "=" * 44 + "+")
    print()
    print("This will:")
    print("  1. Delete all runs and events from SDLC DB (Heroku Postgres)")
    print("  2. Delete all events and checkpoints from worker DB (local Postgres)")
    if not db_only:
        print("  3. Reset codebase to stable-baseline (GitHub + Heroku)")
    print()

    # Show current state
    sdlc_runs = count_rows(sdlc_engine, "runs")
    sdlc_events = count_rows(sdlc_engine, "run_events")
    worker_events = count_rows(worker_engine, "events")
    worker_checkpoints = count_rows(worker_engine, "checkpoints")
    print("Current state:")
    print(f"  SDLC DB:   {sdlc_runs} runs, {sdlc_events} events")
    print(f"  Worker DB: {worker_events} events, {worker_checkpoints} checkpoints")
    if not db_only:
        head = subprocess.run(
            ["git", "log", "--oneline", "-1"], capture_output=True, text=True
        ).stdout.strip()
        tag = subprocess.run(
            ["git", "log", "--oneline", "-1", "stable-baseline"],
            capture_output=True, text=True
        ).stdout.strip()
        print(f"  HEAD:      {head}")
        print(f"  Baseline:  {tag}")
    print()

    if not skip_confirm:
        response = input("Proceed? [y/N] ").strip().lower()
        if response != "y":
            print("Aborted.")
            sys.exit(0)

    # Step 1: Wipe SDLC database
    print()
    print("-> Wiping SDLC database...")
    wipe_tables(sdlc_engine, ["run_events", "runs"], "SDLC DB")

    # Step 2: Wipe worker database
    print("-> Wiping worker database...")
    wipe_tables(worker_engine, ["checkpoints", "events"], "Worker DB")

    # Step 3: Reset codebase
    if not db_only:
        print("-> Resetting codebase...")
        reset_codebase()

    # Verify
    print()
    print("-> Verifying...")
    print(f"  SDLC DB:   {count_rows(sdlc_engine, 'runs')} runs")
    print(f"  Worker DB: {count_rows(worker_engine, 'events')} events")

    try:
        import httpx
        r = httpx.get(
            f"https://{HEROKU_APP}-bdff250d08f2.herokuapp.com/api/health",
            timeout=10,
        )
        print(f"  App health: HTTP {r.status_code}")
    except Exception:
        print("  App health: could not reach")

    print()
    print("Reset complete.")


if __name__ == "__main__":
    main()

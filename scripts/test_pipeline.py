"""Minimal end-to-end pipeline test.

Proves the loop: clone → branch → change → commit → push → Heroku deploys.

Usage:
    python3 scripts/test_pipeline.py

Requires: git SSH access to github.com/shine2lay/agentic-sdlc-demo
"""

import os
import subprocess
import sys
import tempfile
from datetime import datetime, timezone


REPO_URL = "git@github.com:shine2lay/agentic-sdlc-demo.git"
BRANCH = "main"


def run(cmd: list[str], cwd: str | None = None) -> str:
    """Run a command and return stdout."""
    print(f"  $ {' '.join(cmd)}")
    result = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"  STDERR: {result.stderr.strip()}")
        raise RuntimeError(f"Command failed: {' '.join(cmd)}")
    return result.stdout.strip()


def main():
    workdir = tempfile.mkdtemp(prefix="sdlc-test-")
    repo_dir = os.path.join(workdir, "repo")

    print(f"\n=== Stage 1: Clone ===")
    run(["git", "clone", REPO_URL, "repo"], cwd=workdir)
    print(f"  Cloned to {repo_dir}")

    print(f"\n=== Stage 2: Branch ===")
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
    branch_name = f"auto/{timestamp}"
    run(["git", "checkout", "-b", branch_name], cwd=repo_dir)
    print(f"  Created branch: {branch_name}")

    print(f"\n=== Stage 3: Code Change ===")
    # Smallest possible change: update a build timestamp file
    build_info = {
        "last_auto_build": timestamp,
        "source": "agentic-sdlc-pipeline",
    }
    build_file = os.path.join(repo_dir, "BUILD_INFO")
    with open(build_file, "w") as f:
        for k, v in build_info.items():
            f.write(f"{k}={v}\n")
    print(f"  Wrote BUILD_INFO")

    print(f"\n=== Stage 4: Commit ===")
    run(["git", "add", "BUILD_INFO"], cwd=repo_dir)
    run(["git", "commit", "-m", f"auto: update build info ({timestamp})"], cwd=repo_dir)
    print(f"  Committed")

    print(f"\n=== Stage 5: Push ===")
    # Push branch then merge to main
    run(["git", "checkout", BRANCH], cwd=repo_dir)
    run(["git", "merge", branch_name], cwd=repo_dir)
    run(["git", "push", "origin", BRANCH], cwd=repo_dir)
    print(f"  Pushed to {BRANCH}")

    print(f"\n=== Done ===")
    print(f"  Heroku should auto-deploy from GitHub shortly.")
    print(f"  Check: https://dashboard.heroku.com/apps/agentic-sdlc-demo/activity")
    print(f"  Cleanup: rm -rf {workdir}")


if __name__ == "__main__":
    main()

"""Acceptance tests for progress-bar-config endpoint and inline stage_progress on /runs."""

import json
import sys
import uuid

from fastapi.testclient import TestClient

from server.app import app

client = TestClient(app)


# ── 1. GET /api/progress-bar-config ──────────────────────────────

def test_progress_bar_config_returns_200():
    """Endpoint exists and returns 200 with exact expected shape."""
    response = client.get("/api/progress-bar-config")
    assert response.status_code == 200, f"Expected 200, got {response.status_code}"
    data = response.json()
    assert data == {
        "bar_height_px": 4,
        "bar_color": "#22c55e",
        "bar_bg_color": "#e5e7eb",
        "bar_border_radius": "2px",
        "animate": True,
    }, f"Unexpected response body: {data}"
    print("PASS: progress-bar-config returns correct shape")


# ── 2. GET /api/runs includes stage_progress ─────────────────────

def test_runs_list_includes_stage_progress_null_for_pending():
    """A freshly created (pending) run has stage_progress: null."""
    # Create a pending run via the suggest endpoint
    resp = client.post("/api/suggest", json={"suggestion": "test progress feature"})
    assert resp.status_code == 200, f"suggest failed: {resp.status_code}"
    run_id = resp.json()["run_id"]

    # Fetch runs list and find our run
    resp = client.get("/api/runs")
    assert resp.status_code == 200
    data = resp.json()
    runs = data["runs"]
    our_run = next((r for r in runs if r["id"] == run_id), None)
    assert our_run is not None, f"Run {run_id} not found in list"

    # stage_progress must be present as a key and be None/null
    assert "stage_progress" in our_run, (
        f"stage_progress field missing from run dict. Keys: {list(our_run.keys())}"
    )
    assert our_run["stage_progress"] is None, (
        f"Expected null for pending run, got {our_run['stage_progress']}"
    )
    print("PASS: pending run has stage_progress: null")


def test_runs_list_includes_stage_progress_for_completed():
    """A completed run with execution.nodes data returns stage_progress counts."""
    # Create a run directly, then complete it with execution data
    resp = client.post(
        "/api/runs",
        json={"workflow": "sdlc_deploy_test", "inputs": {"task_description": "test"}},
    )
    assert resp.status_code == 200
    run_id = resp.json()["id"]

    # Claim the run
    worker_id = f"test-worker-{uuid.uuid4()}"
    resp = client.post(f"/api/runs/{run_id}/claim", json={"worker_id": worker_id})
    assert resp.status_code == 200

    # Complete with execution nodes — 2 completed, 1 failed, 3 total
    result_payload = {
        "execution": {
            "nodes": [
                {"name": "clone", "status": "completed"},
                {"name": "build", "status": "completed"},
                {"name": "deploy", "status": "failed"},
            ],
            "total_tokens": 500,
        }
    }
    resp = client.put(
        f"/api/runs/{run_id}/status",
        json={"status": "completed", "result": result_payload},
    )
    assert resp.status_code == 200

    # Fetch runs list and inspect stage_progress
    resp = client.get("/api/runs")
    assert resp.status_code == 200
    our_run = next((r for r in resp.json()["runs"] if r["id"] == run_id), None)
    assert our_run is not None

    sp = our_run.get("stage_progress")
    assert sp is not None, "stage_progress should not be null for completed run with nodes"
    assert sp["completed_stages"] == 2, f"Expected 2 completed, got {sp['completed_stages']}"
    assert sp["total_stages"] == 3, f"Expected 3 total, got {sp['total_stages']}"
    assert sp["failed_stages"] == 1, f"Expected 1 failed, got {sp['failed_stages']}"
    assert sp["percent"] == 67, f"Expected 67%, got {sp['percent']}"
    print("PASS: completed run has correct stage_progress counts")


def test_runs_list_preserves_existing_fields():
    """Adding stage_progress must not remove existing fields from /runs response."""
    resp = client.get("/api/runs")
    assert resp.status_code == 200
    data = resp.json()
    assert "runs" in data
    assert "total" in data
    if data["runs"]:
        run = data["runs"][0]
        expected_keys = [
            "id", "workflow", "status", "inputs", "created_at",
            "has_result", "duration_seconds", "total_tokens", "workflow_output",
        ]
        for key in expected_keys:
            assert key in run, f"Existing field '{key}' missing from run dict"
    print("PASS: existing fields preserved in /runs response")


# ── 3. extract_stage_progress edge cases ─────────────────────────

def test_stage_progress_handles_no_execution_key():
    """A run whose result has no 'execution' key should yield stage_progress: null."""
    resp = client.post(
        "/api/runs",
        json={"workflow": "sdlc_deploy_test", "inputs": {}},
    )
    run_id = resp.json()["id"]
    worker_id = f"test-worker-{uuid.uuid4()}"
    client.post(f"/api/runs/{run_id}/claim", json={"worker_id": worker_id})
    # Complete with result that lacks 'execution'
    client.put(
        f"/api/runs/{run_id}/status",
        json={"status": "completed", "result": {"some_other_key": 123}},
    )
    resp = client.get("/api/runs")
    our_run = next((r for r in resp.json()["runs"] if r["id"] == run_id), None)
    assert our_run is not None
    assert our_run.get("stage_progress") is None, (
        "stage_progress should be null when result has no execution key"
    )
    print("PASS: no execution key yields null stage_progress")


def test_stage_progress_handles_empty_nodes():
    """Empty nodes list should yield percent=0, not division-by-zero."""
    resp = client.post(
        "/api/runs",
        json={"workflow": "sdlc_deploy_test", "inputs": {}},
    )
    run_id = resp.json()["id"]
    worker_id = f"test-worker-{uuid.uuid4()}"
    client.post(f"/api/runs/{run_id}/claim", json={"worker_id": worker_id})
    client.put(
        f"/api/runs/{run_id}/status",
        json={"status": "completed", "result": {"execution": {"nodes": []}}},
    )
    resp = client.get("/api/runs")
    our_run = next((r for r in resp.json()["runs"] if r["id"] == run_id), None)
    assert our_run is not None
    # With empty nodes, either null or {percent: 0} is acceptable
    sp = our_run.get("stage_progress")
    if sp is not None:
        assert sp["percent"] == 0, f"Expected percent=0 for empty nodes, got {sp['percent']}"
        assert sp["total_stages"] == 0
    print("PASS: empty nodes handled without division-by-zero")


# ── 4. Health endpoint not broken ────────────────────────────────

def test_health_still_works():
    """Sanity check: /api/health is not broken by changes."""
    resp = client.get("/api/health")
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok"}
    print("PASS: health endpoint still works")


# ── 5. No route conflict ────────────────────────────────────────

def test_progress_bar_config_no_route_conflict():
    """Ensure /progress-bar-config does not shadow other config endpoints."""
    # typewriter-config should still work
    resp = client.get("/api/typewriter-config")
    assert resp.status_code == 200
    assert "lines" in resp.json()
    print("PASS: no route conflict with existing config endpoints")


# ── Runner ───────────────────────────────────────────────────────

ALL_TESTS = [
    test_progress_bar_config_returns_200,
    test_runs_list_includes_stage_progress_null_for_pending,
    test_runs_list_includes_stage_progress_for_completed,
    test_runs_list_preserves_existing_fields,
    test_stage_progress_handles_no_execution_key,
    test_stage_progress_handles_empty_nodes,
    test_health_still_works,
    test_progress_bar_config_no_route_conflict,
]

if __name__ == "__main__":
    passed = 0
    failed = 0
    for test_fn in ALL_TESTS:
        try:
            test_fn()
            passed += 1
        except Exception as e:
            print(f"FAIL: {test_fn.__name__}: {e}")
            failed += 1

    print(f"\nResults: {passed} passed, {failed} failed out of {len(ALL_TESTS)} tests")
    if failed > 0:
        print("SOME TESTS FAILED (expected — feature not implemented yet)")
        sys.exit(1)
    else:
        print("ALL TESTS PASSED")

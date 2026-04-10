"""Acceptance tests for GET /api/run-counts endpoint.

Tests the new run-counts endpoint that returns count badges for
filter tabs: all, deployed, rejected, failed, running, pending.
"""

import sys
import json
from fastapi.testclient import TestClient
from server.app import app
from server.database import get_session, engine
from server.models import Run
from sqlmodel import Session, select

client = TestClient(app)

EXPECTED_KEYS = {"all", "deployed", "rejected", "failed", "running", "pending"}


def _create_run(session: Session, status: str, result_json: str | None = None) -> Run:
    """Helper to insert a run directly into the database."""
    import uuid
    run = Run(
        id=str(uuid.uuid4()),
        workflow="test-workflow",
        status=status,
        inputs=json.dumps({"feature": "test"}),
        result=result_json,
    )
    session.add(run)
    session.commit()
    session.refresh(run)
    return run


def _clear_runs(session: Session):
    """Remove all runs from the database."""
    runs = session.exec(select(Run)).all()
    for run in runs:
        session.delete(run)
    session.commit()


def test_run_counts_endpoint_exists():
    """GET /api/run-counts returns 200 with the correct JSON shape."""
    response = client.get("/api/run-counts")
    assert response.status_code == 200, f"Expected 200, got {response.status_code}"
    data = response.json()
    assert isinstance(data, dict), f"Expected dict, got {type(data)}"
    assert set(data.keys()) == EXPECTED_KEYS, f"Expected keys {EXPECTED_KEYS}, got {set(data.keys())}"
    for key in EXPECTED_KEYS:
        assert isinstance(data[key], int), f"Expected int for '{key}', got {type(data[key])}"
    print("PASS: run-counts endpoint exists with correct shape")


def test_run_counts_empty_database():
    """With zero runs, all counts should be zero."""
    with Session(engine) as session:
        _clear_runs(session)

    response = client.get("/api/run-counts")
    assert response.status_code == 200
    data = response.json()
    expected = {"all": 0, "deployed": 0, "rejected": 0, "failed": 0, "running": 0, "pending": 0}
    assert data == expected, f"Expected {expected}, got {data}"
    print("PASS: empty database returns all zeros")


def test_run_counts_all_equals_sum():
    """counts['all'] must equal the sum of the other five categories."""
    with Session(engine) as session:
        _clear_runs(session)
        _create_run(session, "pending")
        _create_run(session, "running")
        _create_run(session, "failed")
        # completed with no REJECT -> deployed
        _create_run(session, "completed", json.dumps({"execution": {"workflow_output": {"result": "DEPLOY"}}}))
        # completed with REJECT -> rejected
        _create_run(session, "completed", json.dumps({"execution": {"workflow_output": {"result": "REJECT"}}}))

    response = client.get("/api/run-counts")
    assert response.status_code == 200
    data = response.json()
    category_sum = data["deployed"] + data["rejected"] + data["failed"] + data["running"] + data["pending"]
    assert data["all"] == category_sum, f"all={data['all']} != sum={category_sum}"
    assert data["all"] == 5, f"Expected all=5, got {data['all']}"
    print("PASS: all equals sum of categories")


def test_classify_completed_reject():
    """A completed run with workflow_output.result='REJECT' must be counted as 'rejected'."""
    with Session(engine) as session:
        _clear_runs(session)
        _create_run(session, "completed", json.dumps({"execution": {"workflow_output": {"result": "REJECT"}}}))

    response = client.get("/api/run-counts")
    assert response.status_code == 200
    data = response.json()
    assert data["rejected"] == 1, f"Expected rejected=1, got {data['rejected']}"
    assert data["deployed"] == 0, f"Expected deployed=0, got {data['deployed']}"
    print("PASS: completed REJECT -> rejected")


def test_classify_completed_lowercase_reject():
    """A completed run with workflow_output.result='reject' (lowercase) must also be 'rejected'."""
    with Session(engine) as session:
        _clear_runs(session)
        _create_run(session, "completed", json.dumps({"execution": {"workflow_output": {"result": "reject"}}}))

    response = client.get("/api/run-counts")
    assert response.status_code == 200
    data = response.json()
    assert data["rejected"] == 1, f"Expected rejected=1, got {data['rejected']}"
    print("PASS: completed reject (lowercase) -> rejected")


def test_classify_completed_deployed():
    """A completed run without REJECT result must be counted as 'deployed'."""
    with Session(engine) as session:
        _clear_runs(session)
        _create_run(session, "completed", json.dumps({"execution": {"workflow_output": {"result": "DEPLOY"}}}))

    response = client.get("/api/run-counts")
    assert response.status_code == 200
    data = response.json()
    assert data["deployed"] == 1, f"Expected deployed=1, got {data['deployed']}"
    assert data["rejected"] == 0, f"Expected rejected=0, got {data['rejected']}"
    print("PASS: completed non-REJECT -> deployed")


def test_classify_failed():
    """A failed run must be counted as 'failed'."""
    with Session(engine) as session:
        _clear_runs(session)
        _create_run(session, "failed")

    response = client.get("/api/run-counts")
    assert response.status_code == 200
    data = response.json()
    assert data["failed"] == 1, f"Expected failed=1, got {data['failed']}"
    print("PASS: failed -> failed")


def test_classify_claimed_as_running():
    """A claimed run must be counted as 'running' (matching frontend getOutcome logic)."""
    with Session(engine) as session:
        _clear_runs(session)
        _create_run(session, "claimed")

    response = client.get("/api/run-counts")
    assert response.status_code == 200
    data = response.json()
    assert data["running"] == 1, f"Expected running=1, got {data['running']}"
    print("PASS: claimed -> running")


def test_classify_pending():
    """A pending run must be counted as 'pending'."""
    with Session(engine) as session:
        _clear_runs(session)
        _create_run(session, "pending")

    response = client.get("/api/run-counts")
    assert response.status_code == 200
    data = response.json()
    assert data["pending"] == 1, f"Expected pending=1, got {data['pending']}"
    print("PASS: pending -> pending")


def test_existing_health_endpoint():
    """Existing GET /api/health must still return 200 with {status: ok}."""
    response = client.get("/api/health")
    assert response.status_code == 200
    data = response.json()
    assert data == {"status": "ok"}, f"Unexpected health response: {data}"
    print("PASS: /api/health still works")


def test_existing_pipeline_stats_endpoint():
    """Existing GET /api/pipeline-stats must still return 200 with correct shape."""
    response = client.get("/api/pipeline-stats")
    assert response.status_code == 200
    data = response.json()
    assert "completed" in data and "failed" in data and "total" in data, f"Unexpected shape: {data}"
    print("PASS: /api/pipeline-stats still works")


def test_existing_runs_endpoint():
    """Existing GET /api/runs must still return paginated results unchanged."""
    response = client.get("/api/runs")
    assert response.status_code == 200
    data = response.json()
    assert "runs" in data and "total" in data, f"Unexpected shape: {data}"
    assert isinstance(data["runs"], list)
    assert isinstance(data["total"], int)
    print("PASS: /api/runs still works")


ALL_TESTS = [
    test_run_counts_endpoint_exists,
    test_run_counts_empty_database,
    test_run_counts_all_equals_sum,
    test_classify_completed_reject,
    test_classify_completed_lowercase_reject,
    test_classify_completed_deployed,
    test_classify_failed,
    test_classify_claimed_as_running,
    test_classify_pending,
    test_existing_health_endpoint,
    test_existing_pipeline_stats_endpoint,
    test_existing_runs_endpoint,
]

if __name__ == "__main__":
    passed = 0
    failed = 0
    for test in ALL_TESTS:
        try:
            test()
            passed += 1
        except Exception as e:
            print(f"FAIL: {test.__name__}: {e}")
            failed += 1

    print(f"\nResults: {passed} passed, {failed} failed out of {len(ALL_TESTS)} tests")
    if failed > 0:
        sys.exit(1)
    else:
        print("ALL TESTS PASSED")

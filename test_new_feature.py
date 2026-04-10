"""Acceptance tests for GET /api/mini-chart-config endpoint.

Tests are written BEFORE the feature is implemented — they should FAIL initially.
"""

import sys
import os
from datetime import UTC, datetime, timedelta

# Use in-memory SQLite for tests
os.environ["DATABASE_URL"] = "sqlite://"

from fastapi.testclient import TestClient
from sqlmodel import Session, SQLModel

from server.app import app
from server.database import engine, init_db
from server.models import Run

client = TestClient(app)


def _reset_db():
    """Drop and recreate all tables for a clean slate."""
    SQLModel.metadata.drop_all(engine)
    SQLModel.metadata.create_all(engine)


def _create_run(session: Session, status: str, result: str | None = None,
                created_at: datetime | None = None) -> Run:
    """Helper to insert a Run with the given status and created_at."""
    import uuid
    run = Run(
        id=str(uuid.uuid4()),
        workflow="test-workflow",
        status=status,
        result=result,
        created_at=created_at or datetime.now(UTC),
    )
    session.add(run)
    session.commit()
    session.refresh(run)
    return run


def test_happy_path_returns_200_with_valid_schema():
    """GET /api/mini-chart-config returns 200 with all required fields."""
    _reset_db()
    response = client.get("/api/mini-chart-config")
    assert response.status_code == 200, f"Expected 200, got {response.status_code}"
    data = response.json()
    # Check all top-level fields exist
    for field in ("bar_color_success", "bar_color_failure", "bar_width_px",
                  "bar_gap_px", "chart_height_px", "point_count", "data_points"):
        assert field in data, f"Missing field: {field}"
    assert isinstance(data["data_points"], list)
    assert data["point_count"] == 7
    assert isinstance(data["bar_width_px"], int)
    assert isinstance(data["bar_gap_px"], int)
    assert isinstance(data["chart_height_px"], int)
    print("PASS: happy path returns 200 with valid schema")


def test_zero_finished_runs_returns_empty_data_points():
    """With no finished runs, data_points should be an empty list and no 500."""
    _reset_db()
    # Insert only pending and running runs — these should be excluded
    with Session(engine) as session:
        _create_run(session, status="pending")
        _create_run(session, status="running")
    response = client.get("/api/mini-chart-config")
    assert response.status_code == 200, f"Expected 200, got {response.status_code}"
    data = response.json()
    assert data["data_points"] == [], f"Expected empty data_points, got {data['data_points']}"
    assert data["point_count"] == 7
    print("PASS: zero finished runs returns empty data_points")


def test_mixed_outcomes_computes_correct_rates():
    """With a mix of deployed/rejected/failed runs, rates are correct."""
    _reset_db()
    today = datetime.now(UTC)
    with Session(engine) as session:
        # 2 deployed + 1 failed + 1 rejected on the same day = rate 2/4 = 0.5
        _create_run(session, status="completed", result='{"output": {"result": "ACCEPT"}}', created_at=today)
        _create_run(session, status="completed", result='{"output": {"result": "ACCEPT"}}', created_at=today)
        _create_run(session, status="failed", created_at=today)
        _create_run(session, status="completed", result='{"output": {"result": "REJECT"}}', created_at=today)
        # A pending run that should be excluded
        _create_run(session, status="pending", created_at=today)

    response = client.get("/api/mini-chart-config")
    assert response.status_code == 200
    data = response.json()
    assert len(data["data_points"]) == 1, f"Expected 1 data point, got {len(data['data_points'])}"
    dp = data["data_points"][0]
    assert dp["total"] == 4, f"Expected total=4, got {dp['total']}"
    assert dp["successful"] == 2, f"Expected successful=2, got {dp['successful']}"
    assert dp["rate"] == 0.5, f"Expected rate=0.5, got {dp['rate']}"
    print("PASS: mixed outcomes computes correct rates")


def test_data_points_sorted_chronologically():
    """data_points should be sorted by date ascending."""
    _reset_db()
    today = datetime.now(UTC)
    with Session(engine) as session:
        for i in range(5):
            day = today - timedelta(days=4 - i)
            _create_run(session, status="completed", result='{"output": {"result": "ACCEPT"}}', created_at=day)

    response = client.get("/api/mini-chart-config")
    assert response.status_code == 200
    data = response.json()
    dates = [dp["date"] for dp in data["data_points"]]
    assert dates == sorted(dates), f"data_points not sorted chronologically: {dates}"
    print("PASS: data_points sorted chronologically")


def test_at_most_7_data_points():
    """Even with more than 7 days of data, at most 7 data_points are returned."""
    _reset_db()
    today = datetime.now(UTC)
    with Session(engine) as session:
        for i in range(10):
            day = today - timedelta(days=9 - i)
            _create_run(session, status="completed", result='{"output": {"result": "ACCEPT"}}', created_at=day)

    response = client.get("/api/mini-chart-config")
    assert response.status_code == 200
    data = response.json()
    assert len(data["data_points"]) <= 7, f"Expected at most 7 data_points, got {len(data['data_points'])}"
    print("PASS: at most 7 data_points")


def test_excludes_pending_and_running_from_counts():
    """Pending and running runs must not appear in any data_point counts."""
    _reset_db()
    today = datetime.now(UTC)
    with Session(engine) as session:
        _create_run(session, status="completed", result='{"output": {"result": "ACCEPT"}}', created_at=today)
        _create_run(session, status="pending", created_at=today)
        _create_run(session, status="running", created_at=today)
        _create_run(session, status="claimed", created_at=today)

    response = client.get("/api/mini-chart-config")
    assert response.status_code == 200
    data = response.json()
    assert len(data["data_points"]) == 1
    dp = data["data_points"][0]
    assert dp["total"] == 1, f"Expected total=1 (only deployed), got {dp['total']}"
    assert dp["successful"] == 1
    assert dp["rate"] == 1.0
    print("PASS: excludes pending and running from counts")


def test_rate_values_between_0_and_1():
    """All rate values must be between 0.0 and 1.0 inclusive, rounded to 2 decimals."""
    _reset_db()
    today = datetime.now(UTC)
    with Session(engine) as session:
        # 1 deployed out of 3 = 0.33
        _create_run(session, status="completed", result='{"output": {"result": "ACCEPT"}}', created_at=today)
        _create_run(session, status="failed", created_at=today)
        _create_run(session, status="failed", created_at=today)

    response = client.get("/api/mini-chart-config")
    assert response.status_code == 200
    data = response.json()
    for dp in data["data_points"]:
        assert 0.0 <= dp["rate"] <= 1.0, f"Rate out of range: {dp['rate']}"
        # Check rounded to 2 decimals
        assert dp["rate"] == round(dp["rate"], 2), f"Rate not rounded to 2 decimals: {dp['rate']}"
    print("PASS: rate values between 0 and 1, rounded to 2 decimals")


def test_existing_endpoints_still_work():
    """Existing endpoints must not be broken by the new code."""
    _reset_db()
    for path in ("/api/health", "/api/run-counts", "/api/gradient-banner-config"):
        resp = client.get(path)
        assert resp.status_code == 200, f"{path} returned {resp.status_code}, expected 200"
    print("PASS: existing endpoints still work")


if __name__ == "__main__":
    tests = [
        test_happy_path_returns_200_with_valid_schema,
        test_zero_finished_runs_returns_empty_data_points,
        test_mixed_outcomes_computes_correct_rates,
        test_data_points_sorted_chronologically,
        test_at_most_7_data_points,
        test_excludes_pending_and_running_from_counts,
        test_rate_values_between_0_and_1,
        test_existing_endpoints_still_work,
    ]
    failed = []
    for test_fn in tests:
        try:
            test_fn()
        except Exception as e:
            print(f"FAIL: {test_fn.__name__}: {e}")
            failed.append(test_fn.__name__)

    print(f"\n{'=' * 60}")
    print(f"Ran {len(tests)} tests: {len(tests) - len(failed)} passed, {len(failed)} failed")
    if failed:
        print(f"Failed tests: {', '.join(failed)}")
        sys.exit(1)
    else:
        print("ALL TESTS PASSED")

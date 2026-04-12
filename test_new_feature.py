"""Acceptance tests for cost_dollars field in run API responses."""

import sys
from fastapi.testclient import TestClient
from server.app import app

client = TestClient(app)


def test_cost_dollars_in_list_runs():
    """GET /api/runs returns cost_dollars field in each run object."""
    # Verify the helper function and constant are importable
    from server.routes import calculate_cost_dollars, COST_PER_TOKEN

    # Verify COST_PER_TOKEN is a positive number
    assert isinstance(COST_PER_TOKEN, (int, float)), f"COST_PER_TOKEN should be numeric, got {type(COST_PER_TOKEN)}"
    assert COST_PER_TOKEN > 0, f"COST_PER_TOKEN should be positive, got {COST_PER_TOKEN}"

    # Verify calculate_cost_dollars returns correct types
    assert calculate_cost_dollars(None) is None, "calculate_cost_dollars(None) should return None"
    assert isinstance(calculate_cost_dollars(1000), float), "calculate_cost_dollars(1000) should return a float"
    assert calculate_cost_dollars(0) == 0.0, "calculate_cost_dollars(0) should return 0.0"

    # Verify the API response includes cost_dollars
    response = client.get("/api/runs")
    assert response.status_code == 200, f"Expected 200, got {response.status_code}"
    data = response.json()
    runs = data["runs"]
    for run in runs:
        assert "cost_dollars" in run, (
            f"cost_dollars missing from run {run['id']}, keys: {sorted(run.keys())}"
        )
        # cost_dollars should be a number or null
        val = run["cost_dollars"]
        assert val is None or isinstance(val, (int, float)), (
            f"cost_dollars should be number or null, got {type(val)} for run {run['id']}"
        )
    print("PASS: cost_dollars in list runs")


def test_cost_dollars_in_get_run():
    """GET /api/runs/{run_id} returns cost_dollars field."""
    # Fetch a run ID from the list endpoint
    response = client.get("/api/runs?limit=1")
    assert response.status_code == 200, f"Expected 200, got {response.status_code}"
    data = response.json()
    runs = data["runs"]
    if len(runs) == 0:
        # No runs in DB -- verify at least via the helper function
        from server.routes import calculate_cost_dollars
        assert calculate_cost_dollars(1_000_000) is not None, (
            "calculate_cost_dollars should return a value for non-None input"
        )
        print("PASS: cost_dollars in get_run (no runs in DB, verified helper)")
        return

    run_id = runs[0]["id"]
    response = client.get(f"/api/runs/{run_id}")
    assert response.status_code == 200, f"Expected 200, got {response.status_code}"
    run_data = response.json()
    assert "cost_dollars" in run_data, (
        f"cost_dollars missing from run detail, keys: {sorted(run_data.keys())}"
    )
    val = run_data["cost_dollars"]
    assert val is None or isinstance(val, (int, float)), (
        f"cost_dollars should be number or null, got {type(val)}"
    )
    print("PASS: cost_dollars in get_run")


if __name__ == "__main__":
    passed = 0
    failed = 0
    for test_fn in [
        test_cost_dollars_in_list_runs,
        test_cost_dollars_in_get_run,
    ]:
        try:
            test_fn()
            passed += 1
        except Exception as e:
            print(f"FAIL: {test_fn.__name__}: {e}")
            failed += 1

    print(f"\nResults: {passed} passed, {failed} failed out of {passed + failed}")
    if failed > 0:
        sys.exit(1)
    print("ALL TESTS PASSED")

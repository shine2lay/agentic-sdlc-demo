"""Acceptance tests for the countdown timer config endpoint and community creations update."""

import sys
from fastapi.testclient import TestClient
from server.app import app

client = TestClient(app)


def test_countdown_timer_config_happy_path():
    """GET /api/countdown-timer-config returns 200 with all expected fields and values."""
    response = client.get("/api/countdown-timer-config")
    assert response.status_code == 200, f"Expected 200, got {response.status_code}"
    data = response.json()
    assert data["title"] == "Countdown Timer", f"Expected title 'Countdown Timer', got {data.get('title')}"
    assert data["default_minutes"] == 5, f"Expected default_minutes 5, got {data.get('default_minutes')}"
    assert data["default_seconds"] == 0, f"Expected default_seconds 0, got {data.get('default_seconds')}"
    assert data["min_seconds"] == 1, f"Expected min_seconds 1, got {data.get('min_seconds')}"
    assert data["max_seconds"] == 5999, f"Expected max_seconds 5999, got {data.get('max_seconds')}"
    print("PASS: countdown timer config happy path")


def test_community_creations_includes_timer():
    """GET /api/community-creations-config includes a Countdown Timer entry."""
    response = client.get("/api/community-creations-config")
    assert response.status_code == 200, f"Expected 200, got {response.status_code}"
    data = response.json()
    creations = data.get("creations", [])
    timer_entries = [c for c in creations if c.get("name") == "Countdown Timer"]
    assert len(timer_entries) == 1, f"Expected 1 'Countdown Timer' entry in creations, found {len(timer_entries)}"
    assert timer_entries[0]["path"] == "/tools/timer", f"Expected path '/tools/timer', got {timer_entries[0].get('path')}"
    print("PASS: community creations includes timer")


def test_regression_existing_endpoints():
    """Verify existing endpoints still work (regression check)."""
    # Health endpoint
    resp = client.get("/api/health")
    assert resp.status_code == 200, f"Health check failed: {resp.status_code}"
    assert resp.json() == {"status": "ok"}, f"Health response unexpected: {resp.json()}"

    # ASCII art config
    resp = client.get("/api/ascii-art-config")
    assert resp.status_code == 200, f"ASCII art config failed: {resp.status_code}"

    # Community creations config
    resp = client.get("/api/community-creations-config")
    assert resp.status_code == 200, f"Community creations config failed: {resp.status_code}"

    # Import check for syntax errors
    from server.routes import router as _r
    assert _r is not None

    print("PASS: regression existing endpoints")


if __name__ == "__main__":
    passed = 0
    failed = 0
    for test_fn in [
        test_countdown_timer_config_happy_path,
        test_community_creations_includes_timer,
        test_regression_existing_endpoints,
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

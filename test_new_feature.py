"""Acceptance tests for the suggestions-count endpoint.

Tests that GET /api/suggestions-count returns a valid response
with total_suggestions (int >= 0) and poll_interval_ms (int == 10000).
The endpoint does not exist yet, so the new test is expected to FAIL.
"""

import sys
from fastapi.testclient import TestClient
from server.app import app

client = TestClient(app)


def test_existing_endpoints_not_broken():
    """Adding the new endpoint must not break health or other config endpoints."""
    # Health endpoint
    r = client.get("/api/health")
    assert r.status_code == 200, f"Health returned {r.status_code}"
    assert r.json() == {"status": "ok"}, f"Health body unexpected: {r.json()}"

    # Sparkle config must still have its own enabled field
    r = client.get("/api/sparkle-config")
    assert r.status_code == 200, f"sparkle-config returned {r.status_code}"
    spark = r.json()
    assert "enabled" in spark, "'enabled' missing from sparkle-config"

    # Gradient border config must still have its own enabled field
    r = client.get("/api/gradient-border-config")
    assert r.status_code == 200, f"gradient-border-config returned {r.status_code}"
    gb = r.json()
    assert "enabled" in gb, "'enabled' missing from gradient-border-config"

    print("PASS: existing endpoints still work correctly")


def test_suggestions_count_endpoint():
    """GET /api/suggestions-count must return total_suggestions and poll_interval_ms."""
    response = client.get("/api/suggestions-count")
    assert response.status_code == 200, f"Expected 200, got {response.status_code}"
    data = response.json()
    assert "total_suggestions" in data, f"'total_suggestions' missing from response: {data}"
    assert isinstance(data["total_suggestions"], int), f"total_suggestions should be int, got {type(data['total_suggestions'])}"
    assert data["total_suggestions"] >= 0, f"total_suggestions should be >= 0, got {data['total_suggestions']}"
    assert "poll_interval_ms" in data, f"'poll_interval_ms' missing from response: {data}"
    assert isinstance(data["poll_interval_ms"], int), f"poll_interval_ms should be int, got {type(data['poll_interval_ms'])}"
    assert data["poll_interval_ms"] == 10000, f"Expected poll_interval_ms=10000, got {data['poll_interval_ms']}"
    print("PASS: suggestions-count endpoint returns valid response")


if __name__ == "__main__":
    try:
        test_existing_endpoints_not_broken()
        test_suggestions_count_endpoint()
        print("ALL TESTS PASSED")
    except Exception as e:
        print(f"FAIL: {e}")
        sys.exit(1)

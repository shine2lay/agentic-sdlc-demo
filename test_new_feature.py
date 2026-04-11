"""Acceptance tests for the sparkle-config endpoint.

Tests the GET /api/sparkle-config endpoint that should return
sparkle animation configuration for the shipped count display.
The endpoint does not exist yet, so these tests are expected to FAIL.
"""

import sys
from fastapi.testclient import TestClient
from server.app import app

client = TestClient(app)


def test_sparkle_config_returns_200_with_all_fields():
    """GET /api/sparkle-config returns 200 with all expected fields and values."""
    response = client.get("/api/sparkle-config")
    assert response.status_code == 200, f"Expected 200, got {response.status_code}"
    data = response.json()

    # Verify all required fields exist
    required_fields = [
        "enabled", "particle_count", "duration_ms", "spread_px",
        "colors", "repeat_interval_ms", "size_px", "target",
    ]
    for field in required_fields:
        assert field in data, f"Missing field: {field}"

    # Verify expected static values
    assert data["enabled"] is True
    assert data["particle_count"] == 6
    assert data["duration_ms"] == 1200
    assert data["spread_px"] == 18
    assert data["colors"] == ["#fbbf24", "#f59e0b", "#d97706", "#ffffff"]
    assert data["repeat_interval_ms"] == 4000
    assert data["size_px"] == 6
    assert data["target"] == "shipped"

    print("PASS: sparkle-config returns 200 with all expected fields and values")


def test_existing_endpoints_still_work():
    """Existing /api/health and /api/parallax-config endpoints still return 200."""
    health = client.get("/api/health")
    assert health.status_code == 200, f"Health expected 200, got {health.status_code}"
    assert health.json().get("status") == "ok"

    parallax = client.get("/api/parallax-config")
    assert parallax.status_code == 200, f"Parallax-config expected 200, got {parallax.status_code}"

    print("PASS: existing endpoints (health, parallax-config) still return 200")


if __name__ == "__main__":
    try:
        test_sparkle_config_returns_200_with_all_fields()
        test_existing_endpoints_still_work()
        print("ALL TESTS PASSED")
    except Exception as e:
        print(f"FAIL: {e}")
        sys.exit(1)

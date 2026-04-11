"""Acceptance tests for GET /api/parallax-config endpoint.

These tests verify the parallax-config endpoint returns the correct
response shape and values, and that existing endpoints are unaffected.
"""

import sys
from fastapi.testclient import TestClient
from server.app import app

client = TestClient(app)

EXPECTED_PARALLAX = {
    "enabled": True,
    "speed_factor": 0.3,
    "max_offset_px": 120,
    "direction": "up",
    "easing": "ease-out",
}


def test_parallax_config_returns_200_with_correct_shape():
    """GET /api/parallax-config returns 200 with exact expected payload."""
    response = client.get("/api/parallax-config")
    assert response.status_code == 200, f"Expected 200, got {response.status_code}"
    data = response.json()
    assert data == EXPECTED_PARALLAX, f"Payload mismatch: {data}"
    # Verify individual field types
    assert isinstance(data["enabled"], bool)
    assert isinstance(data["speed_factor"], float)
    assert isinstance(data["max_offset_px"], int)
    assert isinstance(data["direction"], str)
    assert isinstance(data["easing"], str)
    print("PASS: parallax config returns 200 with correct shape and values")


def test_existing_endpoints_not_broken():
    """Existing config endpoints and health check still work after adding parallax-config."""
    # Health
    r = client.get("/api/health")
    assert r.status_code == 200
    assert r.json() == {"status": "ok"}

    # Typewriter config
    r = client.get("/api/typewriter-config")
    assert r.status_code == 200
    tw = r.json()
    assert "lines" in tw and "speed_ms" in tw and "start_delay_ms" in tw

    # Back-to-top config
    r = client.get("/api/back-to-top-config")
    assert r.status_code == 200
    btt = r.json()
    assert "enabled" in btt and "scroll_threshold_px" in btt

    print("PASS: existing endpoints (health, typewriter-config, back-to-top-config) still work")


if __name__ == "__main__":
    try:
        test_parallax_config_returns_200_with_correct_shape()
        test_existing_endpoints_not_broken()
        print("ALL TESTS PASSED")
    except Exception as e:
        print(f"FAIL: {e}")
        sys.exit(1)

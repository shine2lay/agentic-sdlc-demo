"""Acceptance tests for GET /api/fade-in-config endpoint.

Tests that the endpoint returns the correct fade-in animation configuration
for run cards, matching the expected response shape and values.
"""

import sys
from fastapi.testclient import TestClient
from server.app import app

client = TestClient(app)


def test_fade_in_config_returns_200_with_all_fields():
    """GET /api/fade-in-config returns HTTP 200 with all six expected fields and values."""
    response = client.get("/api/fade-in-config")
    assert response.status_code == 200, f"Expected 200, got {response.status_code}"
    assert response.headers["content-type"] == "application/json"
    data = response.json()
    assert data == {
        "duration_ms": 400,
        "delay_ms": 0,
        "easing": "ease-out",
        "translate_y_px": 12,
        "stagger_ms": 60,
        "initial_opacity": 0.0,
    }, f"Unexpected response body: {data}"
    print("PASS: fade-in config returns 200 with all fields")


def test_existing_endpoints_unaffected():
    """Existing config endpoints still return HTTP 200 with unchanged shapes."""
    # /api/health
    r = client.get("/api/health")
    assert r.status_code == 200, f"/api/health returned {r.status_code}"
    assert r.json() == {"status": "ok"}

    # /api/status-border-config
    r = client.get("/api/status-border-config")
    assert r.status_code == 200, f"/api/status-border-config returned {r.status_code}"
    data = r.json()
    assert "border_width_px" in data
    assert "colors" in data

    # /api/dot-grid-config
    r = client.get("/api/dot-grid-config")
    assert r.status_code == 200, f"/api/dot-grid-config returned {r.status_code}"
    data = r.json()
    assert "dot_size_px" in data or "spacing_px" in data or "color" in data

    print("PASS: existing endpoints unaffected")


if __name__ == "__main__":
    try:
        test_fade_in_config_returns_200_with_all_fields()
        test_existing_endpoints_unaffected()
        print("ALL TESTS PASSED")
    except Exception as e:
        print(f"FAIL: {e}")
        sys.exit(1)

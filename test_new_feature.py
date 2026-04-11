"""Acceptance tests for the gradient-border-config endpoint.

Tests the GET /api/gradient-border-config endpoint that should return
gradient border animation configuration for the suggestion input box.
The endpoint does not exist yet, so these tests are expected to FAIL.
"""

import sys
from fastapi.testclient import TestClient
from server.app import app

client = TestClient(app)


def test_gradient_border_config_returns_all_fields():
    """GET /api/gradient-border-config returns 200 with all 7 expected fields."""
    response = client.get("/api/gradient-border-config")
    assert response.status_code == 200, f"Expected 200, got {response.status_code}"
    data = response.json()
    expected_fields = {
        "enabled", "colors", "angle_deg",
        "animation_duration_ms", "border_width_px",
        "border_radius", "target",
    }
    missing = expected_fields - set(data.keys())
    assert not missing, f"Missing fields: {missing}"
    # Validate types
    assert isinstance(data["enabled"], bool), "enabled should be bool"
    assert isinstance(data["colors"], list), "colors should be a list"
    assert all(isinstance(c, str) for c in data["colors"]), "each color should be a string"
    assert isinstance(data["angle_deg"], int), "angle_deg should be int"
    assert isinstance(data["animation_duration_ms"], int), "animation_duration_ms should be int"
    assert isinstance(data["border_width_px"], int), "border_width_px should be int"
    assert isinstance(data["border_radius"], str), "border_radius should be str"
    assert isinstance(data["target"], str), "target should be str"
    print("PASS: gradient-border-config returns all fields with correct types")


def test_existing_endpoints_not_broken():
    """Verify /api/health and /api/sparkle-config still work (no regression)."""
    health = client.get("/api/health")
    assert health.status_code == 200, f"health: expected 200, got {health.status_code}"
    assert health.json() == {"status": "ok"}, f"health: unexpected body {health.json()}"

    sparkle = client.get("/api/sparkle-config")
    assert sparkle.status_code == 200, f"sparkle-config: expected 200, got {sparkle.status_code}"
    sparkle_data = sparkle.json()
    assert "enabled" in sparkle_data, "sparkle-config missing 'enabled' field"
    assert "colors" in sparkle_data, "sparkle-config missing 'colors' field"
    print("PASS: existing endpoints (health, sparkle-config) not broken")


if __name__ == "__main__":
    try:
        test_gradient_border_config_returns_all_fields()
        test_existing_endpoints_not_broken()
        print("ALL TESTS PASSED")
    except Exception as e:
        print(f"FAIL: {e}")
        sys.exit(1)

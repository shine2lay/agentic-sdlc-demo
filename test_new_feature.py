"""Acceptance tests for GET /api/back-to-top-config endpoint.

Tests that the endpoint returns a 200 with all expected fields and correct types,
and that existing endpoints are not broken by the new addition.
These tests should FAIL until the feature is implemented.
"""

import sys
from fastapi.testclient import TestClient
from server.app import app

client = TestClient(app)


def test_back_to_top_config_returns_200_with_all_fields():
    """Happy path: endpoint exists and returns all 11 config fields with correct types and values."""
    response = client.get("/api/back-to-top-config")
    assert response.status_code == 200, f"Expected 200, got {response.status_code}"
    data = response.json()

    # Verify all 11 fields are present
    expected_fields = [
        "enabled",
        "scroll_threshold_px",
        "position_right_px",
        "position_bottom_px",
        "size_px",
        "bg_color",
        "hover_bg_color",
        "icon_color",
        "border_radius",
        "transition_ms",
        "scroll_behavior",
    ]
    for field in expected_fields:
        assert field in data, f"Missing field: {field}"

    # Verify types
    assert isinstance(data["enabled"], bool), "enabled should be bool"
    assert isinstance(data["scroll_threshold_px"], int), "scroll_threshold_px should be int"
    assert isinstance(data["position_right_px"], int), "position_right_px should be int"
    assert isinstance(data["position_bottom_px"], int), "position_bottom_px should be int"
    assert isinstance(data["size_px"], int), "size_px should be int"
    assert isinstance(data["bg_color"], str), "bg_color should be str"
    assert isinstance(data["hover_bg_color"], str), "hover_bg_color should be str"
    assert isinstance(data["icon_color"], str), "icon_color should be str"
    assert isinstance(data["border_radius"], str), "border_radius should be str"
    assert isinstance(data["transition_ms"], int), "transition_ms should be int"
    assert isinstance(data["scroll_behavior"], str), "scroll_behavior should be str"

    # Verify expected default values
    assert data["enabled"] is True
    assert data["scroll_threshold_px"] == 400
    assert data["position_right_px"] == 32
    assert data["position_bottom_px"] == 32
    assert data["size_px"] == 44
    assert data["bg_color"] == "#6366f1"
    assert data["hover_bg_color"] == "#4f46e5"
    assert data["icon_color"] == "#ffffff"
    assert data["border_radius"] == "50%"
    assert data["transition_ms"] == 200
    assert data["scroll_behavior"] == "smooth"

    print("PASS: happy path — back-to-top config returns 200 with all fields and correct values")


def test_existing_endpoints_not_broken():
    """Regression: existing config and health endpoints still work after adding the new one."""
    health = client.get("/api/health")
    assert health.status_code == 200, f"Health check failed: {health.status_code}"
    assert health.json().get("status") == "ok"

    typewriter = client.get("/api/typewriter-config")
    assert typewriter.status_code == 200, f"Typewriter config failed: {typewriter.status_code}"
    assert "lines" in typewriter.json()

    progress = client.get("/api/progress-bar-config")
    assert progress.status_code == 200, f"Progress bar config failed: {progress.status_code}"
    assert "bar_height_px" in progress.json()

    print("PASS: existing endpoints still work")


if __name__ == "__main__":
    try:
        test_back_to_top_config_returns_200_with_all_fields()
        test_existing_endpoints_not_broken()
        print("ALL TESTS PASSED")
    except Exception as e:
        print(f"FAIL: {e}")
        sys.exit(1)

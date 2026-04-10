"""Acceptance tests for GET /api/skeleton-config endpoint.

Tests the shimmer loading skeleton configuration endpoint that should return
all 8 fields with values matching existing frontend defaults.
"""

import sys

from fastapi.testclient import TestClient

from server.app import app

client = TestClient(app)

EXPECTED_RESPONSE = {
    "rows": 8,
    "row_height_px": 72,
    "shimmer_duration_ms": 1500,
    "border_radius_px": 8,
    "gap_px": 12,
    "base_color": "#1e293b",
    "shimmer_color": "#334155",
    "shimmer_angle_deg": 90,
}

REQUIRED_FIELDS = [
    "rows",
    "row_height_px",
    "shimmer_duration_ms",
    "border_radius_px",
    "gap_px",
    "base_color",
    "shimmer_color",
    "shimmer_angle_deg",
]


def test_skeleton_config_returns_200_with_all_fields():
    """GET /api/skeleton-config returns 200 with all 8 expected fields and correct values."""
    response = client.get("/api/skeleton-config")
    assert response.status_code == 200, f"Expected 200, got {response.status_code}"
    data = response.json()
    for field in REQUIRED_FIELDS:
        assert field in data, f"Missing field: {field}"
    assert data == EXPECTED_RESPONSE, f"Response mismatch: {data}"
    print("PASS: skeleton-config returns 200 with all fields and correct values")


def test_existing_endpoints_unaffected():
    """Verify /api/health and /api/checkmark-config still work correctly."""
    # Health check
    health = client.get("/api/health")
    assert health.status_code == 200, f"Health expected 200, got {health.status_code}"
    assert health.json() == {"status": "ok"}, f"Health response changed: {health.json()}"

    # Checkmark config should still return its fields
    checkmark = client.get("/api/checkmark-config")
    assert checkmark.status_code == 200, f"Checkmark expected 200, got {checkmark.status_code}"
    checkmark_data = checkmark.json()
    for field in ["size_px", "stroke_color", "stroke_width_px", "animation_duration_ms", "display_duration_ms", "easing"]:
        assert field in checkmark_data, f"Checkmark missing field: {field}"
    print("PASS: existing endpoints /api/health and /api/checkmark-config unaffected")


if __name__ == "__main__":
    try:
        test_skeleton_config_returns_200_with_all_fields()
        test_existing_endpoints_unaffected()
        print("ALL TESTS PASSED")
    except Exception as e:
        print(f"FAIL: {e}")
        sys.exit(1)

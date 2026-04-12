"""Acceptance tests for the active tab shimmer config feature."""

import sys
from fastapi.testclient import TestClient
from server.app import app

client = TestClient(app)


def test_active_tab_shimmer_config_returns_200_with_all_fields():
    """GET /api/active-tab-shimmer-config returns 200 with all required fields."""
    response = client.get("/api/active-tab-shimmer-config")
    assert response.status_code == 200, f"Expected 200, got {response.status_code}"
    data = response.json()
    assert data["enabled"] is True
    assert isinstance(data["gradient_colors"], list)
    assert len(data["gradient_colors"]) == 5, f"Expected 5 gradient colors, got {len(data['gradient_colors'])}"
    assert data["animation_duration_ms"] == 2000
    assert data["angle_deg"] == 120
    assert data["shimmer_width_percent"] == 30
    assert data["opacity"] == 0.6
    assert data["respect_reduced_motion"] is True
    assert data["target"] == "active-filter-tab"
    expected_fields = {"enabled", "gradient_colors", "animation_duration_ms", "angle_deg", "shimmer_width_percent", "opacity", "respect_reduced_motion", "target"}
    assert set(data.keys()) == expected_fields, f"Field mismatch: {set(data.keys()) ^ expected_fields}"
    print("PASS: active tab shimmer config returns 200 with all fields")


def test_active_tab_shimmer_config_response_gradient_colors_are_strings():
    """Each entry in gradient_colors must be a non-empty string."""
    response = client.get("/api/active-tab-shimmer-config")
    assert response.status_code == 200, f"Expected 200, got {response.status_code}"
    data = response.json()
    for i, color in enumerate(data["gradient_colors"]):
        assert isinstance(color, str) and len(color) > 0, f"gradient_colors[{i}] is not a non-empty string: {color!r}"
    print("PASS: gradient_colors entries are all non-empty strings")


if __name__ == "__main__":
    try:
        test_active_tab_shimmer_config_returns_200_with_all_fields()
        test_active_tab_shimmer_config_response_gradient_colors_are_strings()
        print("ALL TESTS PASSED")
    except Exception as e:
        print(f"FAIL: {e}")
        sys.exit(1)

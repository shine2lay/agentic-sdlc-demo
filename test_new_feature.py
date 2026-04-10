"""Acceptance tests for GET /api/dot-grid-config endpoint.

Tests the new dot-grid-config endpoint that returns dot size, spacing,
color, and opacity for the page background dot grid pattern.
"""

import sys
from fastapi.testclient import TestClient
from server.app import app

client = TestClient(app)


def test_dot_grid_config_returns_200_with_expected_shape():
    """GET /api/dot-grid-config returns 200 with dot_size_px, dot_spacing_px, dot_color, dot_opacity."""
    response = client.get("/api/dot-grid-config")
    assert response.status_code == 200, f"Expected 200, got {response.status_code}"
    data = response.json()

    assert "dot_size_px" in data, "Missing 'dot_size_px' key in response"
    assert "dot_spacing_px" in data, "Missing 'dot_spacing_px' key in response"
    assert "dot_color" in data, "Missing 'dot_color' key in response"
    assert "dot_opacity" in data, "Missing 'dot_opacity' key in response"

    assert isinstance(data["dot_size_px"], float), "dot_size_px must be a float"
    assert isinstance(data["dot_spacing_px"], int), "dot_spacing_px must be an int"
    assert isinstance(data["dot_color"], str), "dot_color must be a string"
    assert isinstance(data["dot_opacity"], float), "dot_opacity must be a float"

    print("PASS: dot grid config returns 200 with expected shape")


def test_dot_grid_config_returns_correct_values():
    """GET /api/dot-grid-config returns the exact configured values."""
    response = client.get("/api/dot-grid-config")
    assert response.status_code == 200, f"Expected 200, got {response.status_code}"
    data = response.json()

    assert data["dot_size_px"] == 1.5, f"dot_size_px should be 1.5, got {data['dot_size_px']}"
    assert data["dot_spacing_px"] == 24, f"dot_spacing_px should be 24, got {data['dot_spacing_px']}"
    assert data["dot_color"] == "#7dd3fc", f"dot_color should be '#7dd3fc', got {data['dot_color']}"
    assert data["dot_opacity"] == 0.08, f"dot_opacity should be 0.08, got {data['dot_opacity']}"

    print("PASS: dot grid config returns correct values")


def test_existing_endpoints_not_broken():
    """Existing endpoints /api/health and /api/pipeline-stages still work."""
    health = client.get("/api/health")
    assert health.status_code == 200, f"/api/health returned {health.status_code}"
    assert health.json().get("status") == "ok", "Health check should return status ok"

    stages = client.get("/api/pipeline-stages")
    assert stages.status_code == 200, f"/api/pipeline-stages returned {stages.status_code}"
    stages_data = stages.json()
    assert "stages" in stages_data, "Pipeline stages response missing 'stages' key"

    print("PASS: existing endpoints not broken")


if __name__ == "__main__":
    passed = 0
    failed = 0
    for test_fn in [
        test_dot_grid_config_returns_200_with_expected_shape,
        test_dot_grid_config_returns_correct_values,
        test_existing_endpoints_not_broken,
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

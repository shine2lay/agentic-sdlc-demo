"""Acceptance tests for GET /api/deploy-checkmark-config endpoint."""

import sys
from fastapi.testclient import TestClient
from server.app import app

client = TestClient(app)


def test_deploy_checkmark_config_returns_200_with_all_fields():
    """Happy path: endpoint returns 200 with all 13 expected fields and correct values."""
    response = client.get("/api/deploy-checkmark-config")
    assert response.status_code == 200, f"Expected 200, got {response.status_code}"
    assert response.headers["content-type"] == "application/json"

    data = response.json()

    # Verify all 13 fields exist with correct types and values
    assert data["enabled"] is True
    assert data["size_px"] == 20
    assert data["stroke_color"] == "#34d399"
    assert data["fill_opacity"] == 0.1
    assert isinstance(data["fill_opacity"], float)
    assert data["circle_stroke_width"] == 2.0
    assert isinstance(data["circle_stroke_width"], float)
    assert data["check_stroke_width"] == 2.5
    assert isinstance(data["check_stroke_width"], float)
    assert data["circle_animation_duration_ms"] == 400
    assert data["draw_animation_duration_ms"] == 300
    assert data["draw_animation_delay_ms"] == 200
    assert data["easing"] == "ease-out"
    assert data["respect_reduced_motion"] is True
    assert data["animate_only_on_transition"] is True
    assert data["target"] == "deployed-run-card"

    # Verify exactly 13 fields, no extras
    assert len(data) == 13, f"Expected 13 fields, got {len(data)}: {list(data.keys())}"

    print("PASS: deploy checkmark config returns 200 with all fields and correct values")


def test_existing_endpoints_not_regressed():
    """Regression: existing config endpoints still return 200."""
    shimmer = client.get("/api/active-tab-shimmer-config")
    assert shimmer.status_code == 200, f"active-tab-shimmer-config regressed: {shimmer.status_code}"

    typing = client.get("/api/typing-test-config")
    assert typing.status_code == 200, f"typing-test-config regressed: {typing.status_code}"

    print("PASS: existing config endpoints not regressed")


if __name__ == "__main__":
    try:
        test_deploy_checkmark_config_returns_200_with_all_fields()
        test_existing_endpoints_not_regressed()
        print("ALL TESTS PASSED")
    except Exception as e:
        print(f"FAIL: {e}")
        sys.exit(1)

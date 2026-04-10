"""Acceptance tests for GET /api/status-border-config endpoint.

Tests that the endpoint returns border styling config and a color mapping
whose keys match the five outcomes from classify_run_outcome().
"""

import sys

from fastapi.testclient import TestClient

from server.app import app

client = TestClient(app)

EXPECTED_OUTCOME_KEYS = {"deployed", "rejected", "failed", "running", "pending"}


def test_status_border_config_returns_valid_response():
    """Happy path: endpoint returns 200 with correct structure and values."""
    response = client.get("/api/status-border-config")
    assert response.status_code == 200, f"Expected 200, got {response.status_code}"
    data = response.json()

    # Verify border styling fields
    assert data["border_width_px"] == 3
    assert data["border_radius_px"] == 2
    assert data["border_side"] == "left"

    # Verify colors dict has exactly the 5 outcome keys
    colors = data["colors"]
    assert isinstance(colors, dict), "colors should be a dict"
    assert set(colors.keys()) == EXPECTED_OUTCOME_KEYS, (
        f"Expected keys {EXPECTED_OUTCOME_KEYS}, got {set(colors.keys())}"
    )

    # Verify each color value is a non-empty hex string
    for key, value in colors.items():
        assert isinstance(value, str) and value.startswith("#"), (
            f"Color for '{key}' should be a hex string, got {value!r}"
        )

    print("PASS: status-border-config returns valid response")


def test_existing_endpoints_still_work():
    """Regression: existing config endpoints remain functional."""
    for path in ("/api/health", "/api/typewriter-config", "/api/dot-grid-config"):
        response = client.get(path)
        assert response.status_code == 200, (
            f"Expected 200 for {path}, got {response.status_code}"
        )
    print("PASS: existing endpoints still return 200")


if __name__ == "__main__":
    passed = 0
    failed = 0
    all_tests = [
        test_status_border_config_returns_valid_response,
        test_existing_endpoints_still_work,
    ]
    for test in all_tests:
        try:
            test()
            passed += 1
        except Exception as e:
            print(f"FAIL: {test.__name__}: {e}")
            failed += 1

    print(f"\nResults: {passed} passed, {failed} failed out of {len(all_tests)} tests")
    if failed > 0:
        sys.exit(1)
    else:
        print("ALL TESTS PASSED")

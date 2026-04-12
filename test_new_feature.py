"""Acceptance tests for GET /api/deploy-visit-confetti-config endpoint.

Tests verify the deploy-visit confetti configuration endpoint returns
correct status, all 17 fields with exact values, and that the existing
/api/confetti-config endpoint remains unchanged (no regression).
"""

import sys
from fastapi.testclient import TestClient
from server.app import app

client = TestClient(app)

# Expected values for the new deploy-visit-confetti-config endpoint
EXPECTED_DEPLOY_VISIT = {
    "enabled": True,
    "particle_count": 80,
    "duration_ms": 2500,
    "spread_deg": 120,
    "colors": ["#34d399", "#6366f1", "#fbbf24", "#ec4899", "#3b82f6", "#a78bfa"],
    "gravity": 0.6,
    "drift": 0.3,
    "size_range": [5, 12],
    "shapes": ["circle", "square", "star"],
    "origin_x": 0.5,
    "origin_y": 0.3,
    "trigger": "first-visit",
    "trigger_status": "deployed",
    "first_visit_only": True,
    "cooldown_session_key": "confetti_seen_run_{run_id}",
    "respect_reduced_motion": True,
    "target": "run-detail-page",
}

# Expected values for the existing confetti-config endpoint (regression check)
EXPECTED_ORIGINAL = {
    "enabled": True,
    "particle_count": 40,
    "duration_ms": 1500,
    "spread_px": 60,
    "colors": ["#34d399", "#6366f1", "#fbbf24", "#ec4899", "#3b82f6"],
    "gravity": 0.8,
    "drift": 0.5,
    "size_range": [4, 8],
    "shapes": ["circle", "square"],
    "trigger": "status-change",
    "trigger_from": "running",
    "trigger_to": "deployed",
    "respect_reduced_motion": True,
    "target": "run-card",
    "max_concurrent": 3,
}


def test_deploy_visit_confetti_config_returns_all_fields():
    """GET /api/deploy-visit-confetti-config returns 200 with all 17 fields matching exact values."""
    response = client.get("/api/deploy-visit-confetti-config")
    assert response.status_code == 200, f"Expected 200 but got {response.status_code}"
    data = response.json()
    # Verify every expected key-value pair
    for key, expected_value in EXPECTED_DEPLOY_VISIT.items():
        assert key in data, f"Missing field: {key}"
        assert data[key] == expected_value, (
            f"Field '{key}': expected {expected_value!r}, got {data[key]!r}"
        )
    # Verify no extra fields beyond the 17 expected
    assert set(data.keys()) == set(EXPECTED_DEPLOY_VISIT.keys()), (
        f"Unexpected fields: {set(data.keys()) - set(EXPECTED_DEPLOY_VISIT.keys())}"
    )
    # Specifically verify cooldown_session_key has literal curly braces (not interpolated)
    assert "{run_id}" in data["cooldown_session_key"], (
        "cooldown_session_key should contain literal {run_id} placeholder"
    )
    print("PASS: deploy-visit-confetti-config returns all 17 fields with correct values")


def test_existing_confetti_config_unchanged():
    """GET /api/confetti-config still returns 200 with its original 15 fields unchanged (regression)."""
    response = client.get("/api/confetti-config")
    assert response.status_code == 200, f"Expected 200 but got {response.status_code}"
    data = response.json()
    for key, expected_value in EXPECTED_ORIGINAL.items():
        assert key in data, f"Missing field in original endpoint: {key}"
        assert data[key] == expected_value, (
            f"Original endpoint field '{key}': expected {expected_value!r}, got {data[key]!r}"
        )
    assert set(data.keys()) == set(EXPECTED_ORIGINAL.keys()), (
        f"Original endpoint has unexpected fields: {set(data.keys()) - set(EXPECTED_ORIGINAL.keys())}"
    )
    # Verify the original model uses spread_px (not spread_deg)
    assert "spread_px" in data, "Original endpoint must use spread_px, not spread_deg"
    assert "spread_deg" not in data, "Original endpoint must NOT have spread_deg"
    print("PASS: existing confetti-config endpoint unchanged (no regression)")


if __name__ == "__main__":
    passed = 0
    failed = 0
    for test_fn in [test_deploy_visit_confetti_config_returns_all_fields, test_existing_confetti_config_unchanged]:
        try:
            test_fn()
            passed += 1
        except Exception as e:
            print(f"FAIL: {test_fn.__name__}: {e}")
            failed += 1
    print(f"\nResults: {passed} passed, {failed} failed out of {passed + failed}")
    if failed:
        sys.exit(1)
    print("ALL TESTS PASSED")

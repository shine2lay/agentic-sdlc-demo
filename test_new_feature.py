"""Acceptance tests for GET /api/noise-texture-config endpoint.

Tests verify the noise texture background configuration endpoint returns
correct status, content type, field names, types, and values.
Also verifies existing endpoints remain unaffected.
"""

import sys
from fastapi.testclient import TestClient
from server.app import app

client = TestClient(app)

EXPECTED_RESPONSE = {
    "enabled": True,
    "noise_opacity": 0.04,
    "base_background_color": "#0f172a",
    "noise_grain_size_px": 2,
    "animation_speed_ms": 8000,
    "noise_intensity": 0.15,
    "blend_mode": "overlay",
    "z_index": -1,
    "respect_reduced_motion": True,
    "target": "page-background",
}

EXPECTED_FIELD_TYPES = {
    "enabled": bool,
    "noise_opacity": float,
    "base_background_color": str,
    "noise_grain_size_px": int,
    "animation_speed_ms": int,
    "noise_intensity": float,
    "blend_mode": str,
    "z_index": int,
    "respect_reduced_motion": bool,
    "target": str,
}


def test_noise_texture_config_returns_200_with_all_fields():
    """GET /api/noise-texture-config returns 200 with correct JSON body."""
    response = client.get("/api/noise-texture-config")
    assert response.status_code == 200, f"Expected 200, got {response.status_code}"
    assert response.headers["content-type"] == "application/json", (
        f"Expected application/json, got {response.headers['content-type']}"
    )
    data = response.json()
    # Check all 10 fields present
    for field in EXPECTED_RESPONSE:
        assert field in data, f"Missing field: {field}"
    # Check exact values
    for field, expected_value in EXPECTED_RESPONSE.items():
        actual = data[field]
        assert actual == expected_value, (
            f"Field '{field}': expected {expected_value!r}, got {actual!r}"
        )
    # Check types
    for field, expected_type in EXPECTED_FIELD_TYPES.items():
        actual = data[field]
        assert isinstance(actual, expected_type), (
            f"Field '{field}': expected type {expected_type.__name__}, got {type(actual).__name__}"
        )
    # No extra fields beyond the 10 expected
    assert set(data.keys()) == set(EXPECTED_RESPONSE.keys()), (
        f"Unexpected extra fields: {set(data.keys()) - set(EXPECTED_RESPONSE.keys())}"
    )
    print("PASS: noise texture config returns 200 with all fields and correct values")


def test_existing_endpoints_still_work():
    """Existing config endpoints and suggest endpoint remain functional."""
    # community-creations-config
    r = client.get("/api/community-creations-config")
    assert r.status_code == 200, f"community-creations-config: expected 200, got {r.status_code}"
    cc_data = r.json()
    assert "title" in cc_data, "community-creations-config missing 'title'"
    assert "creations" in cc_data, "community-creations-config missing 'creations'"

    # emoji-rain-config
    r = client.get("/api/emoji-rain-config")
    assert r.status_code == 200, f"emoji-rain-config: expected 200, got {r.status_code}"

    # POST /api/suggest with empty body should return 400
    r = client.post("/api/suggest", json={"suggestion": ""})
    assert r.status_code == 400, f"suggest empty: expected 400, got {r.status_code}"

    # POST /api/suggest with valid input should return 200
    r = client.post("/api/suggest", json={"suggestion": "test suggestion from acceptance test"})
    assert r.status_code == 200, f"suggest valid: expected 200, got {r.status_code}"

    print("PASS: existing endpoints still work correctly")


if __name__ == "__main__":
    passed = 0
    failed = 0
    for test_fn in [test_noise_texture_config_returns_200_with_all_fields, test_existing_endpoints_still_work]:
        try:
            test_fn()
            passed += 1
        except Exception as e:
            print(f"FAIL: {test_fn.__name__}: {e}")
            failed += 1
    print(f"\nResults: {passed} passed, {failed} failed out of {passed + failed} tests")
    if failed:
        sys.exit(1)
    print("ALL TESTS PASSED")

"""
Acceptance tests for GET /api/checkmark-config endpoint.

This endpoint should return a static JSON config for the suggestion submit
success checkmark animation with six required fields.
"""
import sys
from fastapi.testclient import TestClient
from server.app import app

client = TestClient(app)

EXPECTED_RESPONSE = {
    "size_px": 48,
    "stroke_color": "#22c55e",
    "stroke_width_px": 3,
    "animation_duration_ms": 600,
    "display_duration_ms": 1500,
    "easing": "ease-out",
}


def test_checkmark_config_returns_200_with_all_fields():
    """GET /api/checkmark-config returns 200 with all six expected fields and values."""
    response = client.get("/api/checkmark-config")
    assert response.status_code == 200, f"Expected 200, got {response.status_code}"
    data = response.json()
    assert data == EXPECTED_RESPONSE, f"Response mismatch: {data}"
    print("PASS: checkmark-config returns 200 with correct body")


def test_checkmark_config_stroke_color_matches_status_border_deployed():
    """stroke_color in /checkmark-config matches the deployed color in /status-border-config."""
    checkmark_resp = client.get("/api/checkmark-config")
    assert checkmark_resp.status_code == 200, f"checkmark-config returned {checkmark_resp.status_code}"
    border_resp = client.get("/api/status-border-config")
    assert border_resp.status_code == 200, f"status-border-config returned {border_resp.status_code}"
    checkmark_color = checkmark_resp.json()["stroke_color"]
    deployed_color = border_resp.json()["colors"]["deployed"]
    assert checkmark_color == deployed_color, (
        f"Color mismatch: checkmark stroke_color={checkmark_color}, "
        f"status-border deployed={deployed_color}"
    )
    print("PASS: stroke_color matches deployed border color")


def test_existing_health_endpoint_not_regressed():
    """GET /api/health still returns 200 with {status: ok}."""
    response = client.get("/api/health")
    assert response.status_code == 200, f"Expected 200, got {response.status_code}"
    data = response.json()
    assert data == {"status": "ok"}, f"Unexpected health response: {data}"
    print("PASS: /api/health not regressed")


def test_existing_fade_in_config_not_regressed():
    """GET /api/fade-in-config still returns 200 with expected shape."""
    response = client.get("/api/fade-in-config")
    assert response.status_code == 200, f"Expected 200, got {response.status_code}"
    data = response.json()
    expected_keys = {"duration_ms", "delay_ms", "easing", "translate_y_px", "stagger_ms", "initial_opacity"}
    assert set(data.keys()) == expected_keys, f"Unexpected keys: {set(data.keys())}"
    print("PASS: /api/fade-in-config not regressed")


def test_checkmark_config_in_openapi_schema():
    """The /checkmark-config endpoint appears in the OpenAPI schema."""
    response = client.get("/openapi.json")
    assert response.status_code == 200
    paths = response.json().get("paths", {})
    assert "/api/checkmark-config" in paths, (
        f"/api/checkmark-config not found in OpenAPI paths: {list(paths.keys())}"
    )
    print("PASS: /api/checkmark-config listed in OpenAPI schema")


if __name__ == "__main__":
    failed = []
    tests = [
        test_checkmark_config_returns_200_with_all_fields,
        test_checkmark_config_stroke_color_matches_status_border_deployed,
        test_existing_health_endpoint_not_regressed,
        test_existing_fade_in_config_not_regressed,
        test_checkmark_config_in_openapi_schema,
    ]
    for t in tests:
        try:
            t()
        except Exception as e:
            print(f"FAIL: {t.__name__}: {e}")
            failed.append(t.__name__)

    print(f"\n{len(tests) - len(failed)}/{len(tests)} tests passed")
    if failed:
        print(f"Failed tests: {', '.join(failed)}")
        sys.exit(1)
    else:
        print("ALL TESTS PASSED")

"""
Acceptance tests for: GET /api/pipeline-glow-config endpoint.

Tests verify:
  - New endpoint returns 200 with all 12 fields, correct types and values
  - glow_color_rgb is green (102, 187, 106) matching emerald-500, not blue
  - total_stages is 7 matching STAGES array length
  - min/max interpolation ranges are valid (min < max)
  - Existing endpoints unaffected (health, confetti-config, ascii-art-config, sparkle-config)
"""
import sys
from fastapi.testclient import TestClient
from server.app import app

client = TestClient(app)

EXPECTED_FIELDS = {
    "enabled": bool,
    "glow_color_rgb": str,
    "min_blur_px": int,
    "max_blur_px": int,
    "min_spread_px": int,
    "max_spread_px": int,
    "min_opacity": float,
    "max_opacity": float,
    "animation_duration_ms": int,
    "total_stages": int,
    "respect_reduced_motion": bool,
    "target": str,
}


def test_pipeline_glow_config_happy_path():
    """GET /api/pipeline-glow-config returns 200 with all 12 fields and correct values."""
    response = client.get("/api/pipeline-glow-config")
    assert response.status_code == 200, f"Expected 200, got {response.status_code}"
    data = response.json()

    # All 12 fields present with correct types
    for field, expected_type in EXPECTED_FIELDS.items():
        assert field in data, f"Missing field: {field}"
        assert isinstance(data[field], expected_type), (
            f"Field '{field}' expected {expected_type.__name__}, got {type(data[field]).__name__}"
        )

    # Exact value checks
    assert data["glow_color_rgb"] == "102, 187, 106", (
        f"glow_color_rgb should be green '102, 187, 106' (emerald-500 #66bb6a), got '{data['glow_color_rgb']}'"
    )
    assert data["total_stages"] == 7, (
        f"total_stages should be 7 (matching STAGES array length), got {data['total_stages']}"
    )
    assert data["enabled"] is True
    assert data["respect_reduced_motion"] is True
    assert data["target"] == "pipeline-stage"
    assert data["animation_duration_ms"] == 2000

    # Interpolation range sanity: min < max for blur, spread, opacity
    assert data["min_blur_px"] < data["max_blur_px"], "min_blur_px must be < max_blur_px"
    assert data["min_spread_px"] < data["max_spread_px"], "min_spread_px must be < max_spread_px"
    assert data["min_opacity"] < data["max_opacity"], "min_opacity must be < max_opacity"

    # Exact min/max values
    assert data["min_blur_px"] == 4
    assert data["max_blur_px"] == 18
    assert data["min_spread_px"] == 1
    assert data["max_spread_px"] == 6
    assert data["min_opacity"] == 0.25
    assert data["max_opacity"] == 0.7

    print("PASS: pipeline-glow-config happy path - all 12 fields correct")


def test_regression_existing_endpoints():
    """Existing nearby endpoints still work after adding the new one."""
    # /api/health
    r = client.get("/api/health")
    assert r.status_code == 200, f"/api/health returned {r.status_code}"
    assert r.json().get("status") == "ok", f"/api/health body: {r.json()}"

    # /api/confetti-config (nearest neighbor)
    r = client.get("/api/confetti-config")
    assert r.status_code == 200, f"/api/confetti-config returned {r.status_code}"
    confetti = r.json()
    assert "enabled" in confetti, "confetti-config missing 'enabled'"

    # /api/ascii-art-config (other nearest neighbor)
    r = client.get("/api/ascii-art-config")
    assert r.status_code == 200, f"/api/ascii-art-config returned {r.status_code}"
    ascii_art = r.json()
    assert "enabled" in ascii_art, "ascii-art-config missing 'enabled'"

    # /api/sparkle-config
    r = client.get("/api/sparkle-config")
    assert r.status_code == 200, f"/api/sparkle-config returned {r.status_code}"

    # Verify no import errors
    from server.routes import router as _r
    assert _r is not None, "router import failed"

    print("PASS: regression - existing endpoints unchanged")


if __name__ == "__main__":
    try:
        test_pipeline_glow_config_happy_path()
        test_regression_existing_endpoints()
        print("ALL TESTS PASSED")
    except Exception as e:
        print(f"FAIL: {e}")
        sys.exit(1)

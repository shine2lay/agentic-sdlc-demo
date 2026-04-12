"""Acceptance tests for the emoji rain config endpoint."""

import sys
from fastapi.testclient import TestClient
from server.app import app

client = TestClient(app)


def test_emoji_rain_config_returns_200_with_all_fields():
    """GET /api/emoji-rain-config returns 200 with all 13 fields matching the schema."""
    response = client.get("/api/emoji-rain-config")
    assert response.status_code == 200, f"Expected 200, got {response.status_code}"
    assert response.headers["content-type"] == "application/json"
    data = response.json()

    # Verify all 13 required fields are present with correct types and values
    assert data["enabled"] is True
    assert isinstance(data["emojis"], list)
    assert len(data["emojis"]) == 10, f"Expected 10 emojis, got {len(data['emojis'])}"
    assert all(isinstance(e, str) and len(e) > 0 for e in data["emojis"])
    assert data["drop_count"] == 25
    assert isinstance(data["min_duration_ms"], int)
    assert isinstance(data["max_duration_ms"], int)
    assert isinstance(data["min_delay_ms"], int)
    assert isinstance(data["max_delay_ms"], int)
    assert isinstance(data["min_size_px"], int)
    assert isinstance(data["max_size_px"], int)
    assert isinstance(data["opacity"], float)
    assert data["z_index"] == -1
    assert data["respect_reduced_motion"] is True
    assert data["target"] == "hero-section"

    # Verify exactly 13 fields (no extras, no missing)
    expected_fields = {
        "enabled", "emojis", "drop_count",
        "min_duration_ms", "max_duration_ms",
        "min_delay_ms", "max_delay_ms",
        "min_size_px", "max_size_px",
        "opacity", "z_index",
        "respect_reduced_motion", "target",
    }
    assert set(data.keys()) == expected_fields, f"Field mismatch: {set(data.keys()) ^ expected_fields}"
    print("PASS: emoji rain config returns 200 with all fields")


def test_nearby_endpoints_not_regressed():
    """Countdown timer config and ascii-art-generate still work after insertion."""
    # Countdown timer config (GET, right before insertion point)
    r1 = client.get("/api/countdown-timer-config")
    assert r1.status_code == 200, f"countdown-timer-config returned {r1.status_code}"
    timer_data = r1.json()
    assert "title" in timer_data
    assert timer_data["default_minutes"] == 5
    print("PASS: countdown-timer-config not regressed")

    # ASCII art generate (POST, right after insertion point)
    r2 = client.post("/api/ascii-art-generate", json={"text": "HI"})
    assert r2.status_code == 200, f"ascii-art-generate returned {r2.status_code}"
    art_data = r2.json()
    assert "art" in art_data
    print("PASS: ascii-art-generate not regressed")


if __name__ == "__main__":
    try:
        test_emoji_rain_config_returns_200_with_all_fields()
        test_nearby_endpoints_not_regressed()
        print("ALL TESTS PASSED")
    except Exception as e:
        print(f"FAIL: {e}")
        sys.exit(1)

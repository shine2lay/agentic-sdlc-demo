"""Acceptance tests for the Confetti Config endpoint.

Tests that:
- GET /api/confetti-config returns 200
- Response contains all 15 required fields with correct types
- Field values match the expected configuration
- Trigger fields are correct for frontend animation logic
- All existing endpoints remain unbroken
The endpoint does not exist yet, so the new tests are expected to FAIL.
"""

import sys
from fastapi.testclient import TestClient
from server.app import app

client = TestClient(app)


def test_existing_endpoints_not_broken():
    """Adding the new feature must not break health or other config endpoints."""
    # Health endpoint
    r = client.get("/api/health")
    assert r.status_code == 200, f"Health returned {r.status_code}"
    assert r.json() == {"status": "ok"}, f"Health body unexpected: {r.json()}"

    # Sparkle config
    r = client.get("/api/sparkle-config")
    assert r.status_code == 200, f"sparkle-config returned {r.status_code}"
    assert "enabled" in r.json(), "'enabled' missing from sparkle-config"

    # Gradient border config
    r = client.get("/api/gradient-border-config")
    assert r.status_code == 200, f"gradient-border-config returned {r.status_code}"
    assert "enabled" in r.json(), "'enabled' missing from gradient-border-config"

    # Markdown preview config
    r = client.get("/api/markdown-preview-config")
    assert r.status_code == 200, f"markdown-preview-config returned {r.status_code}"
    assert r.json()["title"] == "Markdown Preview", "markdown title mismatch"

    # Color picker config
    r = client.get("/api/color-picker-config")
    assert r.status_code == 200, f"color-picker-config returned {r.status_code}"

    # Bounce button config
    r = client.get("/api/bounce-button-config")
    assert r.status_code == 200, f"bounce-button-config returned {r.status_code}"

    # Programming joke
    r = client.get("/api/programming-joke")
    assert r.status_code == 200, f"programming-joke returned {r.status_code}"

    # ASCII art config
    r = client.get("/api/ascii-art-config")
    assert r.status_code == 200, f"ascii-art-config returned {r.status_code}"

    print("PASS: existing endpoints still work correctly")


def test_confetti_config_returns_200():
    """GET /api/confetti-config must return HTTP 200."""
    response = client.get("/api/confetti-config")
    assert response.status_code == 200, f"Expected 200, got {response.status_code}"
    print("PASS: confetti-config returns 200")


def test_confetti_config_shape():
    """Response JSON must contain all 15 required fields."""
    response = client.get("/api/confetti-config")
    assert response.status_code == 200, f"Expected 200, got {response.status_code}"
    data = response.json()

    required_fields = [
        "enabled",
        "particle_count",
        "duration_ms",
        "spread_px",
        "colors",
        "gravity",
        "drift",
        "size_range",
        "shapes",
        "trigger",
        "trigger_from",
        "trigger_to",
        "respect_reduced_motion",
        "target",
        "max_concurrent",
    ]
    for field in required_fields:
        assert field in data, f"Missing required field: '{field}'"

    # Type checks
    assert isinstance(data["enabled"], bool), f"enabled should be bool, got {type(data['enabled'])}"
    assert isinstance(data["particle_count"], int), f"particle_count should be int, got {type(data['particle_count'])}"
    assert isinstance(data["duration_ms"], int), f"duration_ms should be int, got {type(data['duration_ms'])}"
    assert isinstance(data["spread_px"], int), f"spread_px should be int, got {type(data['spread_px'])}"
    assert isinstance(data["colors"], list), f"colors should be list, got {type(data['colors'])}"
    assert isinstance(data["gravity"], (int, float)), f"gravity should be float, got {type(data['gravity'])}"
    assert isinstance(data["drift"], (int, float)), f"drift should be float, got {type(data['drift'])}"
    assert isinstance(data["size_range"], list), f"size_range should be list, got {type(data['size_range'])}"
    assert isinstance(data["shapes"], list), f"shapes should be list, got {type(data['shapes'])}"
    assert isinstance(data["trigger"], str), f"trigger should be str, got {type(data['trigger'])}"
    assert isinstance(data["trigger_from"], str), f"trigger_from should be str, got {type(data['trigger_from'])}"
    assert isinstance(data["trigger_to"], str), f"trigger_to should be str, got {type(data['trigger_to'])}"
    assert isinstance(data["respect_reduced_motion"], bool), f"respect_reduced_motion should be bool, got {type(data['respect_reduced_motion'])}"
    assert isinstance(data["target"], str), f"target should be str, got {type(data['target'])}"
    assert isinstance(data["max_concurrent"], int), f"max_concurrent should be int, got {type(data['max_concurrent'])}"

    print("PASS: confetti-config response has all 15 fields with correct types")


def test_confetti_config_values():
    """Assert specific expected values for the confetti configuration."""
    response = client.get("/api/confetti-config")
    assert response.status_code == 200, f"Expected 200, got {response.status_code}"
    data = response.json()

    assert data["enabled"] is True, f"enabled should be True, got {data['enabled']}"
    assert data["particle_count"] == 40, f"particle_count should be 40, got {data['particle_count']}"
    assert data["duration_ms"] == 1500, f"duration_ms should be 1500, got {data['duration_ms']}"
    assert data["trigger_from"] == "running", f"trigger_from should be 'running', got {data['trigger_from']}"
    assert data["trigger_to"] == "deployed", f"trigger_to should be 'deployed', got {data['trigger_to']}"
    assert data["respect_reduced_motion"] is True, f"respect_reduced_motion should be True, got {data['respect_reduced_motion']}"
    assert data["max_concurrent"] == 3, f"max_concurrent should be 3, got {data['max_concurrent']}"
    assert len(data["colors"]) == 5, f"colors should have 5 entries, got {len(data['colors'])}"
    assert len(data["size_range"]) == 2, f"size_range should have 2 entries, got {len(data['size_range'])}"
    assert data["size_range"][0] < data["size_range"][1], f"size_range[0] should be < size_range[1], got {data['size_range']}"

    print("PASS: confetti-config values match expected configuration")


def test_confetti_config_trigger_fields():
    """Assert trigger fields the frontend relies on for animation logic."""
    response = client.get("/api/confetti-config")
    assert response.status_code == 200, f"Expected 200, got {response.status_code}"
    data = response.json()

    assert data["trigger"] == "status-change", f"trigger should be 'status-change', got {data['trigger']}"
    assert data["trigger_from"] == "running", f"trigger_from should be 'running', got {data['trigger_from']}"
    assert data["trigger_to"] == "deployed", f"trigger_to should be 'deployed', got {data['trigger_to']}"
    assert data["target"] == "run-card", f"target should be 'run-card', got {data['target']}"

    print("PASS: confetti-config trigger fields are correct")


if __name__ == "__main__":
    try:
        test_existing_endpoints_not_broken()
        test_confetti_config_returns_200()
        test_confetti_config_shape()
        test_confetti_config_values()
        test_confetti_config_trigger_fields()
        print("ALL TESTS PASSED")
    except Exception as e:
        print(f"FAIL: {e}")
        sys.exit(1)

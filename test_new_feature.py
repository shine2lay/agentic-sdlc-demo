"""Acceptance tests for the typewriter-config 'enabled' field.

Tests that GET /api/typewriter-config returns an 'enabled' boolean,
matching the pattern used by every other UI config endpoint
(back-to-top, parallax, sparkle, gradient-border).
The field does not exist yet, so these tests are expected to FAIL.
"""

import sys
from fastapi.testclient import TestClient
from server.app import app

client = TestClient(app)


def test_typewriter_config_has_enabled_field():
    """GET /api/typewriter-config must include 'enabled: true' plus all existing fields."""
    response = client.get("/api/typewriter-config")
    assert response.status_code == 200, f"Expected 200, got {response.status_code}"
    data = response.json()
    # Core assertion: 'enabled' field must exist and be a boolean
    assert "enabled" in data, f"'enabled' field missing from response: {data}"
    assert isinstance(data["enabled"], bool), f"'enabled' should be bool, got {type(data['enabled'])}"
    assert data["enabled"] is True, f"'enabled' should default to True, got {data['enabled']}"
    # Verify existing fields are still present and unchanged
    assert "lines" in data, "'lines' field missing"
    assert len(data["lines"]) == 2, f"Expected 2 lines, got {len(data['lines'])}"
    assert data["speed_ms"] == 80, f"Expected speed_ms=80, got {data['speed_ms']}"
    assert data["start_delay_ms"] == 300, f"Expected start_delay_ms=300, got {data['start_delay_ms']}"
    print("PASS: typewriter-config returns enabled field with all existing fields intact")


def test_existing_endpoints_not_broken():
    """Adding the enabled field must not break health or other config endpoints."""
    # Health endpoint
    r = client.get("/api/health")
    assert r.status_code == 200, f"Health returned {r.status_code}"
    assert r.json() == {"status": "ok"}, f"Health body unexpected: {r.json()}"

    # Sparkle config must still have its own enabled field
    r = client.get("/api/sparkle-config")
    assert r.status_code == 200, f"sparkle-config returned {r.status_code}"
    spark = r.json()
    assert "enabled" in spark, "'enabled' missing from sparkle-config"

    # Gradient border config must still have its own enabled field
    r = client.get("/api/gradient-border-config")
    assert r.status_code == 200, f"gradient-border-config returned {r.status_code}"
    gb = r.json()
    assert "enabled" in gb, "'enabled' missing from gradient-border-config"

    print("PASS: existing endpoints still work correctly")


if __name__ == "__main__":
    try:
        test_typewriter_config_has_enabled_field()
        test_existing_endpoints_not_broken()
        print("ALL TESTS PASSED")
    except Exception as e:
        print(f"FAIL: {e}")
        sys.exit(1)

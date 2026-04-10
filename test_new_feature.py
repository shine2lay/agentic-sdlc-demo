"""Acceptance tests for GET /api/typewriter-config endpoint.

Tests the new typewriter-config endpoint that returns heading lines,
typing speed, and start delay for the homepage typewriter animation.
"""

import sys
from fastapi.testclient import TestClient
from server.app import app

client = TestClient(app)


def test_typewriter_config_returns_200_with_expected_shape():
    """GET /api/typewriter-config returns 200 with lines, speed_ms, and start_delay_ms."""
    response = client.get("/api/typewriter-config")
    assert response.status_code == 200, f"Expected 200, got {response.status_code}"
    data = response.json()

    # Must contain the three top-level keys
    assert "lines" in data, "Missing 'lines' key in response"
    assert "speed_ms" in data, "Missing 'speed_ms' key in response"
    assert "start_delay_ms" in data, "Missing 'start_delay_ms' key in response"

    # lines must be a non-empty list of objects with text and css_class
    assert isinstance(data["lines"], list), "'lines' must be a list"
    assert len(data["lines"]) >= 2, "Expected at least 2 lines"
    for line in data["lines"]:
        assert "text" in line, "Each line must have a 'text' field"
        assert "css_class" in line, "Each line must have a 'css_class' field"

    # speed_ms and start_delay_ms must be positive integers
    assert isinstance(data["speed_ms"], int) and data["speed_ms"] > 0, "speed_ms must be a positive int"
    assert isinstance(data["start_delay_ms"], int) and data["start_delay_ms"] > 0, "start_delay_ms must be a positive int"

    print("PASS: typewriter config returns 200 with expected shape")


def test_typewriter_config_returns_correct_content():
    """GET /api/typewriter-config returns the specific heading lines and timing values."""
    response = client.get("/api/typewriter-config")
    assert response.status_code == 200, f"Expected 200, got {response.status_code}"
    data = response.json()

    # Verify exact line content
    assert data["lines"][0]["text"] == "Describe a change.", (
        f"First line text wrong: {data['lines'][0]['text']}"
    )
    assert data["lines"][0]["css_class"] == "", (
        f"First line css_class should be empty, got: {data['lines'][0]['css_class']}"
    )
    assert data["lines"][1]["text"] == "Watch AI build it.", (
        f"Second line text wrong: {data['lines'][1]['text']}"
    )
    assert data["lines"][1]["css_class"] == "accent", (
        f"Second line css_class should be 'accent', got: {data['lines'][1]['css_class']}"
    )

    # Verify timing values
    assert data["speed_ms"] == 80, f"speed_ms should be 80, got {data['speed_ms']}"
    assert data["start_delay_ms"] == 300, f"start_delay_ms should be 300, got {data['start_delay_ms']}"

    print("PASS: typewriter config returns correct content")


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
        test_typewriter_config_returns_200_with_expected_shape,
        test_typewriter_config_returns_correct_content,
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

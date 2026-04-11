"""Acceptance tests for the bounce-button-config endpoint.

Tests that GET /api/bounce-button-config returns a valid response
with all animation configuration fields (enabled, scale_start, scale_peak,
duration_ms, easing, iteration_count, delay_ms, debounce_ms,
skip_initial_render, respect_reduced_motion, target).
The endpoint does not exist yet, so the new test is expected to FAIL.
"""

import sys
from fastapi.testclient import TestClient
from server.app import app

client = TestClient(app)


def test_existing_endpoints_not_broken():
    """Adding the new endpoint must not break health or other config endpoints."""
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

    # Markdown preview config must still work
    r = client.get("/api/markdown-preview-config")
    assert r.status_code == 200, f"markdown-preview-config returned {r.status_code}"
    md = r.json()
    assert md["title"] == "Markdown Preview", f"markdown title mismatch: {md['title']}"

    # Color picker config must still work
    r = client.get("/api/color-picker-config")
    assert r.status_code == 200, f"color-picker-config returned {r.status_code}"

    # Programming joke must still work
    r = client.get("/api/programming-joke")
    assert r.status_code == 200, f"programming-joke returned {r.status_code}"

    print("PASS: existing endpoints still work correctly")


def test_programming_joke_endpoint():
    """GET /api/programming-joke must return joke and category strings."""
    response = client.get("/api/programming-joke")
    assert response.status_code == 200, f"Expected 200, got {response.status_code}"
    data = response.json()
    assert "joke" in data, f"'joke' missing from response: {data}"
    assert isinstance(data["joke"], str), f"joke should be str, got {type(data['joke'])}"
    assert len(data["joke"]) > 0, "joke should not be empty"
    assert "category" in data, f"'category' missing from response: {data}"
    assert isinstance(data["category"], str), f"category should be str, got {type(data['category'])}"
    print("PASS: programming-joke endpoint returns valid response")


def test_markdown_preview_config():
    """GET /api/markdown-preview-config must return title, default_markdown, editor_placeholder, debounce_ms."""
    response = client.get("/api/markdown-preview-config")
    assert response.status_code == 200, f"Expected 200, got {response.status_code}"
    data = response.json()
    assert data["title"] == "Markdown Preview", f"title mismatch: {data['title']}"
    assert isinstance(data["default_markdown"], str) and len(data["default_markdown"]) > 0, "default_markdown must be non-empty string"
    assert isinstance(data["editor_placeholder"], str) and len(data["editor_placeholder"]) > 0, "editor_placeholder must be non-empty string"
    assert data["debounce_ms"] == 200, f"debounce_ms mismatch: {data['debounce_ms']}"
    print("PASS: markdown-preview-config endpoint returns valid response")


def test_color_picker_config():
    """GET /api/color-picker-config must return title, default_color, formats, show_preview, preset_colors."""
    response = client.get("/api/color-picker-config")
    assert response.status_code == 200, f"Expected 200, got {response.status_code}"
    data = response.json()
    assert data["title"] == "Color Picker", f"title mismatch: {data['title']}"
    assert data["default_color"] == "#6366f1", f"default_color mismatch: {data['default_color']}"
    assert data["formats"] == ["hex", "rgb", "hsl"], f"formats mismatch: {data['formats']}"
    assert data["show_preview"] is True, f"show_preview mismatch: {data['show_preview']}"
    assert isinstance(data["preset_colors"], list), "preset_colors must be a list"
    assert len(data["preset_colors"]) == 9, f"Expected 9 preset colors, got {len(data['preset_colors'])}"
    for color in data["preset_colors"]:
        assert isinstance(color, str) and len(color) == 7 and color.startswith("#"), f"Invalid preset color: {color}"
    print("PASS: color-picker-config endpoint returns valid response")


def test_bounce_button_config():
    """GET /api/bounce-button-config must return all animation config fields."""
    response = client.get("/api/bounce-button-config")
    assert response.status_code == 200, f"Expected 200, got {response.status_code}"
    data = response.json()

    # Core toggle
    assert data["enabled"] is True, f"enabled mismatch: {data.get('enabled')}"

    # Scale animation parameters
    assert data["scale_start"] == 1.0, f"scale_start mismatch: {data.get('scale_start')}"
    assert data["scale_peak"] == 1.07, f"scale_peak mismatch: {data.get('scale_peak')}"

    # Timing
    assert data["duration_ms"] == 600, f"duration_ms mismatch: {data.get('duration_ms')}"
    assert data["easing"] == "cubic-bezier(0.34, 1.56, 0.64, 1)", f"easing mismatch: {data.get('easing')}"
    assert data["iteration_count"] == 2, f"iteration_count mismatch: {data.get('iteration_count')}"
    assert data["delay_ms"] == 100, f"delay_ms mismatch: {data.get('delay_ms')}"

    # Debounce to prevent rapid-fire animation on fast toggling
    assert data["debounce_ms"] == 300, f"debounce_ms mismatch: {data.get('debounce_ms')}"

    # Prevent bounce on initial page load / hydration
    assert data["skip_initial_render"] is True, f"skip_initial_render mismatch: {data.get('skip_initial_render')}"

    # Accessibility: respect prefers-reduced-motion
    assert data["respect_reduced_motion"] is True, f"respect_reduced_motion mismatch: {data.get('respect_reduced_motion')}"

    # Target element
    assert data["target"] == "submit-button", f"target mismatch: {data.get('target')}"

    print("PASS: bounce-button-config endpoint returns valid response")


if __name__ == "__main__":
    try:
        test_existing_endpoints_not_broken()
        test_programming_joke_endpoint()
        test_markdown_preview_config()
        test_color_picker_config()
        test_bounce_button_config()
        print("ALL TESTS PASSED")
    except Exception as e:
        print(f"FAIL: {e}")
        sys.exit(1)

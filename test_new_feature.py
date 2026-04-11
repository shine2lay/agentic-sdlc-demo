"""Acceptance tests for the color-picker-config endpoint.

Tests that GET /api/color-picker-config returns a valid response
with title, default_color, formats, show_preview, and preset_colors.
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


if __name__ == "__main__":
    try:
        test_existing_endpoints_not_broken()
        test_programming_joke_endpoint()
        test_markdown_preview_config()
        test_color_picker_config()
        print("ALL TESTS PASSED")
    except Exception as e:
        print(f"FAIL: {e}")
        sys.exit(1)

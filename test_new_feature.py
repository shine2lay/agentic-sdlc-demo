"""Acceptance tests for the ASCII Art Generator feature.

Tests that:
- GET /api/ascii-art-config returns valid configuration
- POST /api/ascii-art-generate produces block-letter ASCII art
- Empty/whitespace-only text is rejected with 400
- Long text is truncated to 20 characters
- Unknown/special characters don't crash the endpoint
- All existing endpoints remain unbroken
The endpoints do not exist yet, so the new tests are expected to FAIL.
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

    # ASCII art config (new — should return 200 once implemented)
    r = client.get("/api/ascii-art-config")
    assert r.status_code == 200, f"ascii-art-config returned {r.status_code}"

    print("PASS: existing endpoints still work correctly")


def test_ascii_art_config():
    """GET /api/ascii-art-config must return all configuration fields."""
    response = client.get("/api/ascii-art-config")
    assert response.status_code == 200, f"Expected 200, got {response.status_code}"
    data = response.json()

    assert data["title"] == "ASCII Art Generator", f"title mismatch: {data.get('title')}"
    assert data["default_text"] == "HELLO", f"default_text mismatch: {data.get('default_text')}"
    assert data["max_length"] == 20, f"max_length mismatch: {data.get('max_length')}"
    assert data["block_char"] == "#", f"block_char mismatch: {data.get('block_char')}"
    assert data["empty_char"] == " ", f"empty_char mismatch: {data.get('empty_char')}"
    assert data["supported_characters"] == "A-Z 0-9 ! ? . -", f"supported_characters mismatch: {data.get('supported_characters')}"
    assert data["letter_height"] == 5, f"letter_height mismatch: {data.get('letter_height')}"

    print("PASS: ascii-art-config endpoint returns valid response")


def test_ascii_art_generate():
    """POST /api/ascii-art-generate with valid text must return block art."""
    response = client.post("/api/ascii-art-generate", json={"text": "HI"})
    assert response.status_code == 200, f"Expected 200, got {response.status_code}"
    data = response.json()

    assert "art" in data, f"'art' missing from response: {data}"
    assert isinstance(data["art"], str), f"art should be str, got {type(data['art'])}"
    assert len(data["art"]) > 0, "art should not be empty"
    assert "#" in data["art"], "art should contain '#' characters"

    assert data["original_text"] == "HI", f"original_text mismatch: {data.get('original_text')}"
    assert data["height"] == 5, f"height mismatch: {data.get('height')}"
    assert data["width"] > 0, f"width should be > 0, got {data.get('width')}"

    print("PASS: ascii-art-generate endpoint returns valid art")


def test_ascii_art_generate_empty_text():
    """POST /api/ascii-art-generate with empty text must return 400."""
    response = client.post("/api/ascii-art-generate", json={"text": ""})
    assert response.status_code == 400, f"Expected 400 for empty text, got {response.status_code}"

    print("PASS: empty text rejected with 400")


def test_ascii_art_generate_whitespace_only():
    """POST /api/ascii-art-generate with whitespace-only text must return 400."""
    response = client.post("/api/ascii-art-generate", json={"text": "   "})
    assert response.status_code == 400, f"Expected 400 for whitespace-only text, got {response.status_code}"

    print("PASS: whitespace-only text rejected with 400")


def test_ascii_art_generate_truncation():
    """POST /api/ascii-art-generate with >20 chars must truncate original_text to 20."""
    response = client.post("/api/ascii-art-generate", json={"text": "ABCDEFGHIJKLMNOPQRSTUVWXYZ"})
    assert response.status_code == 200, f"Expected 200, got {response.status_code}"
    data = response.json()

    assert len(data["original_text"]) <= 20, f"original_text should be <= 20 chars, got {len(data['original_text'])}"

    print("PASS: long text truncated to 20 characters")


def test_ascii_art_generate_special_chars():
    """POST /api/ascii-art-generate with unknown characters must not crash."""
    response = client.post("/api/ascii-art-generate", json={"text": "@#$"})
    assert response.status_code == 200, f"Expected 200, got {response.status_code}"
    data = response.json()

    assert isinstance(data["art"], str), f"art should be str, got {type(data['art'])}"
    assert data["height"] == 5, f"height should be 5, got {data.get('height')}"

    print("PASS: special characters handled without crashing")


if __name__ == "__main__":
    try:
        test_existing_endpoints_not_broken()
        test_ascii_art_config()
        test_ascii_art_generate()
        test_ascii_art_generate_empty_text()
        test_ascii_art_generate_whitespace_only()
        test_ascii_art_generate_truncation()
        test_ascii_art_generate_special_chars()
        print("ALL TESTS PASSED")
    except Exception as e:
        print(f"FAIL: {e}")
        sys.exit(1)

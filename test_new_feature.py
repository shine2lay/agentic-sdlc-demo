"""Acceptance tests for the Community Creations Config endpoint.

Tests that:
- GET /api/community-creations-config returns 200
- Response contains title and creations fields with correct types
- Creations list has exactly 4 items with correct structure
- All creation paths match existing frontend routes
- All existing endpoints remain unbroken
The endpoint does not exist yet, so the new tests are expected to FAIL.
"""

import sys
from fastapi.testclient import TestClient
from server.app import app

client = TestClient(app)


def test_existing_endpoints_not_broken():
    """Adding the new feature must not break health or other config endpoints."""
    r = client.get("/api/health")
    assert r.status_code == 200, f"Health returned {r.status_code}"
    assert r.json() == {"status": "ok"}, f"Health body unexpected: {r.json()}"

    r = client.get("/api/sparkle-config")
    assert r.status_code == 200, f"sparkle-config returned {r.status_code}"

    r = client.get("/api/confetti-config")
    assert r.status_code == 200, f"confetti-config returned {r.status_code}"

    r = client.get("/api/ascii-art-config")
    assert r.status_code == 200, f"ascii-art-config returned {r.status_code}"

    print("PASS: existing endpoints still work correctly")


def test_community_creations_config_returns_200():
    """GET /api/community-creations-config must return HTTP 200."""
    response = client.get("/api/community-creations-config")
    assert response.status_code == 200, f"Expected 200, got {response.status_code}"
    print("PASS: community-creations-config returns 200")


def test_community_creations_config_shape():
    """Response JSON must contain title and creations fields."""
    response = client.get("/api/community-creations-config")
    assert response.status_code == 200
    data = response.json()

    assert "title" in data, "Missing 'title' field"
    assert "creations" in data, "Missing 'creations' field"
    assert isinstance(data["title"], str), f"title should be str, got {type(data['title'])}"
    assert isinstance(data["creations"], list), f"creations should be list, got {type(data['creations'])}"

    for item in data["creations"]:
        assert "name" in item, f"Missing 'name' in creation item: {item}"
        assert "description" in item, f"Missing 'description' in creation item: {item}"
        assert "path" in item, f"Missing 'path' in creation item: {item}"
        assert isinstance(item["name"], str), f"name should be str, got {type(item['name'])}"
        assert isinstance(item["description"], str), f"description should be str, got {type(item['description'])}"
        assert isinstance(item["path"], str), f"path should be str, got {type(item['path'])}"

    print("PASS: community-creations-config has correct shape")


def test_community_creations_config_values():
    """Assert specific expected values for the community creations."""
    response = client.get("/api/community-creations-config")
    assert response.status_code == 200
    data = response.json()

    assert data["title"] == "These pages were built entirely by AI from user suggestions"
    assert len(data["creations"]) == 4, f"Expected 4 creations, got {len(data['creations'])}"

    paths = [c["path"] for c in data["creations"]]
    assert "/games/tictactoe" in paths, "/games/tictactoe missing from creations"
    assert "/tools/colors" in paths, "/tools/colors missing from creations"
    assert "/tools/ascii" in paths, "/tools/ascii missing from creations"
    assert "/tools/markdown" in paths, "/tools/markdown missing from creations"

    for item in data["creations"]:
        assert len(item["description"]) > 0, f"Empty description for {item['name']}"
        assert item["path"].startswith("/"), f"Path should start with /, got {item['path']}"

    print("PASS: community-creations-config values match expected")


if __name__ == "__main__":
    try:
        test_existing_endpoints_not_broken()
        test_community_creations_config_returns_200()
        test_community_creations_config_shape()
        test_community_creations_config_values()
        print("ALL TESTS PASSED")
    except Exception as e:
        print(f"FAIL: {e}")
        sys.exit(1)

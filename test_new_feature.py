"""Acceptance tests for the programming-joke endpoint.

Tests that GET /api/programming-joke returns a valid response
with joke (non-empty string) and category (string).
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


if __name__ == "__main__":
    try:
        test_existing_endpoints_not_broken()
        test_programming_joke_endpoint()
        print("ALL TESTS PASSED")
    except Exception as e:
        print(f"FAIL: {e}")
        sys.exit(1)

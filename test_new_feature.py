"""Acceptance tests for GET /api/agent-fun-fact endpoint.

Tests that the endpoint returns a random fun fact about the AI agents
with 'fact' (str) and 'category' (str) fields, where category is one
of the known categories.

These tests are expected to FAIL until the feature is implemented.
"""

import sys
from fastapi.testclient import TestClient
from server.app import app

client = TestClient(app)

VALID_CATEGORIES = [
    "architecture", "safety", "humor", "security",
    "process", "performance", "community",
]


def test_agent_fun_fact_returns_200_with_valid_payload():
    response = client.get("/api/agent-fun-fact")
    assert response.status_code == 200, f"Expected 200, got {response.status_code}"
    data = response.json()
    assert "fact" in data, "Response missing 'fact' field"
    assert "category" in data, "Response missing 'category' field"
    assert isinstance(data["fact"], str) and len(data["fact"]) > 0, "fact must be a non-empty string"
    assert data["category"] in VALID_CATEGORIES, (
        f"category '{data['category']}' not in {VALID_CATEGORIES}"
    )
    print("PASS: agent fun fact returns 200 with valid payload")


def test_agent_fun_fact_facts_are_under_90_chars():
    # Call multiple times to sample facts and verify length constraint
    seen_facts = set()
    for _ in range(30):
        response = client.get("/api/agent-fun-fact")
        assert response.status_code == 200
        fact = response.json()["fact"]
        seen_facts.add(fact)
    for fact in seen_facts:
        assert len(fact) <= 90, f"Fact exceeds 90 chars ({len(fact)}): {fact}"
    print(f"PASS: all {len(seen_facts)} sampled facts are under 90 characters")


if __name__ == "__main__":
    try:
        test_agent_fun_fact_returns_200_with_valid_payload()
        test_agent_fun_fact_facts_are_under_90_chars()
        print("ALL TESTS PASSED")
    except Exception as e:
        print(f"FAIL: {e}")
        sys.exit(1)

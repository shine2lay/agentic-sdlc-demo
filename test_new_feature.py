"""Acceptance tests for the tic-tac-toe config endpoint.

Tests that GET /api/tictactoe-config returns valid game configuration
with board_size, player_symbols, player_colors, winning_length,
empty_cell, and title fields.
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


def test_tictactoe_config_endpoint():
    """GET /api/tictactoe-config must return valid game configuration."""
    response = client.get("/api/tictactoe-config")
    assert response.status_code == 200, f"Expected 200, got {response.status_code}"
    data = response.json()
    assert data["board_size"] == 3, f"Expected board_size=3, got {data['board_size']}"
    assert data["winning_length"] == 3, f"Expected winning_length=3, got {data['winning_length']}"
    assert data["player_symbols"] == ["X", "O"], f"Unexpected player_symbols: {data['player_symbols']}"
    assert len(data["player_colors"]) == 2, f"Expected 2 player_colors, got {len(data['player_colors'])}"
    assert data["empty_cell"] == "", f"Expected empty_cell='', got {data['empty_cell']}"
    assert data["title"] == "Tic-Tac-Toe", f"Expected title='Tic-Tac-Toe', got {data['title']}"
    print("PASS: tictactoe-config endpoint returns valid configuration")


if __name__ == "__main__":
    try:
        test_existing_endpoints_not_broken()
        test_tictactoe_config_endpoint()
        print("ALL TESTS PASSED")
    except Exception as e:
        print(f"FAIL: {e}")
        sys.exit(1)

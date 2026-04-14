"""Acceptance tests for the agentic-sdlc demo API.

Tests cover:
- deploy-visit-confetti-config endpoint (all 17 fields with exact values)
- confetti-config regression (original 15 fields unchanged)
- /api/runs endpoint returns expected fields with created_at as ISO-8601
  and does NOT return a created_at_relative field (regression guard for
  the relative-timestamp feature which is handled client-side)
- typing-test-config endpoint returns expected fields
- typing-test-calculate endpoint: valid input, mistyped input, near-zero elapsed clamping
"""

import sys
import math
from datetime import datetime
from fastapi.testclient import TestClient
from server.app import app

client = TestClient(app)

# Expected values for the new deploy-visit-confetti-config endpoint
EXPECTED_DEPLOY_VISIT = {
    "enabled": True,
    "particle_count": 80,
    "duration_ms": 2500,
    "spread_deg": 120,
    "colors": ["#34d399", "#6366f1", "#fbbf24", "#ec4899", "#3b82f6", "#a78bfa"],
    "gravity": 0.6,
    "drift": 0.3,
    "size_range": [5, 12],
    "shapes": ["circle", "square", "star"],
    "origin_x": 0.5,
    "origin_y": 0.3,
    "trigger": "first-visit",
    "trigger_status": "deployed",
    "first_visit_only": True,
    "cooldown_session_key": "confetti_seen_run_{run_id}",
    "respect_reduced_motion": True,
    "target": "run-detail-page",
}

# Expected values for the existing confetti-config endpoint (regression check)
EXPECTED_ORIGINAL = {
    "enabled": True,
    "particle_count": 40,
    "duration_ms": 1500,
    "spread_px": 60,
    "colors": ["#34d399", "#6366f1", "#fbbf24", "#ec4899", "#3b82f6"],
    "gravity": 0.8,
    "drift": 0.5,
    "size_range": [4, 8],
    "shapes": ["circle", "square"],
    "trigger": "status-change",
    "trigger_from": "running",
    "trigger_to": "deployed",
    "respect_reduced_motion": True,
    "target": "run-card",
    "max_concurrent": 3,
}

# Fields every run object must contain in GET /api/runs
EXPECTED_RUN_FIELDS = {
    "id", "workflow", "status", "inputs", "created_at",
    "started_at", "completed_at", "error", "has_result",
    "duration_seconds", "total_tokens", "workflow_output", "cost_dollars",
}


def test_deploy_visit_confetti_config_returns_all_fields():
    """GET /api/deploy-visit-confetti-config returns 200 with all 17 fields matching exact values."""
    response = client.get("/api/deploy-visit-confetti-config")
    assert response.status_code == 200, f"Expected 200 but got {response.status_code}"
    data = response.json()
    # Verify every expected key-value pair
    for key, expected_value in EXPECTED_DEPLOY_VISIT.items():
        assert key in data, f"Missing field: {key}"
        assert data[key] == expected_value, (
            f"Field '{key}': expected {expected_value!r}, got {data[key]!r}"
        )
    # Verify no extra fields beyond the 17 expected
    assert set(data.keys()) == set(EXPECTED_DEPLOY_VISIT.keys()), (
        f"Unexpected fields: {set(data.keys()) - set(EXPECTED_DEPLOY_VISIT.keys())}"
    )
    # Specifically verify cooldown_session_key has literal curly braces (not interpolated)
    assert "{run_id}" in data["cooldown_session_key"], (
        "cooldown_session_key should contain literal {run_id} placeholder"
    )
    print("PASS: deploy-visit-confetti-config returns all 17 fields with correct values")


def test_existing_confetti_config_unchanged():
    """GET /api/confetti-config still returns 200 with its original 15 fields unchanged (regression)."""
    response = client.get("/api/confetti-config")
    assert response.status_code == 200, f"Expected 200 but got {response.status_code}"
    data = response.json()
    for key, expected_value in EXPECTED_ORIGINAL.items():
        assert key in data, f"Missing field in original endpoint: {key}"
        assert data[key] == expected_value, (
            f"Original endpoint field '{key}': expected {expected_value!r}, got {data[key]!r}"
        )
    assert set(data.keys()) == set(EXPECTED_ORIGINAL.keys()), (
        f"Original endpoint has unexpected fields: {set(data.keys()) - set(EXPECTED_ORIGINAL.keys())}"
    )
    # Verify the original model uses spread_px (not spread_deg)
    assert "spread_px" in data, "Original endpoint must use spread_px, not spread_deg"
    assert "spread_deg" not in data, "Original endpoint must NOT have spread_deg"
    print("PASS: existing confetti-config endpoint unchanged (no regression)")


def test_runs_endpoint_returns_expected_fields():
    """GET /api/runs returns 200 with runs containing all expected fields and created_at as ISO-8601.

    This is a regression guard: relative timestamps are formatted client-side
    by formatTimeAgo(run.created_at). The server must continue to return raw
    created_at as ISO-8601 and must NOT add a created_at_relative field.
    """
    response = client.get("/api/runs?limit=1")
    assert response.status_code == 200, f"Expected 200 but got {response.status_code}"
    data = response.json()

    # Response must have 'runs' key
    assert "runs" in data, "Response missing 'runs' key"
    assert "total" in data, "Response missing 'total' key"

    runs = data["runs"]
    assert isinstance(runs, list), f"'runs' should be a list, got {type(runs).__name__}"

    if len(runs) > 0:
        run = runs[0]

        # Verify all expected fields are present
        missing = EXPECTED_RUN_FIELDS - set(run.keys())
        assert not missing, f"Run is missing fields: {missing}"

        # Verify created_at is a valid ISO-8601 string
        created_at = run["created_at"]
        assert isinstance(created_at, str), (
            f"created_at should be a string, got {type(created_at).__name__}"
        )
        try:
            datetime.fromisoformat(created_at)
        except ValueError:
            raise AssertionError(
                f"created_at '{created_at}' is not a valid ISO-8601 datetime"
            )

        # Verify created_at_relative is NOT present — relative formatting
        # is handled client-side by formatTimeAgo(), not by the server
        assert "created_at_relative" not in run, (
            "Run should NOT contain 'created_at_relative' — "
            "relative timestamps are formatted client-side"
        )

    print("PASS: /api/runs returns expected fields with created_at as ISO-8601, no created_at_relative")


def test_typing_test_config_returns_expected_fields():
    """GET /api/typing-test-config returns 200 with title, sentences, time_limit_seconds, words_per_minute_label."""
    response = client.get("/api/typing-test-config")
    assert response.status_code == 200, f"Expected 200 but got {response.status_code}"
    data = response.json()

    assert "title" in data, "Missing field: title"
    assert isinstance(data["title"], str), f"title should be str, got {type(data['title']).__name__}"

    assert "sentences" in data, "Missing field: sentences"
    assert isinstance(data["sentences"], list), f"sentences should be list, got {type(data['sentences']).__name__}"
    assert len(data["sentences"]) >= 1, "sentences should have at least 1 entry"

    assert "time_limit_seconds" in data, "Missing field: time_limit_seconds"
    assert isinstance(data["time_limit_seconds"], int), f"time_limit_seconds should be int, got {type(data['time_limit_seconds']).__name__}"

    assert "words_per_minute_label" in data, "Missing field: words_per_minute_label"
    assert isinstance(data["words_per_minute_label"], str), f"words_per_minute_label should be str, got {type(data['words_per_minute_label']).__name__}"

    print("PASS: typing-test-config returns expected fields")


def test_typing_test_calculate_valid_input():
    """POST /api/typing-test-calculate with perfect input returns correct WPM and 100% accuracy."""
    response = client.post("/api/typing-test-calculate", json={
        "original": "hello world",
        "typed": "hello world",
        "elapsed_seconds": 5.0,
    })
    assert response.status_code == 200, f"Expected 200 but got {response.status_code}"
    data = response.json()

    assert "wpm" in data, "Missing field: wpm"
    assert data["wpm"] > 0, f"wpm should be > 0, got {data['wpm']}"

    assert "accuracy" in data, "Missing field: accuracy"
    assert data["accuracy"] == 100.0, f"accuracy should be 100.0, got {data['accuracy']}"

    assert "correct_chars" in data, "Missing field: correct_chars"
    assert data["correct_chars"] == 11, f"correct_chars should be 11, got {data['correct_chars']}"

    assert "total_chars" in data, "Missing field: total_chars"
    assert data["total_chars"] == 11, f"total_chars should be 11, got {data['total_chars']}"

    assert "elapsed_seconds" in data, "Missing field: elapsed_seconds"
    assert data["elapsed_seconds"] == 5.0, f"elapsed_seconds should be 5.0, got {data['elapsed_seconds']}"

    print("PASS: typing-test-calculate with valid input returns correct results")


def test_typing_test_calculate_mistyped_input():
    """POST /api/typing-test-calculate with mistyped input returns accuracy < 100."""
    response = client.post("/api/typing-test-calculate", json={
        "original": "hello world",
        "typed": "hxllo wxrld",
        "elapsed_seconds": 5.0,
    })
    assert response.status_code == 200, f"Expected 200 but got {response.status_code}"
    data = response.json()

    assert data["accuracy"] < 100.0, f"accuracy should be < 100 for mistyped input, got {data['accuracy']}"
    assert data["correct_chars"] < data["total_chars"], (
        f"correct_chars ({data['correct_chars']}) should be < total_chars ({data['total_chars']}) for mistyped input"
    )

    print("PASS: typing-test-calculate with mistyped input returns accuracy < 100")


def test_typing_test_calculate_near_zero_elapsed():
    """POST /api/typing-test-calculate with near-zero elapsed_seconds should clamp to 0.1, not error."""
    response = client.post("/api/typing-test-calculate", json={
        "original": "hello",
        "typed": "hello",
        "elapsed_seconds": 0.01,
    })
    assert response.status_code == 200, (
        f"Expected 200 (clamped) but got {response.status_code}; "
        "near-zero elapsed should be clamped to 0.1, not rejected"
    )
    data = response.json()

    assert data["elapsed_seconds"] == 0.1, (
        f"elapsed_seconds should be clamped to 0.1, got {data['elapsed_seconds']}"
    )
    assert math.isfinite(data["wpm"]), f"wpm should be a finite number, got {data['wpm']}"

    print("PASS: typing-test-calculate with near-zero elapsed clamps to 0.1")


if __name__ == "__main__":
    passed = 0
    failed = 0
    for test_fn in [
        test_deploy_visit_confetti_config_returns_all_fields,
        test_existing_confetti_config_unchanged,
        test_runs_endpoint_returns_expected_fields,
        test_typing_test_config_returns_expected_fields,
        test_typing_test_calculate_valid_input,
        test_typing_test_calculate_mistyped_input,
        test_typing_test_calculate_near_zero_elapsed,
    ]:
        try:
            test_fn()
            passed += 1
        except Exception as e:
            print(f"FAIL: {test_fn.__name__}: {e}")
            failed += 1
    print(f"\nResults: {passed} passed, {failed} failed out of {passed + failed}")
    if failed:
        sys.exit(1)
    print("ALL TESTS PASSED")

"""Acceptance tests for the agentic-sdlc demo API.

Tests cover:
- deploy-visit-confetti-config endpoint (all 17 fields with exact values)
- confetti-config regression (original 15 fields unchanged)
- /api/runs endpoint returns expected fields with created_at as ISO-8601
  and does NOT return a created_at_relative field (regression guard for
  the relative-timestamp feature which is handled client-side)
- typing-test-config endpoint returns expected fields
- typing-test-calculate endpoint: valid input, mistyped input, near-zero elapsed clamping
- color-picker-config endpoint returns hex_input_placeholder field
- color-picker-convert endpoint: valid hex conversion, invalid hex rejection
- pipeline-stage-tooltip-config endpoint returns 7 stages with correct names, descriptions, icons, and config
- greeting-config endpoint returns time-of-day greeting configuration with
  greetings, boundaries, emoji_map, text_color, and animation fields
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

# Expected greeting periods
EXPECTED_GREETING_PERIODS = {"morning", "afternoon", "evening", "night"}

# Expected boundary values for each period
EXPECTED_BOUNDARIES = {
    "morning": 5,
    "afternoon": 12,
    "evening": 17,
    "night": 21,
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


def test_color_picker_config_returns_expected_fields():
    """GET /api/color-picker-config returns 200 with all 6 fields including hex_input_placeholder."""
    response = client.get("/api/color-picker-config")
    assert response.status_code == 200, f"Expected 200 but got {response.status_code}"
    data = response.json()

    # Verify all 6 expected fields exist
    expected_fields = {"title", "default_color", "formats", "show_preview", "preset_colors", "hex_input_placeholder"}
    missing = expected_fields - set(data.keys())
    assert not missing, f"Missing fields: {missing}"

    # Verify types
    assert isinstance(data["title"], str), f"title should be str, got {type(data['title']).__name__}"
    assert isinstance(data["default_color"], str), f"default_color should be str, got {type(data['default_color']).__name__}"
    assert isinstance(data["formats"], list), f"formats should be list, got {type(data['formats']).__name__}"
    assert isinstance(data["show_preview"], bool), f"show_preview should be bool, got {type(data['show_preview']).__name__}"
    assert isinstance(data["preset_colors"], list), f"preset_colors should be list, got {type(data['preset_colors']).__name__}"
    assert isinstance(data["hex_input_placeholder"], str), f"hex_input_placeholder should be str, got {type(data['hex_input_placeholder']).__name__}"

    # Verify preset_colors has exactly 9 items
    assert len(data["preset_colors"]) == 9, f"preset_colors should have 9 items, got {len(data['preset_colors'])}"

    # Verify hex_input_placeholder value
    assert data["hex_input_placeholder"] == "#6366f1", (
        f"hex_input_placeholder should be '#6366f1', got {data['hex_input_placeholder']!r}"
    )

    print("PASS: color-picker-config returns all 6 fields including hex_input_placeholder")


def test_color_picker_convert_valid_hex():
    """POST /api/color-picker-convert with valid hex returns 200 with correct RGB, HSL, and hex."""
    response = client.post("/api/color-picker-convert", json={"hex_code": "#ff5733"})
    assert response.status_code == 200, f"Expected 200 but got {response.status_code}"
    data = response.json()

    # Verify hex is uppercased
    assert data["hex"] == "#FF5733", f"hex should be '#FF5733', got {data['hex']!r}"

    # Verify RGB components
    assert data["red"] == 255, f"red should be 255, got {data['red']}"
    assert data["green"] == 87, f"green should be 87, got {data['green']}"
    assert data["blue"] == 51, f"blue should be 51, got {data['blue']}"

    # Verify rgb string
    assert data["rgb"] == "rgb(255, 87, 51)", f"rgb should be 'rgb(255, 87, 51)', got {data['rgb']!r}"

    # Verify is_valid
    assert data["is_valid"] is True, f"is_valid should be True, got {data['is_valid']!r}"

    # Verify HSL values are present and numeric
    assert isinstance(data["hue"], int), f"hue should be int, got {type(data['hue']).__name__}"
    assert isinstance(data["saturation"], int), f"saturation should be int, got {type(data['saturation']).__name__}"
    assert isinstance(data["lightness"], int), f"lightness should be int, got {type(data['lightness']).__name__}"

    # Verify hsl string is present
    assert "hsl" in data, "Missing field: hsl"
    assert isinstance(data["hsl"], str), f"hsl should be str, got {type(data['hsl']).__name__}"

    print("PASS: color-picker-convert with valid hex returns correct results")


def test_color_picker_convert_invalid_hex():
    """POST /api/color-picker-convert with invalid hex returns 400 with descriptive error."""
    response = client.post("/api/color-picker-convert", json={"hex_code": "notacolor"})
    assert response.status_code == 400, f"Expected 400 but got {response.status_code}"
    data = response.json()

    assert "detail" in data, "Error response missing 'detail' field"
    assert "Invalid hex color code" in data["detail"], (
        f"detail should contain 'Invalid hex color code', got {data['detail']!r}"
    )

    print("PASS: color-picker-convert with invalid hex returns 400 with descriptive error")


EXPECTED_STAGE_NAMES = ["Validate", "Analyze", "Plan", "Build", "Review", "Push", "Verify"]


def test_pipeline_stage_tooltip_config():
    """GET /api/pipeline-stage-tooltip-config returns 200 with all config fields and exactly 7 stages."""
    response = client.get("/api/pipeline-stage-tooltip-config")
    assert response.status_code == 200, f"Expected 200 but got {response.status_code}"
    data = response.json()

    # Top-level boolean/config fields
    assert data["enabled"] is True, f"enabled should be True, got {data['enabled']!r}"
    assert data["show_delay_ms"] == 200, f"show_delay_ms should be 200, got {data['show_delay_ms']}"
    assert data["hide_delay_ms"] == 150, f"hide_delay_ms should be 150, got {data['hide_delay_ms']}"
    assert data["position"] == "top", f"position should be 'top', got {data['position']!r}"
    assert data["max_width_px"] == 220, f"max_width_px should be 220, got {data['max_width_px']}"
    assert data["bg_color"] == "var(--temper-surface)", f"bg_color mismatch: {data['bg_color']!r}"
    assert data["text_color"] == "var(--temper-text)", f"text_color mismatch: {data['text_color']!r}"
    assert data["border_radius_px"] == 8, f"border_radius_px should be 8, got {data['border_radius_px']}"
    assert data["font_size_px"] == 12, f"font_size_px should be 12, got {data['font_size_px']}"
    assert data["padding_px"] == 10, f"padding_px should be 10, got {data['padding_px']}"
    assert data["arrow_size_px"] == 6, f"arrow_size_px should be 6, got {data['arrow_size_px']}"
    assert data["respect_reduced_motion"] is True, f"respect_reduced_motion should be True, got {data['respect_reduced_motion']!r}"
    assert data["target"] == "pipeline-stage", f"target should be 'pipeline-stage', got {data['target']!r}"

    # Stages: exactly 7 in the correct order
    stages = data["stages"]
    assert isinstance(stages, list), f"stages should be a list, got {type(stages).__name__}"
    assert len(stages) == 7, f"Expected 7 stages, got {len(stages)}"

    actual_names = [s["name"] for s in stages]
    assert actual_names == EXPECTED_STAGE_NAMES, (
        f"Stage names mismatch: expected {EXPECTED_STAGE_NAMES}, got {actual_names}"
    )

    # Each stage must have non-empty description and icon
    for stage in stages:
        assert isinstance(stage["description"], str) and len(stage["description"]) > 0, (
            f"Stage '{stage['name']}' should have a non-empty description"
        )
        assert isinstance(stage["icon"], str) and len(stage["icon"]) > 0, (
            f"Stage '{stage['name']}' should have a non-empty icon"
        )

    print("PASS: pipeline-stage-tooltip-config returns all fields with 7 correct stages")


def test_pipeline_glow_config_still_works():
    """GET /api/pipeline-glow-config still returns 200 (regression check for nearest neighbor endpoint)."""
    response = client.get("/api/pipeline-glow-config")
    assert response.status_code == 200, f"Expected 200 but got {response.status_code}"
    data = response.json()
    assert "enabled" in data, "pipeline-glow-config response missing 'enabled' field"
    print("PASS: pipeline-glow-config still returns 200 (regression)")


def test_greeting_config_returns_all_fields():
    """GET /api/greeting-config returns 200 with enabled, greetings, boundaries, emoji_map, text_color, animation."""
    response = client.get("/api/greeting-config")
    assert response.status_code == 200, f"Expected 200 but got {response.status_code}"
    data = response.json()

    # Verify enabled is a boolean set to True
    assert "enabled" in data, "Missing field: enabled"
    assert isinstance(data["enabled"], bool), f"enabled should be bool, got {type(data['enabled']).__name__}"
    assert data["enabled"] is True, f"enabled should be True, got {data['enabled']!r}"

    # Verify greetings is a dict with exactly 4 keys (morning, afternoon, evening, night)
    assert "greetings" in data, "Missing field: greetings"
    assert isinstance(data["greetings"], dict), f"greetings should be dict, got {type(data['greetings']).__name__}"
    assert set(data["greetings"].keys()) == EXPECTED_GREETING_PERIODS, (
        f"greetings keys should be {EXPECTED_GREETING_PERIODS}, got {set(data['greetings'].keys())}"
    )
    for period in EXPECTED_GREETING_PERIODS:
        assert isinstance(data["greetings"][period], str), (
            f"greetings['{period}'] should be str, got {type(data['greetings'][period]).__name__}"
        )
        assert len(data["greetings"][period]) > 0, f"greetings['{period}'] should be non-empty"

    # Verify boundaries is a dict with exactly 4 keys and correct integer values
    assert "boundaries" in data, "Missing field: boundaries"
    assert isinstance(data["boundaries"], dict), f"boundaries should be dict, got {type(data['boundaries']).__name__}"
    assert set(data["boundaries"].keys()) == EXPECTED_GREETING_PERIODS, (
        f"boundaries keys should be {EXPECTED_GREETING_PERIODS}, got {set(data['boundaries'].keys())}"
    )
    for period, expected_hour in EXPECTED_BOUNDARIES.items():
        assert data["boundaries"][period] == expected_hour, (
            f"boundaries['{period}'] should be {expected_hour}, got {data['boundaries'][period]}"
        )

    # Verify emoji_map is a dict with exactly 4 keys, each a non-empty string
    assert "emoji_map" in data, "Missing field: emoji_map"
    assert isinstance(data["emoji_map"], dict), f"emoji_map should be dict, got {type(data['emoji_map']).__name__}"
    assert set(data["emoji_map"].keys()) == EXPECTED_GREETING_PERIODS, (
        f"emoji_map keys should be {EXPECTED_GREETING_PERIODS}, got {set(data['emoji_map'].keys())}"
    )
    for period in EXPECTED_GREETING_PERIODS:
        assert isinstance(data["emoji_map"][period], str), (
            f"emoji_map['{period}'] should be str, got {type(data['emoji_map'][period]).__name__}"
        )
        assert len(data["emoji_map"][period]) > 0, f"emoji_map['{period}'] should be non-empty"

    # Verify text_color is a string
    assert "text_color" in data, "Missing field: text_color"
    assert isinstance(data["text_color"], str), f"text_color should be str, got {type(data['text_color']).__name__}"
    assert len(data["text_color"]) > 0, "text_color should be non-empty"

    # Verify animation is a string
    assert "animation" in data, "Missing field: animation"
    assert isinstance(data["animation"], str), f"animation should be str, got {type(data['animation']).__name__}"
    assert len(data["animation"]) > 0, "animation should be non-empty"

    # Verify exactly 6 top-level keys (no extras)
    expected_keys = {"enabled", "greetings", "boundaries", "emoji_map", "text_color", "animation"}
    assert set(data.keys()) == expected_keys, (
        f"Expected keys {expected_keys}, got {set(data.keys())}. "
        f"Extra: {set(data.keys()) - expected_keys}, Missing: {expected_keys - set(data.keys())}"
    )

    print("PASS: greeting-config returns all fields with correct types and values")


def test_greeting_config_regression_health_still_works():
    """GET /api/health still returns 200 after adding greeting-config (regression)."""
    response = client.get("/api/health")
    assert response.status_code == 200, f"Expected 200 but got {response.status_code}"
    data = response.json()
    assert data["status"] == "ok", f"health status should be 'ok', got {data['status']!r}"
    print("PASS: /api/health still returns 200 (regression)")


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
        test_color_picker_config_returns_expected_fields,
        test_color_picker_convert_valid_hex,
        test_color_picker_convert_invalid_hex,
        test_pipeline_stage_tooltip_config,
        test_pipeline_glow_config_still_works,
        test_greeting_config_returns_all_fields,
        test_greeting_config_regression_health_still_works,
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

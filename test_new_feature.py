"""
Acceptance tests for: add smooth scroll animation params to back-to-top config endpoint.

Tests verify:
  - back-to-top config includes new smooth scroll fields (scroll_duration_ms, scroll_easing, respect_reduced_motion)
  - existing back-to-top config fields remain unchanged (regression)
  - other endpoints unaffected (health, parallax-config, typewriter-config)

Also includes prior regression tests for homepage section ordering.
"""
import sys
import re
from pathlib import Path
from fastapi.testclient import TestClient
from server.app import app

client = TestClient(app)

HOMEPAGE_PATH = Path(__file__).parent / "frontend" / "src" / "pages" / "HomePage.tsx"


# ── Backend regression tests (ensure APIs powering both sections still work) ──

def test_community_creations_endpoint_still_works():
    """Regression: community-creations-config endpoint returns expected shape."""
    response = client.get("/api/community-creations-config")
    assert response.status_code == 200, f"Expected 200, got {response.status_code}"
    data = response.json()
    assert "title" in data, "Missing 'title' in response"
    assert "creations" in data, "Missing 'creations' in response"
    assert len(data["creations"]) > 0, "Expected at least one community creation"
    for creation in data["creations"]:
        assert "name" in creation, "Creation missing 'name'"
        assert "path" in creation, "Creation missing 'path'"
        assert creation["path"].startswith("/"), f"Path should start with /: {creation['path']}"
    print("PASS: community creations endpoint still works")


def test_runs_endpoint_still_works():
    """Regression: runs endpoint returns expected shape."""
    response = client.get("/api/runs")
    assert response.status_code == 200, f"Expected 200, got {response.status_code}"
    data = response.json()
    assert "runs" in data, "Missing 'runs' in response"
    assert isinstance(data["runs"], list), "'runs' should be a list"
    print("PASS: runs endpoint still works")


def test_back_to_top_smooth_scroll_fields():
    """Verify back-to-top config includes smooth scroll animation parameters."""
    response = client.get("/api/back-to-top-config")
    assert response.status_code == 200, f"Expected 200, got {response.status_code}"
    data = response.json()
    assert data["scroll_behavior"] == "smooth", f"Expected scroll_behavior 'smooth', got {data['scroll_behavior']}"
    assert data["scroll_duration_ms"] == 600, f"Expected scroll_duration_ms 600, got {data.get('scroll_duration_ms')}"
    assert data["scroll_easing"] == "cubic-bezier(0.25, 0.1, 0.25, 1)", f"Expected cubic-bezier easing, got {data.get('scroll_easing')}"
    assert data["respect_reduced_motion"] is True, f"Expected respect_reduced_motion True, got {data.get('respect_reduced_motion')}"
    print("PASS: back-to-top config includes smooth scroll animation fields")


def test_back_to_top_existing_fields_unchanged():
    """Regression: existing back-to-top config fields are still present and unchanged."""
    response = client.get("/api/back-to-top-config")
    assert response.status_code == 200, f"Expected 200, got {response.status_code}"
    data = response.json()
    assert data["enabled"] is True, f"Expected enabled True, got {data.get('enabled')}"
    assert data["scroll_threshold_px"] == 400, f"Expected scroll_threshold_px 400, got {data.get('scroll_threshold_px')}"
    assert data["position_right_px"] == 32, f"Expected position_right_px 32, got {data.get('position_right_px')}"
    assert data["position_bottom_px"] == 32, f"Expected position_bottom_px 32, got {data.get('position_bottom_px')}"
    assert data["size_px"] == 44, f"Expected size_px 44, got {data.get('size_px')}"
    assert data["bg_color"] == "#6366f1", f"Expected bg_color '#6366f1', got {data.get('bg_color')}"
    assert data["hover_bg_color"] == "#4f46e5", f"Expected hover_bg_color '#4f46e5', got {data.get('hover_bg_color')}"
    assert data["icon_color"] == "#ffffff", f"Expected icon_color '#ffffff', got {data.get('icon_color')}"
    assert data["border_radius"] == "50%", f"Expected border_radius '50%', got {data.get('border_radius')}"
    assert data["transition_ms"] == 200, f"Expected transition_ms 200, got {data.get('transition_ms')}"
    print("PASS: existing back-to-top config fields unchanged")


def test_health_endpoint():
    """Regression: health endpoint still returns ok."""
    response = client.get("/api/health")
    assert response.status_code == 200, f"Expected 200, got {response.status_code}"
    data = response.json()
    assert data["status"] == "ok", f"Expected status 'ok', got {data.get('status')}"
    print("PASS: health endpoint still works")


def test_parallax_config_unaffected():
    """Regression: parallax-config endpoint returns unchanged shape."""
    response = client.get("/api/parallax-config")
    assert response.status_code == 200, f"Expected 200, got {response.status_code}"
    data = response.json()
    assert "enabled" in data, "Missing 'enabled' in parallax config"
    assert "speed_factor" in data, "Missing 'speed_factor' in parallax config"
    assert "max_offset_px" in data, "Missing 'max_offset_px' in parallax config"
    print("PASS: parallax config unaffected")


def test_typewriter_config_unaffected():
    """Regression: typewriter-config endpoint returns unchanged shape."""
    response = client.get("/api/typewriter-config")
    assert response.status_code == 200, f"Expected 200, got {response.status_code}"
    data = response.json()
    assert "enabled" in data, "Missing 'enabled' in typewriter config"
    assert "lines" in data, "Missing 'lines' in typewriter config"
    assert "speed_ms" in data, "Missing 'speed_ms' in typewriter config"
    print("PASS: typewriter config unaffected")


# ── Frontend source-level tests (verify the HomePage.tsx changes) ──

def test_community_creations_appears_before_recent_changes():
    """Community Creations section must render ABOVE Recent Changes in the JSX."""
    source = HOMEPAGE_PATH.read_text()

    cc_match = re.search(r'/\*\s*──\s*Community Creations', source)
    rc_match = re.search(r'/\*\s*──\s*Recent changes', source)

    assert cc_match is not None, "Could not find Community Creations section comment"
    assert rc_match is not None, "Could not find Recent Changes section comment"

    cc_pos = cc_match.start()
    rc_pos = rc_match.start()

    assert cc_pos < rc_pos, (
        f"Community Creations (pos {cc_pos}) must appear BEFORE "
        f"Recent Changes (pos {rc_pos}) in the source. "
        f"Currently Community Creations comes after Recent Changes."
    )
    print("PASS: community creations appears before recent changes")


def test_empty_state_copy_updated():
    """Empty state message should say 'to get started!' not 'above!'."""
    source = HOMEPAGE_PATH.read_text()

    assert "Submit a suggestion to get started!" in source, (
        "Expected empty state text 'Submit a suggestion to get started!' not found. "
        "The old text 'Submit a suggestion above!' should be replaced."
    )
    assert "Submit a suggestion above!" not in source, (
        "Stale empty state text 'Submit a suggestion above!' still present in source."
    )
    print("PASS: empty state copy updated")


def test_community_creations_border_removed():
    """Community Creations inner div should NOT have border-t after the move."""
    source = HOMEPAGE_PATH.read_text()

    # Find the Community Creations section
    cc_match = re.search(r'/\*\s*──\s*Community Creations', source)
    assert cc_match is not None, "Could not find Community Creations section comment"

    # Look at the next ~400 chars after the comment for the inner div
    snippet = source[cc_match.start():cc_match.start() + 400]

    # The inner div should NOT have border-t styling anymore
    assert 'border-t border-[var(--temper-border)] pt-10' not in snippet, (
        "Community Creations inner div still has 'border-t border-[var(--temper-border)] pt-10'. "
        "After moving above Recent Changes, this border should be removed."
    )
    print("PASS: community creations border-t removed")


def test_recent_changes_has_border_separator():
    """Recent Changes section should have a border-t separator after Community Creations moves above it."""
    source = HOMEPAGE_PATH.read_text()

    # Find the Recent Changes section
    rc_match = re.search(r'/\*\s*──\s*Recent changes', source)
    assert rc_match is not None, "Could not find Recent Changes section comment"

    # Look at the next ~300 chars for a border-t class
    snippet = source[rc_match.start():rc_match.start() + 300]

    assert 'border-t' in snippet, (
        "Recent Changes section should have a 'border-t' class for visual separation "
        "from Community Creations above it."
    )
    print("PASS: recent changes has border separator")


if __name__ == "__main__":
    tests = [
        test_community_creations_endpoint_still_works,
        test_runs_endpoint_still_works,
        test_back_to_top_smooth_scroll_fields,
        test_back_to_top_existing_fields_unchanged,
        test_health_endpoint,
        test_parallax_config_unaffected,
        test_typewriter_config_unaffected,
        test_community_creations_appears_before_recent_changes,
        test_empty_state_copy_updated,
        test_community_creations_border_removed,
        test_recent_changes_has_border_separator,
    ]
    passed = 0
    failed = 0
    for test in tests:
        try:
            test()
            passed += 1
        except Exception as e:
            print(f"FAIL: {test.__name__}: {e}")
            failed += 1
    print(f"\nResults: {passed} passed, {failed} failed out of {len(tests)} tests")
    if failed > 0:
        sys.exit(1)
    else:
        print("ALL TESTS PASSED")

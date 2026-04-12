"""
Acceptance tests for: reorder homepage to show Community Creations above Recent Changes.

This is a frontend-only change. Backend regression tests verify the APIs powering
both sections still work. Source-level tests verify the HomePage.tsx changes:
  - Community Creations section appears BEFORE Recent Changes
  - Border styling updated (no border-t on Community Creations inner div)
  - Recent Changes section gets a border-t separator
  - Empty-state copy says "to get started!" not "above!"
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

"""Acceptance tests for improved shimmer loading skeleton cards.

The feature changes the skeleton loading state in HomePage.tsx to:
1. Show 8 skeleton cards instead of 4 (matching default showCount)
2. Match real run card structure: left border, icon dot, two title lines, timestamp
3. Add accessibility attributes (role='status', aria-busy='true')
4. Remove fixed h-24 height constraint

These tests verify the source file contains the expected patterns and
that backend safeguard endpoints remain unchanged.
"""

import sys
from pathlib import Path
from fastapi.testclient import TestClient
from server.app import app

client = TestClient(app)

HOMEPAGE_PATH = Path(__file__).parent / "frontend" / "src" / "pages" / "HomePage.tsx"


def test_skeleton_count_is_eight():
    """Skeleton loading should render 8 cards, not 4, to match default showCount."""
    source = HOMEPAGE_PATH.read_text()
    # The old code uses [1, 2, 3, 4].map — new code should use length: 8
    assert "length: 8" in source, (
        "Expected skeleton to render 8 cards (Array.from({length: 8})), "
        "but did not find 'length: 8' in HomePage.tsx"
    )
    # Old 4-card array should be gone
    assert "[1, 2, 3, 4]" not in source, (
        "Old 4-card skeleton array [1, 2, 3, 4] should be removed"
    )
    print("PASS: skeleton count is 8")


def test_skeleton_accessibility_attributes():
    """Skeleton grid should have role='status' and aria-busy for screen readers."""
    source = HOMEPAGE_PATH.read_text()
    assert 'role="status"' in source or "role='status'" in source, (
        "Skeleton grid must have role='status' attribute"
    )
    # Check for aria-busy on the skeleton loading grid
    loading_section_start = source.find("{loading ? (")
    assert loading_section_start != -1, "Could not find loading section in HomePage.tsx"
    loading_section_end = source.find(") : filteredRuns", loading_section_start)
    assert loading_section_end != -1, "Could not find end of loading section"
    skeleton_section = source[loading_section_start:loading_section_end]
    assert "aria-busy" in skeleton_section, (
        "Skeleton grid must have aria-busy attribute"
    )
    # Check for visually-hidden loading text
    assert "sr-only" in skeleton_section and "Loading" in skeleton_section, (
        "Expected a visually-hidden <span className='sr-only'> with loading text in skeleton section"
    )
    print("PASS: skeleton accessibility attributes present")


def test_skeleton_card_structure_matches_run_cards():
    """Skeleton cards should mirror real run card structure with left border, icon dot, title lines."""
    source = HOMEPAGE_PATH.read_text()
    # Find the skeleton loading section specifically
    loading_section_start = source.find("{loading ? (")
    assert loading_section_start != -1, "Could not find loading section in HomePage.tsx"
    loading_section_end = source.find(") : filteredRuns", loading_section_start)
    assert loading_section_end != -1, "Could not find end of loading section"
    skeleton_section = source[loading_section_start:loading_section_end]
    # Left border accent (3px colored left border)
    assert "border-l-[3px]" in skeleton_section, (
        "Skeleton cards should have a 3px left border accent like real run cards"
    )
    # Icon dot placeholder (rounded-full circle)
    assert "rounded-full" in skeleton_section, (
        "Skeleton cards should have a rounded-full icon dot placeholder"
    )
    # Should NOT have fixed h-24 height on skeleton cards
    assert "h-24" not in skeleton_section, (
        "Skeleton cards should not have fixed h-24 height — height should be determined by content"
    )
    print("PASS: skeleton card structure matches run cards")


def test_skeleton_css_unchanged():
    """The existing .skeleton CSS class shimmer animation must not be modified."""
    css_path = Path(__file__).parent / "frontend" / "src" / "index.css"
    css = css_path.read_text()
    assert ".skeleton {" in css or ".skeleton{" in css, (
        "The .skeleton CSS class must still exist in index.css"
    )
    assert "shimmer" in css, (
        "The shimmer animation must still be referenced in the skeleton CSS"
    )
    assert "background-size: 200% 100%" in css, (
        "The skeleton shimmer background-size must remain 200% 100%"
    )
    print("PASS: skeleton CSS unchanged")


def test_backend_health_endpoint():
    """Safeguard: /api/health must still return 200."""
    response = client.get("/api/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    print("PASS: /api/health returns 200")


def test_backend_runs_endpoint():
    """Safeguard: /api/runs must still return expected structure."""
    response = client.get("/api/runs")
    assert response.status_code == 200
    data = response.json()
    assert "runs" in data, "Response must contain 'runs' key"
    assert "total" in data, "Response must contain 'total' key"
    assert isinstance(data["runs"], list), "'runs' must be a list"
    print("PASS: /api/runs returns expected structure")


if __name__ == "__main__":
    tests = [
        test_skeleton_count_is_eight,
        test_skeleton_accessibility_attributes,
        test_skeleton_card_structure_matches_run_cards,
        test_skeleton_css_unchanged,
        test_backend_health_endpoint,
        test_backend_runs_endpoint,
    ]
    failed = []
    for t in tests:
        try:
            t()
        except Exception as e:
            print(f"FAIL: {t.__name__}: {e}")
            failed.append(t.__name__)
    if failed:
        print(f"\n{len(failed)} test(s) FAILED: {', '.join(failed)}")
        sys.exit(1)
    else:
        print("\nALL TESTS PASSED")

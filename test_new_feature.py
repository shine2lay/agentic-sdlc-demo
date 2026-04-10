"""
Acceptance tests for: animated checkmark on successful suggestion submission.

Tests verify:
1. POST /api/suggest returns a 'message' field (backend contract for banner text)
2. The CSS file contains the new checkmark animation classes
   (animate-checkmark-circle, animate-checkmark-draw) and reduced-motion overrides
3. HomePage.tsx has AnimatedCheckmark component, role="status" on the banner,
   flex layout for icon alignment, and the stale-state fix (clearing submitMessage)
"""

import sys
import os

# ---------------------------------------------------------------------------
# Test 1 – Backend: /api/suggest returns a message field
# ---------------------------------------------------------------------------
from fastapi.testclient import TestClient
from server.app import app

client = TestClient(app)


def test_suggest_returns_message_field():
    """POST /api/suggest should return status, run_id, and message."""
    response = client.post("/api/suggest", json={"suggestion": "Add dark mode toggle"})
    assert response.status_code == 200, f"Expected 200, got {response.status_code}"
    data = response.json()
    assert "message" in data, f"Response missing 'message' field: {data}"
    assert "status" in data, f"Response missing 'status' field: {data}"
    assert data["status"] == "submitted", f"Expected status 'submitted', got {data['status']}"
    print("PASS: suggest endpoint returns message field")


# ---------------------------------------------------------------------------
# Test 2 – Frontend: CSS contains checkmark animation classes
# ---------------------------------------------------------------------------
CSS_PATH = os.path.join(os.path.dirname(__file__), "frontend", "src", "index.css")


def test_css_has_checkmark_animations():
    """index.css must define animate-checkmark-circle and animate-checkmark-draw."""
    with open(CSS_PATH) as f:
        css = f.read()

    assert "animate-checkmark-circle" in css, (
        "CSS missing .animate-checkmark-circle class"
    )
    assert "animate-checkmark-draw" in css, (
        "CSS missing .animate-checkmark-draw class"
    )
    assert "@keyframes checkmark-circle" in css, (
        "CSS missing @keyframes checkmark-circle"
    )
    assert "@keyframes checkmark-draw" in css, (
        "CSS missing @keyframes checkmark-draw"
    )
    print("PASS: CSS contains checkmark animation classes")


# ---------------------------------------------------------------------------
# Test 3 – Frontend: HomePage.tsx has AnimatedCheckmark + banner fixes
# ---------------------------------------------------------------------------
TSX_PATH = os.path.join(os.path.dirname(__file__), "frontend", "src", "pages", "HomePage.tsx")


def test_homepage_has_animated_checkmark():
    """HomePage.tsx must define AnimatedCheckmark and use it in the success banner."""
    with open(TSX_PATH) as f:
        tsx = f.read()

    # AnimatedCheckmark component must exist
    assert "AnimatedCheckmark" in tsx, (
        "HomePage.tsx missing AnimatedCheckmark component"
    )

    # The success banner must have role="status" for accessibility
    assert 'role="status"' in tsx, (
        "Success banner missing role=\"status\" attribute"
    )

    # The banner must use flex layout with gap for icon alignment
    assert "flex items-center gap-2" in tsx, (
        "Success banner missing 'flex items-center gap-2' layout classes"
    )

    # Stale-state fix: setTimeout must clear submitMessage too
    assert "setSubmitMessage('')" in tsx or 'setSubmitMessage("")' in tsx, (
        "setTimeout callbacks must clear submitMessage to prevent stale text"
    )

    print("PASS: HomePage.tsx has AnimatedCheckmark and banner fixes")


# ---------------------------------------------------------------------------
# Runner
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    passed = 0
    failed = 0
    for test_fn in [
        test_suggest_returns_message_field,
        test_css_has_checkmark_animations,
        test_homepage_has_animated_checkmark,
    ]:
        try:
            test_fn()
            passed += 1
        except Exception as e:
            print(f"FAIL: {test_fn.__name__}: {e}")
            failed += 1

    print(f"\n{passed} passed, {failed} failed out of {passed + failed} tests")
    if failed:
        sys.exit(1)
    print("ALL TESTS PASSED")

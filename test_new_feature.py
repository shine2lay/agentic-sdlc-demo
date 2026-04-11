"""Acceptance tests for: smooth number animation on filter tab counts.

The HomePage filter tabs (All, Shipped, Rejected, Failed) should display counts
that animate smoothly when values change. This requires:
1. A useAnimatedNumber hook in HomePage.tsx
2. An AnimatedTab component that uses the hook for each tab

These tests verify the frontend source contains the required hook and component.
They should FAIL before implementation and PASS after.
"""

import sys
import os
import re

HOMEPAGE_PATH = os.path.join(
    os.path.dirname(__file__), "frontend", "src", "pages", "HomePage.tsx",
)


def _read(path: str) -> str:
    with open(path) as f:
        return f.read()


def test_use_animated_number_hook_exists():
    """HomePage.tsx must define a useAnimatedNumber hook with requestAnimationFrame."""
    tsx = _read(HOMEPAGE_PATH)
    assert "function useAnimatedNumber" in tsx or "const useAnimatedNumber" in tsx, (
        "HomePage.tsx does not define a useAnimatedNumber hook"
    )
    # The hook must use rAF for frame-based animation
    assert "requestAnimationFrame" in tsx, (
        "useAnimatedNumber must use requestAnimationFrame for smooth animation"
    )
    assert "cancelAnimationFrame" in tsx, (
        "useAnimatedNumber must cancel animation frames on cleanup"
    )
    print("PASS: useAnimatedNumber hook exists with requestAnimationFrame")


def test_animated_tab_component_exists():
    """HomePage.tsx must define an AnimatedTab component that calls useAnimatedNumber."""
    tsx = _read(HOMEPAGE_PATH)
    assert "function AnimatedTab" in tsx or "const AnimatedTab" in tsx, (
        "HomePage.tsx does not define an AnimatedTab component"
    )
    # AnimatedTab must invoke the hook internally (hooks can't be called in .map())
    assert "useAnimatedNumber" in tsx, (
        "AnimatedTab must call useAnimatedNumber for count animation"
    )
    print("PASS: AnimatedTab component exists and uses useAnimatedNumber")


def test_reduced_motion_in_animation_hook():
    """The useAnimatedNumber hook itself must check prefers-reduced-motion."""
    tsx = _read(HOMEPAGE_PATH)
    # Find the useAnimatedNumber function body and verify it contains the check.
    # We look for the hook definition and then check that prefers-reduced-motion
    # appears near requestAnimationFrame (both inside the hook, not elsewhere).
    hook_match = re.search(
        r"function useAnimatedNumber.*?\n\}",
        tsx,
        re.DOTALL,
    )
    assert hook_match is not None, (
        "Could not find useAnimatedNumber function definition"
    )
    hook_body = hook_match.group(0)
    assert "prefers-reduced-motion" in hook_body, (
        "useAnimatedNumber must check prefers-reduced-motion media query"
    )
    print("PASS: useAnimatedNumber respects prefers-reduced-motion")


def test_filter_tabs_use_animated_tab():
    """The filter tab rendering must use AnimatedTab instead of inline buttons."""
    tsx = _read(HOMEPAGE_PATH)
    assert "<AnimatedTab" in tsx, (
        "Filter tabs must render <AnimatedTab> components instead of inline buttons"
    )
    print("PASS: filter tabs use AnimatedTab component")


def test_easing_in_animation_hook():
    """The useAnimatedNumber hook should use an easing function, not linear lerp."""
    tsx = _read(HOMEPAGE_PATH)
    hook_match = re.search(
        r"function useAnimatedNumber.*?\n\}",
        tsx,
        re.DOTALL,
    )
    assert hook_match is not None, (
        "Could not find useAnimatedNumber function definition"
    )
    hook_body = hook_match.group(0)
    # The plan uses cubic ease-out: 1 - (1 - t) ** 3
    has_easing = (
        "eased" in hook_body
        or "** 3" in hook_body
        or "**3" in hook_body
        or "Math.pow" in hook_body
    )
    assert has_easing, (
        "useAnimatedNumber should apply an easing function for smooth deceleration"
    )
    print("PASS: useAnimatedNumber applies easing function")


# ── Runner ──────────────────────────────────────────────────────────────────

ALL_TESTS = [
    test_use_animated_number_hook_exists,
    test_animated_tab_component_exists,
    test_reduced_motion_in_animation_hook,
    test_filter_tabs_use_animated_tab,
    test_easing_in_animation_hook,
]

if __name__ == "__main__":
    passed = 0
    failed = 0
    for test_fn in ALL_TESTS:
        try:
            test_fn()
            passed += 1
        except AssertionError as e:
            print(f"FAIL: {test_fn.__name__}: {e}")
            failed += 1
        except Exception as e:
            print(f"FAIL: {test_fn.__name__}: {e}")
            failed += 1

    print(f"\nResults: {passed} passed, {failed} failed out of {len(ALL_TESTS)} tests")
    if failed > 0:
        sys.exit(1)
    else:
        print("ALL TESTS PASSED")

"""
Acceptance tests for: pulsing glow animation on active pipeline stage circles.

Verifies that:
1. index.css contains the pulse-glow @keyframes and .animate-pulse-glow class
2. index.css contains a prefers-reduced-motion rule for animate-pulse-glow
3. HomePage.tsx uses animate-pulse-glow on the active circle instead of static shadow
4. HomePage.tsx uses scoped transition (not transition-all) on the circle div
"""

import sys
import os
import re

CSS_PATH = os.path.join(os.path.dirname(__file__), "frontend", "src", "index.css")
TSX_PATH = os.path.join(os.path.dirname(__file__), "frontend", "src", "pages", "HomePage.tsx")


def read_file(path: str) -> str:
    with open(path, "r") as f:
        return f.read()


def test_css_has_pulse_glow_keyframes():
    """index.css must define @keyframes pulse-glow with box-shadow steps."""
    css = read_file(CSS_PATH)
    assert "@keyframes pulse-glow" in css, (
        "@keyframes pulse-glow not found in index.css"
    )
    # Should contain box-shadow declarations inside the keyframe
    match = re.search(
        r"@keyframes pulse-glow\s*\{([\s\S]*?)\n\}", css
    )
    assert match, "Could not parse @keyframes pulse-glow block"
    block = match.group(1)
    assert "box-shadow" in block, (
        "pulse-glow keyframe must animate box-shadow"
    )
    print("PASS: CSS has pulse-glow keyframes with box-shadow")


def test_css_has_animate_pulse_glow_class():
    """index.css must define .animate-pulse-glow utility class."""
    css = read_file(CSS_PATH)
    assert ".animate-pulse-glow" in css, (
        ".animate-pulse-glow class not found in index.css"
    )
    # The class should reference the pulse-glow animation
    match = re.search(
        r"\.animate-pulse-glow\s*\{([\s\S]*?)\}", css
    )
    assert match, "Could not parse .animate-pulse-glow block"
    block = match.group(1)
    assert "animation" in block and "pulse-glow" in block, (
        ".animate-pulse-glow must set animation to pulse-glow"
    )
    print("PASS: CSS has .animate-pulse-glow utility class")


def test_css_has_reduced_motion_rule():
    """index.css must include prefers-reduced-motion for pulse-glow accessibility."""
    css = read_file(CSS_PATH)
    assert "prefers-reduced-motion" in css, (
        "prefers-reduced-motion media query not found in index.css"
    )
    # Check that the reduced-motion block references animate-pulse-glow
    reduced_motion_match = re.search(
        r"@media\s*\(prefers-reduced-motion:\s*reduce\)\s*\{([\s\S]*?)\n\}", css
    )
    assert reduced_motion_match, "Could not parse prefers-reduced-motion block"
    block = reduced_motion_match.group(1)
    assert "animate-pulse-glow" in block, (
        "prefers-reduced-motion block must reference .animate-pulse-glow"
    )
    print("PASS: CSS has prefers-reduced-motion rule for pulse-glow")


def test_homepage_uses_animate_pulse_glow():
    """HomePage.tsx active circle must use animate-pulse-glow class."""
    tsx = read_file(TSX_PATH)
    assert "animate-pulse-glow" in tsx, (
        "animate-pulse-glow class not used in HomePage.tsx"
    )
    # Verify it's near scale-110 (the active circle branch)
    lines = tsx.split("\n")
    found = False
    for line in lines:
        if "scale-110" in line and "animate-pulse-glow" in line:
            found = True
            break
    if not found:
        scale_pos = tsx.find("scale-110")
        glow_pos = tsx.find("animate-pulse-glow")
        if scale_pos >= 0 and glow_pos >= 0 and abs(scale_pos - glow_pos) < 300:
            found = True
    assert found, (
        "animate-pulse-glow must appear near scale-110 in the active circle branch"
    )
    print("PASS: HomePage.tsx uses animate-pulse-glow on active circle")


def test_homepage_no_transition_all_on_circle():
    """HomePage.tsx circle div must NOT use transition-all (to avoid fighting keyframes)."""
    tsx = read_file(TSX_PATH)
    match = re.search(
        r"className=\{`w-10 h-10 rounded-full[^`]*`\}", tsx, re.DOTALL
    )
    assert match, "Could not find the circle div className in HomePage.tsx"
    circle_class = match.group(0)
    assert "transition-all" not in circle_class, (
        "Circle div must not use transition-all -- use scoped transition instead "
        "(e.g. transition-[transform,colors,opacity])"
    )
    assert "transition-[" in circle_class or "transition-transform" in circle_class, (
        "Circle div must use a scoped transition (e.g. transition-[transform,colors,opacity])"
    )
    print("PASS: HomePage.tsx circle div uses scoped transition, not transition-all")


def test_homepage_no_static_shadow_on_active():
    """HomePage.tsx active circle must NOT have static shadow-lg (replaced by glow)."""
    tsx = read_file(TSX_PATH)
    match = re.search(
        r"className=\{`w-10 h-10 rounded-full[^`]*`\}", tsx, re.DOTALL
    )
    assert match, "Could not find the circle div className in HomePage.tsx"
    circle_class = match.group(0)
    assert "shadow-lg" not in circle_class, (
        "Active circle must not have shadow-lg -- replaced by animate-pulse-glow"
    )
    print("PASS: HomePage.tsx active circle has no static shadow-lg")


if __name__ == "__main__":
    tests = [
        test_css_has_pulse_glow_keyframes,
        test_css_has_animate_pulse_glow_class,
        test_css_has_reduced_motion_rule,
        test_homepage_uses_animate_pulse_glow,
        test_homepage_no_transition_all_on_circle,
        test_homepage_no_static_shadow_on_active,
    ]
    failed = 0
    for t in tests:
        try:
            t()
        except Exception as e:
            print(f"FAIL: {t.__name__}: {e}")
            failed += 1
    if failed:
        print(f"\n{failed}/{len(tests)} tests FAILED")
        sys.exit(1)
    else:
        print("\nALL TESTS PASSED")

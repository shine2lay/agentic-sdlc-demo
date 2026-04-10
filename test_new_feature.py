"""
Acceptance tests for: staggered fade-in animation on run cards.

Verifies that:
1. HomePage.tsx .map callback captures the array index for stagger delay
2. HomePage.tsx run card div has animate-fade-in class with stagger style
3. index.css .animate-fade-in uses 0.35s duration (not default 0.2s)
4. index.css has prefers-reduced-motion rule that disables .animate-fade-in
"""

import sys
import os
import re

CSS_PATH = os.path.join(os.path.dirname(__file__), "frontend", "src", "index.css")
TSX_PATH = os.path.join(os.path.dirname(__file__), "frontend", "src", "pages", "HomePage.tsx")


def read_file(path: str) -> str:
    with open(path, "r") as f:
        return f.read()


def test_map_callback_captures_index():
    """The .map callback must capture the array index for stagger delay."""
    src = read_file(TSX_PATH)
    assert re.search(r"filteredRuns\.map\(\(run,\s*index\)", src), (
        "filteredRuns.map must capture `index` parameter: .map((run, index) => ...)"
    )
    print("PASS: map callback captures index")


def test_run_card_has_fade_in_class():
    """Each run card div must include the animate-fade-in class."""
    src = read_file(TSX_PATH)
    # Find the run card div (the one with bg-[var(--temper-surface)] and border-l-[3px])
    match = re.search(
        r'className=\{`bg-\[var\(--temper-surface\)\][^`]*`\}', src
    )
    assert match, "Could not find the run card className in HomePage.tsx"
    card_class = match.group(0)
    assert "animate-fade-in" in card_class, (
        "Run card className must include 'animate-fade-in'"
    )
    print("PASS: run card has animate-fade-in class")


def test_run_card_has_stagger_delay():
    """Each run card must set animationDelay based on index * 50ms."""
    src = read_file(TSX_PATH)
    assert re.search(r"animationDelay.*index\s*\*\s*50", src), (
        "Run card must set animationDelay using index * 50ms"
    )
    print("PASS: run card has stagger delay")


def test_run_card_has_fill_mode_backwards():
    """animationFillMode: 'backwards' keeps cards invisible during delay."""
    src = read_file(TSX_PATH)
    assert re.search(r"animationFillMode.*backwards", src), (
        "Run card must set animationFillMode: 'backwards'"
    )
    print("PASS: run card has animationFillMode backwards")


def test_fade_in_duration_is_035s():
    """The .animate-fade-in duration must be 0.35s (not default 0.2s)."""
    src = read_file(CSS_PATH)
    assert re.search(r"\.animate-fade-in\s*\{[^}]*fade-in\s+0\.35s", src), (
        ".animate-fade-in must use 0.35s duration"
    )
    print("PASS: fade-in duration is 0.35s")


def test_reduced_motion_for_fade_in():
    """A prefers-reduced-motion query must disable .animate-fade-in."""
    src = read_file(CSS_PATH)
    pattern = r"@media\s*\(prefers-reduced-motion:\s*reduce\)\s*\{[^}]*\.animate-fade-in\s*\{[^}]*animation:\s*none"
    assert re.search(pattern, src, re.DOTALL), (
        "Must have @media (prefers-reduced-motion: reduce) { .animate-fade-in { animation: none } }"
    )
    print("PASS: reduced-motion disables fade-in")


ALL_TESTS = [
    test_map_callback_captures_index,
    test_run_card_has_fade_in_class,
    test_run_card_has_stagger_delay,
    test_run_card_has_fill_mode_backwards,
    test_fade_in_duration_is_035s,
    test_reduced_motion_for_fade_in,
]

if __name__ == "__main__":
    failed = []
    for t in ALL_TESTS:
        try:
            t()
        except Exception as e:
            failed.append((t.__name__, e))
            print(f"FAIL: {t.__name__}: {e}")

    print(f"\n{len(ALL_TESTS) - len(failed)}/{len(ALL_TESTS)} passed")
    if failed:
        print("FAILED tests:")
        for name, _ in failed:
            print(f"  - {name}")
        sys.exit(1)
    else:
        print("ALL TESTS PASSED")

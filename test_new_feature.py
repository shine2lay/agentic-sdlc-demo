"""
Acceptance tests for: pulsing glow effect on pipeline stage dots when running.

These tests verify the frontend source files contain the expected CSS classes
and conditional logic. They should FAIL before implementation and PASS after.
"""
import sys
import os

# Paths to the target source files
CSS_PATH = os.path.join(os.path.dirname(__file__), "frontend", "src", "index.css")
STAGE_NODE_PATH = os.path.join(
    os.path.dirname(__file__),
    "frontend", "src", "execution", "components", "dag", "StageNode.tsx",
)
SUMMARY_BAR_PATH = os.path.join(
    os.path.dirname(__file__),
    "frontend", "src", "execution", "components", "layout", "WorkflowSummaryBar.tsx",
)
HOMEPAGE_PATH = os.path.join(
    os.path.dirname(__file__), "frontend", "src", "pages", "HomePage.tsx",
)


def _read(path: str) -> str:
    with open(path) as f:
        return f.read()


# ── Test 1: CSS defines the small-glow keyframes and utility class ──────────

def test_css_pulse_glow_sm_keyframes():
    """index.css must contain @keyframes pulse-glow-sm with a smaller spread."""
    css = _read(CSS_PATH)
    assert "@keyframes pulse-glow-sm" in css, (
        "Missing @keyframes pulse-glow-sm in index.css"
    )
    assert ".animate-pulse-glow-sm" in css, (
        "Missing .animate-pulse-glow-sm utility class in index.css"
    )
    print("PASS: CSS defines pulse-glow-sm keyframes and utility class")


# ── Test 2: CSS has prefers-reduced-motion rule for the small glow ───────────

def test_css_reduced_motion_for_sm():
    """The prefers-reduced-motion block must disable animate-pulse-glow-sm."""
    css = _read(CSS_PATH)
    # Find the reduced-motion media block and check it covers the sm variant
    import re
    block = re.search(
        r"@media\s*\(prefers-reduced-motion:\s*reduce\)\s*\{(.+?)\n\}",
        css,
        re.DOTALL,
    )
    assert block is not None, "Missing @media (prefers-reduced-motion: reduce) block"
    inner = block.group(1)
    assert ".animate-pulse-glow-sm" in inner, (
        "prefers-reduced-motion block does not cover .animate-pulse-glow-sm"
    )
    print("PASS: prefers-reduced-motion covers animate-pulse-glow-sm")


# ── Test 3: StageNode status dot gets glow when running ─────────────────────

def test_stage_node_status_dot_glow():
    """StageNode header status dot must apply animate-pulse-glow-sm when running."""
    tsx = _read(STAGE_NODE_PATH)
    assert "animate-pulse-glow-sm" in tsx, (
        "StageNode.tsx does not reference animate-pulse-glow-sm at all"
    )
    # The status dot (w-2.5 h-2.5) should conditionally add the class
    assert "currentStage.status === 'running'" in tsx or "status === 'running'" in tsx, (
        "StageNode.tsx does not conditionally check for running status"
    )
    print("PASS: StageNode status dot applies glow when running")


# ── Test 4: StageNode iteration picker dots get glow when selected+running ──

def test_stage_node_iteration_dot_glow():
    """Iteration picker dots glow only when selected AND the iteration is running."""
    tsx = _read(STAGE_NODE_PATH)
    # Must check both iter.stage.status === 'running' and selection index
    assert "iter.stage.status === 'running'" in tsx, (
        "StageNode.tsx iteration picker does not check iter.stage.status === 'running'"
    )
    print("PASS: StageNode iteration dots glow when selected and running")


# ── Test 5: WorkflowSummaryBar dots glow when running (not slowest) ─────────

def test_summary_bar_running_glow():
    """Summary bar dots must glow when running, unless they are the slowest stage."""
    tsx = _read(SUMMARY_BAR_PATH)
    assert "animate-pulse-glow-sm" in tsx, (
        "WorkflowSummaryBar.tsx does not reference animate-pulse-glow-sm"
    )
    # Should have a branch: isSlowest → yellow ring, running → glow, else plain
    assert "s.status === 'running'" in tsx or "status === 'running'" in tsx, (
        "WorkflowSummaryBar.tsx does not conditionally check for running status"
    )
    print("PASS: WorkflowSummaryBar dots glow when running (not slowest)")


# ── Test 6 (safeguard): HomePage still uses the ORIGINAL animate-pulse-glow ─

def test_homepage_uses_original_glow():
    """HomePage PipelineAnimation must still use animate-pulse-glow (NOT -sm)."""
    tsx = _read(HOMEPAGE_PATH)
    assert "animate-pulse-glow" in tsx, (
        "HomePage.tsx lost the animate-pulse-glow class entirely"
    )
    # It must NOT have been changed to the sm variant
    assert "animate-pulse-glow-sm" not in tsx, (
        "HomePage.tsx was incorrectly changed to use animate-pulse-glow-sm"
    )
    print("PASS: HomePage still uses original animate-pulse-glow (not -sm)")


# ── Test 7 (safeguard): Original pulse-glow CSS is unchanged ────────────────

def test_original_pulse_glow_unchanged():
    """The original @keyframes pulse-glow must still exist with 16px spread."""
    css = _read(CSS_PATH)
    assert "@keyframes pulse-glow {" in css or "@keyframes pulse-glow{" in css, (
        "Original @keyframes pulse-glow is missing from index.css"
    )
    assert "16px" in css, (
        "Original pulse-glow 16px spread value is missing — may have been altered"
    )
    print("PASS: Original pulse-glow keyframes are unchanged")


# ── Runner ───────────────────────────────────────────────────────────────────

ALL_TESTS = [
    test_css_pulse_glow_sm_keyframes,
    test_css_reduced_motion_for_sm,
    test_stage_node_status_dot_glow,
    test_stage_node_iteration_dot_glow,
    test_summary_bar_running_glow,
    test_homepage_uses_original_glow,
    test_original_pulse_glow_unchanged,
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

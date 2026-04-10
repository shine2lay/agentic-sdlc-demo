"""
Acceptance test: colored left border accent on run cards by outcome status.

Verifies that HomePage.tsx has:
1. A `leftBorder` property in the styles Record for each outcome
2. The card wrapper uses `border-l-[3px]` and `${s.leftBorder}` in its className
"""
import sys
import re

TARGET = "frontend/src/pages/HomePage.tsx"


def read_file():
    with open(TARGET, "r") as f:
        return f.read()


def test_styles_record_has_left_border_property():
    """Each outcome in the styles Record must include a leftBorder field."""
    src = read_file()

    # The type annotation should mention leftBorder
    assert "leftBorder: string" in src or "leftBorder:string" in src, (
        "styles Record type annotation does not include 'leftBorder' property"
    )

    # Every outcome entry must have a leftBorder value
    expected_outcomes = ["deployed", "rejected", "failed", "running", "pending"]
    for outcome in expected_outcomes:
        # Find the block for this outcome (e.g. "deployed: { ... leftBorder: '...' ... }")
        pattern = rf"{outcome}:\s*\{{[^}}]*leftBorder:\s*'[^']+'"
        match = re.search(pattern, src)
        assert match is not None, (
            f"Outcome '{outcome}' is missing a leftBorder property in the styles Record"
        )
    print("PASS: styles Record has leftBorder for all outcomes")


def test_card_classname_uses_left_border():
    """The card wrapper div must apply border-l-[3px] and s.leftBorder."""
    src = read_file()

    # Check for border-l-[3px] in the card className
    assert "border-l-[3px]" in src, (
        "Card className does not contain 'border-l-[3px]' for the left border width"
    )

    # Check that ${s.leftBorder} is interpolated into the className
    assert "${s.leftBorder}" in src, (
        "Card className does not interpolate '${s.leftBorder}'"
    )
    print("PASS: card className uses border-l-[3px] and s.leftBorder")


if __name__ == "__main__":
    try:
        test_styles_record_has_left_border_property()
        test_card_classname_uses_left_border()
        print("ALL TESTS PASSED")
    except Exception as e:
        print(f"FAIL: {e}")
        sys.exit(1)

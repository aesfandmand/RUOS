"""The one-viewport hero (design model §22).

The owner stated this as a standing rule for every desktop page, not a note on
one build: the hero is fully visible without scrolling, and a measured sliver
of the next section shows under it so the visitor can see there is more.

The geometry itself is verified in a real browser (§8) -- these tests guard the
two things that would silently delete the rule in a later edit: the height
formula disappearing from the stylesheet, and the rule leaking down to phone
width, where the owner explicitly did not want it.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
CSS = ROOT / "blocks" / "hub-hero" / "style.css"
JS = ROOT / "blocks" / "hub-hero" / "behavior.js"


@pytest.fixture(scope="module")
def css() -> str:
    assert CSS.is_file(), "blocks/hub-hero/style.css is missing"
    return CSS.read_text(encoding="utf-8")


def test_the_hero_height_is_the_viewport_less_header_and_peek(css: str) -> None:
    assert "min-height:calc(100svh - var(--header) - var(--hub-peek))" in css, (
        "§22: the desktop hero height must be the viewport minus the header "
        "minus the deliberate sliver. Without this formula the hero is "
        "whatever its content happens to be and the rule is gone."
    )


def test_the_sliver_is_a_declared_value_not_whatever_is_left(css: str) -> None:
    match = re.search(r"--hub-peek:\s*(\d+)px", css)
    assert match, "§22: --hub-peek must be declared as a real number"
    peek = int(match.group(1))
    assert 40 <= peek <= 160, (
        f"§22: the sliver is {peek}px. Under 40 it reads as a rendering "
        f"accident; over 160 it is a gap, not a hint."
    )


def test_the_rule_is_desktop_only(css: str) -> None:
    """The owner scoped this to desktop. A phone hero squeezed into one short
    viewport drops the lead or the CTA, which is worse than a scroll."""
    start = css.find("@media (width<=1100px)")
    assert start != -1, "§22: hub-hero must have a desktop/handheld boundary at 1100px"
    # the block runs to the next top-level @media, whichever comes first
    nxt = css.find("@media", start + 10)
    block = css[start : nxt if nxt != -1 else len(css)]
    assert "min-height:0" in block, (
        "§22: below 1100px the hero must release its pinned height"
    )


def test_the_header_height_is_measured_not_assumed() -> None:
    """--header is a token with a default; browser chrome and a wrapped nav
    both move the real value, and a hero pinned to the wrong one overflows."""
    js = JS.read_text(encoding="utf-8")
    assert "site-header" in js and 'setProperty("--header"' in js, (
        "§22: hub-hero's behaviour must feed the measured header height back "
        "into the hero rather than trusting the token"
    )


def test_the_light_field_is_decoration_only() -> None:
    """§21: the cursor-driven field carries no text, no control and no meaning,
    and never renders where there is no pointer."""
    markup = (ROOT / "blocks" / "hub-hero" / "markup.html").read_text(encoding="utf-8")
    assert 'class="hub-hero-field" aria-hidden="true"' in markup, (
        "the light field must be aria-hidden and empty"
    )
    css_text = CSS.read_text(encoding="utf-8")
    assert "@media (hover:none),(pointer:coarse){.hub-hero-field{display:none}}" in css_text, (
        "the light field must not render on a touch device"
    )

"""The page critic — the automated art-director/creative-director pass.

Every negative test here mutates a real rendered page rather than building a
fake one from scratch, so what is being proven is that the critic reacts to
the actual shapes ``block_page``/``block_composer`` produce, not to a fixture
that happens to match the critic's own assumptions.
"""
from __future__ import annotations

from dataclasses import replace
from pathlib import Path

import pytest

from ruos.block_composer import ComposedPage
from ruos.block_page import load_page_spec, render_page
from ruos.block_registry import load_library
from ruos.page_critic import PageCritique, critique_page


@pytest.fixture(scope="module")
def library():
    return load_library()


@pytest.fixture(scope="module")
def straboard(library):
    spec = load_page_spec(Path("pages/blocks/straboard.json"))
    return spec, render_page(spec, library)


def test_the_real_straboard_page_earns_a_clean_critique(straboard, library) -> None:
    spec, rendered = straboard
    critique = critique_page(rendered, spec, library)

    assert critique.release_recommendation == "publish"
    assert critique.quality_score == 100
    assert not critique.blockers
    assert not critique.improvement_backlog
    assert critique.placeholder_count > 0  # the datasheet and price notes are real placeholders
    assert {f.discipline for f in critique.findings} == {
        "colour", "navigation", "structure-archetype", "motion", "icons", "content-honesty",
        "images", "rhythm", "accessibility", "seo-schema", "performance",
    }


def test_the_critique_is_deterministic(straboard, library) -> None:
    spec, rendered = straboard
    first = critique_page(rendered, spec, library)
    second = critique_page(rendered, spec, library)

    assert first.payload() == second.payload()
    assert first.sha256 == second.sha256


def test_a_missing_locked_nav_block_is_a_blocker(straboard, library) -> None:
    spec, rendered = straboard
    stripped_composed = replace(rendered.composed, used_blocks=tuple(
        b for b in rendered.composed.used_blocks if b != "bottom-nav"
    ))
    broken = replace(rendered, composed=stripped_composed)

    critique = critique_page(broken, spec, library)
    nav_finding = next(f for f in critique.findings if f.discipline == "navigation")

    assert nav_finding.severity == "blocker"
    assert "bottom-nav" in nav_finding.observation
    assert critique.release_recommendation == "reject"
    assert any("navigation" in blocker for blocker in critique.blockers)


def test_a_dangling_icon_reference_is_caught(straboard, library) -> None:
    spec, rendered = straboard
    broken = replace(rendered, html=rendered.html.replace(
        'href="#icon-home"', 'href="#icon-does-not-exist"', 1,
    ))

    critique = critique_page(broken, spec, library)
    icon_finding = next(f for f in critique.findings if f.discipline == "icons")

    assert icon_finding.severity != "strength"
    assert "icon-does-not-exist" in icon_finding.observation


def test_a_page_with_no_motion_is_flagged(straboard, library) -> None:
    spec, rendered = straboard
    static = replace(rendered, html=rendered.html.replace("data-reveal", "data-inert"))

    critique = critique_page(static, spec, library)
    motion_finding = next(f for f in critique.findings if f.discipline == "motion")

    assert motion_finding.severity != "strength"
    assert "no [data-reveal]" in motion_finding.observation


def test_a_duplicated_h1_fails_accessibility(straboard, library) -> None:
    spec, rendered = straboard
    doubled = replace(rendered, html=rendered.html.replace(
        "<main id=\"main\">", "<main id=\"main\"><h1>یک تیتر اضافه</h1>", 1,
    ))

    critique = critique_page(doubled, spec, library)
    a11y_finding = next(f for f in critique.findings if f.discipline == "accessibility")

    assert a11y_finding.severity != "strength"
    assert "2" in a11y_finding.observation


def test_an_oversized_script_fails_performance(straboard, library) -> None:
    spec, rendered = straboard
    bloated = replace(rendered, script=rendered.script + ("/* padding */" * 10_000))

    critique = critique_page(bloated, spec, library)
    perf_finding = next(f for f in critique.findings if f.discipline == "performance")

    assert perf_finding.severity != "strength"
    assert "script exceeds" in perf_finding.observation


def test_a_short_meta_description_fails_seo(straboard, library) -> None:
    spec, rendered = straboard
    thin_spec = dict(spec)
    thin_spec["description"] = "خیلی کوتاه"

    critique = critique_page(rendered, thin_spec, library)
    seo_finding = next(f for f in critique.findings if f.discipline == "seo-schema")

    assert seo_finding.severity != "strength"
    assert "snippet range" in seo_finding.observation


def test_publish_with_backlog_when_only_non_blocking_findings_exist(straboard, library) -> None:
    spec, rendered = straboard
    thin_spec = dict(spec)
    thin_spec["description"] = "کوتاه"  # a refinement/major, not a blocker

    critique = critique_page(rendered, thin_spec, library)

    assert not critique.blockers
    assert critique.improvement_backlog
    assert critique.release_recommendation == "publish-with-backlog"


def test_report_reads_as_a_short_persian_summary(straboard, library) -> None:
    spec, rendered = straboard
    text = critique_page(rendered, spec, library).report()

    assert text.startswith("# نقد صفحه:")
    assert "100/100" in text
    assert "publish" in text

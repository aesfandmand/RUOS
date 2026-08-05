from dataclasses import replace
from pathlib import Path

import pytest

from ruos.component_resolver import resolve_components
from ruos.pattern_resolver import PatternResolutionError, resolve_patterns
from ruos.spec_loader import load_page_spec


def _page():
    return load_page_spec(Path("pages/structures.json"))


def test_pattern_plan_is_deterministic_and_complete() -> None:
    page = _page()
    components = resolve_components(page)

    first = resolve_patterns(page, components)
    second = resolve_patterns(page, components)

    assert first.fingerprint_payload() == second.fingerprint_payload()
    assert first.narrative_arc == "discover-understand-decide-act"
    assert first.global_motif == "red-umbrella-orbit"
    assert first.scroll_model == "chaptered-progressive"
    assert [pattern.chapter for pattern in first.sections] == [1, 2, 3, 4, 5]
    assert first.sections[0].motif == "orbit"
    assert first.sections[-1].transition == "terminal-stage"


def test_pattern_plan_links_component_variants_to_sections() -> None:
    page = _page()
    components = resolve_components(page)
    plan = resolve_patterns(page, components)

    for section in page.sections:
        pattern = plan.for_section(section.id)
        component = components.for_section(section.id)
        assert pattern.attributes["component_variant"] == component.variant
        assert pattern.attributes["chapter_label"].endswith("/05")


def test_pattern_resolution_rejects_component_count_mismatch() -> None:
    page = _page()
    components = resolve_components(page)
    truncated = replace(components, components=components.components[:-1])

    with pytest.raises(PatternResolutionError, match="one component per section"):
        resolve_patterns(page, truncated)


def test_pattern_lookup_rejects_unknown_section() -> None:
    page = _page()
    plan = resolve_patterns(page, resolve_components(page))

    with pytest.raises(PatternResolutionError, match="No pattern resolved"):
        plan.for_section("missing")

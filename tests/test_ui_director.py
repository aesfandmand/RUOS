from pathlib import Path

import pytest

from ruos.art_director import direct_art
from ruos.component_resolver import resolve_components
from ruos.creative_intelligence import build_creative_intelligence
from ruos.creative_selection import select_creative_library
from ruos.inspiration_intelligence import analyze_inspiration
from ruos.pattern_intelligence import select_patterns
from ruos.pattern_resolver import resolve_patterns
from ruos.query_intelligence import build_query_intelligence
from ruos.research_studio import conduct_research
from ruos.spec_loader import load_page_spec
from ruos.studio_knowledge import compose_studio_knowledge
from ruos.ui_director import UIDirectorError, direct_ui
from ruos.ux_director import direct_ux
from ruos.content_composer import compose_content
from ruos.competitive_intelligence import build_competitive_intelligence
from ruos.visual_dna import resolve_visual_dna


def _inputs():
    page = load_page_spec(Path("pages/structures.json"))
    dna = resolve_visual_dna(page.visual_profile)
    content = compose_content(page)
    intelligence = build_creative_intelligence(page, content)
    research = conduct_research(page, intelligence)
    query = build_query_intelligence(page, research, intelligence)
    competition = build_competitive_intelligence(page, research)
    components = resolve_components(page)
    patterns = resolve_patterns(page, components)
    pattern_selection = select_patterns(page, research, query, competition)
    graph = compose_studio_knowledge(page, research, query, pattern_selection)
    inspiration = analyze_inspiration(page)
    selection = select_creative_library(page, query, components, pattern_selection, graph)
    art = direct_art(page, dna, patterns, selection, inspiration)
    ux = direct_ux(page, components, patterns, art)
    return page, components, art, ux


def test_ui_director_creates_one_distinct_decision_per_section() -> None:
    page, components, art, ux = _inputs()
    ui = direct_ui(page, components, art, ux)
    assert ui.page_slug == "structures"
    assert ui.system_model == "art-led-ux-governed-responsive-interface"
    assert len(ui.sections) == len(page.sections)
    assert [item.section_id for item in ui.sections] == [section.id for section in page.sections]
    assert len({item.composition for item in ui.sections}) == len(ui.sections)
    assert "repetitive equal-weight card wall" in ui.anti_patterns


def test_ui_director_preserves_mobile_and_accessibility_contracts() -> None:
    page, components, art, ux = _inputs()
    ui = direct_ui(page, components, art, ux)
    hero = ui.sections[0]
    knowledge = next(item for item in ui.sections if item.section_id == "knowledge")
    assert "hero remains first" in hero.mobile_behavior
    assert "touch-safe" in knowledge.mobile_behavior
    assert all(item.accessibility_requirements for item in ui.sections)
    assert any("hover" in rule for rule in ui.anti_patterns)


def test_ui_director_is_deterministic_and_rejects_cross_page_inputs() -> None:
    page, components, art, ux = _inputs()
    first = direct_ui(page, components, art, ux)
    second = direct_ui(page, components, art, ux)
    assert first.payload() == second.payload()
    assert first.sha256 == second.sha256
    assert len(first.sha256) == 64

    alien_page = type(page)(
        slug="other",
        lang=page.lang,
        direction=page.direction,
        title=page.title,
        description=page.description,
        brand=page.brand,
        visual_profile=page.visual_profile,
        metadata=page.metadata,
        sections=page.sections,
    )
    with pytest.raises(UIDirectorError):
        direct_ui(alien_page, components, art, ux)

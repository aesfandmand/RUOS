from dataclasses import replace
from pathlib import Path

import pytest

from ruos.art_director import direct_art
from ruos.component_resolver import resolve_components
from ruos.content_composer import compose_content
from ruos.creative_intelligence import build_creative_intelligence
from ruos.creative_selection import select_creative_library
from ruos.inspiration_intelligence import analyze_inspiration
from ruos.pattern_intelligence import select_patterns
from ruos.pattern_resolver import resolve_patterns
from ruos.query_intelligence import build_query_intelligence
from ruos.research_studio import conduct_research
from ruos.competitive_intelligence import build_competitive_intelligence
from ruos.spec_loader import load_page_spec
from ruos.studio_knowledge import compose_studio_knowledge
from ruos.ux_director import UXDirectorError, direct_ux
from ruos.visual_dna import resolve_visual_dna


def _inputs():
    page = load_page_spec(Path("pages/structures.json"))
    components = resolve_components(page)
    patterns = resolve_patterns(page, components)
    content = compose_content(page)
    intelligence = build_creative_intelligence(page, content)
    research = conduct_research(page, intelligence)
    queries = build_query_intelligence(page, research, intelligence)
    competition = build_competitive_intelligence(page, research)
    pattern_intelligence = select_patterns(page, research, queries, competition)
    graph = compose_studio_knowledge(page, research, queries, pattern_intelligence)
    inspiration = analyze_inspiration(page)
    selection = select_creative_library(page, queries, components, pattern_intelligence, graph)
    art = direct_art(page, resolve_visual_dna(page.visual_profile), patterns, selection, inspiration)
    return page, components, patterns, art


def test_ux_director_builds_complete_decision_journey() -> None:
    page, components, patterns, art = _inputs()
    decision = direct_ux(page, components, patterns, art)

    assert decision.journey_model == "orient-understand-compare-decide-act"
    assert [stage.section_id for stage in decision.stages] == [section.id for section in page.sections]
    assert decision.stages[0].desired_state == "curious-and-oriented"
    assert decision.stages[-1].decision_goal == "start a qualified conversation"
    assert all(stage.user_question and stage.exit_condition for stage in decision.stages)
    assert decision.art_decision_sha256 == art.sha256


def test_ux_director_is_deterministic_and_mobile_safe() -> None:
    page, components, patterns, art = _inputs()
    first = direct_ux(page, components, patterns, art)
    second = direct_ux(page, components, patterns, art)

    assert first.payload() == second.payload()
    assert first.sha256 == second.sha256
    assert any("hover" in rule for rule in first.mobile_behavior)
    assert any("reduced-motion" in rule for rule in first.accessibility_contract)
    assert len(first.sha256) == 64


def test_ux_director_rejects_cross_page_art_direction() -> None:
    page, components, patterns, art = _inputs()
    foreign = replace(art, page_slug="another-page")

    with pytest.raises(UXDirectorError, match="do not belong"):
        direct_ux(page, components, patterns, foreign)

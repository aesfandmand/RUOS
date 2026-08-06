from dataclasses import replace
from pathlib import Path

import pytest

from ruos.art_director import ArtDirectorError, direct_art
from ruos.competitive_intelligence import build_competitive_intelligence
from ruos.component_resolver import resolve_components
from ruos.content_composer import compose_content
from ruos.creative_intelligence import build_creative_intelligence
from ruos.creative_selection import select_creative_library
from ruos.inspiration_intelligence import analyze_inspiration
from ruos.pattern_intelligence import select_patterns
from ruos.pattern_resolver import resolve_patterns
from ruos.query_intelligence import build_query_intelligence
from ruos.research_studio import conduct_research
from ruos.spec_loader import load_page_spec
from ruos.studio_knowledge import compose_studio_knowledge
from ruos.visual_dna import resolve_visual_dna


def _inputs():
    page = load_page_spec(Path("pages/structures.json"))
    content = compose_content(page)
    intelligence = build_creative_intelligence(page, content)
    research = conduct_research(page, intelligence)
    queries = build_query_intelligence(page, research, intelligence)
    competition = build_competitive_intelligence(page, research)
    pattern_intelligence = select_patterns(page, research, queries, competition)
    components = resolve_components(page)
    graph = compose_studio_knowledge(page, research, queries, pattern_intelligence)
    selection = select_creative_library(page, queries, components, pattern_intelligence, graph)
    patterns = resolve_patterns(page, components)
    inspiration = analyze_inspiration(page)
    dna = resolve_visual_dna(page.visual_profile)
    return page, dna, patterns, selection, inspiration


def test_inspiration_prioritizes_user_approved_structures_reference() -> None:
    inspiration = _inputs()[-1]
    assert inspiration.evidence_status == "ready"
    assert inspiration.decisions[0].reference_id == "nrg-data-center"
    assert all("copy-layout" in decision.prohibited_actions for decision in inspiration.decisions)
    assert inspiration.payload() == analyze_inspiration(_inputs()[0]).payload()


def test_art_director_is_deterministic_and_mobile_explicit() -> None:
    page, dna, patterns, selection, inspiration = _inputs()
    first = direct_art(page, dna, patterns, selection, inspiration)
    second = direct_art(page, dna, patterns, selection, inspiration)
    assert first.payload() == second.payload()
    assert first.sha256 == second.sha256
    assert first.grid_system.startswith("12-column")
    assert any("mobile" in item for item in first.responsive_translation)
    assert "no repetitive generic card wall" in first.constraints


def test_art_director_rejects_cross_page_inspiration() -> None:
    page, dna, patterns, selection, inspiration = _inputs()
    foreign = replace(inspiration, page_slug="other-page")
    with pytest.raises(ArtDirectorError, match="same page"):
        direct_art(page, dna, patterns, selection, foreign)

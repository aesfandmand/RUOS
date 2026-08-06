from pathlib import Path

import pytest

from ruos.component_resolver import resolve_components
from ruos.creative_intelligence import build_creative_intelligence
from ruos.creative_selection import CreativeSelectionError, select_creative_library
from ruos.content_composer import compose_content
from ruos.pattern_intelligence import select_patterns
from ruos.query_intelligence import build_query_intelligence
from ruos.research_studio import conduct_research
from ruos.competitive_intelligence import build_competitive_intelligence
from ruos.spec_loader import load_page_spec
from ruos.studio_knowledge import compose_studio_knowledge


def _selection():
    page = load_page_spec(Path("pages/structures.json"))
    content = compose_content(page)
    intelligence = build_creative_intelligence(page, content)
    research = conduct_research(page, intelligence)
    queries = build_query_intelligence(page, research, intelligence)
    competition = build_competitive_intelligence(page, research)
    patterns = select_patterns(page, research, queries, competition)
    components = resolve_components(page)
    graph = compose_studio_knowledge(page, research, queries, patterns)
    return page, queries, components, patterns, graph, select_creative_library(page, queries, components, patterns, graph)


def test_selection_covers_every_required_creative_category() -> None:
    selection = _selection()[-1]
    assert [decision.category for decision in selection.decisions] == [
        "hero",
        "layout",
        "typography",
        "motion",
        "interaction",
        "story",
    ]
    assert all(decision.score >= 88 for decision in selection.decisions)
    assert len({candidate.id for candidate in selection.registry}) == len(selection.registry)


def test_selection_is_deterministic_and_explainable() -> None:
    first = _selection()[-1]
    second = _selection()[-1]
    assert first.payload() == second.payload()
    assert first.sha256 == second.sha256
    assert all(decision.reasons for decision in first.decisions)
    assert all(len(decision.candidate_id) > 4 for decision in first.decisions)


def test_selection_rejects_cross_page_inputs() -> None:
    page, queries, components, patterns, graph, _ = _selection()
    invalid_graph = type(graph)(
        page_slug="another-page",
        entities=graph.entities,
        relations=graph.relations,
    )
    with pytest.raises(CreativeSelectionError):
        select_creative_library(page, queries, components, patterns, invalid_graph)

from dataclasses import replace
from pathlib import Path

import pytest

from ruos.content_composer import compose_content
from ruos.creative_intelligence import build_creative_intelligence
from ruos.creative_knowledge_graph import (
    CreativeKnowledgeGraphError,
    KnowledgeEntity,
    KnowledgeRelation,
    build_graph,
)
from ruos.creative_registry import CreativeRegistryError, RegistryItem, default_creative_registry
from ruos.pattern_intelligence import PatternIntelligenceError, select_patterns
from ruos.query_intelligence import build_query_intelligence
from ruos.competitive_intelligence import build_competitive_intelligence
from ruos.research_studio import conduct_research
from ruos.spec_loader import load_page_spec
from ruos.studio_knowledge import compose_studio_knowledge


def _stack():
    page = load_page_spec(Path("pages/structures.json"))
    content = compose_content(page)
    intelligence = build_creative_intelligence(page, content)
    research = conduct_research(page, intelligence)
    queries = build_query_intelligence(page, research, intelligence)
    competition = build_competitive_intelligence(page, research)
    patterns = select_patterns(page, research, queries, competition)
    graph = compose_studio_knowledge(page, research, queries, patterns)
    return page, research, queries, competition, patterns, graph


def test_graph_is_traceable_query_led_and_deterministic() -> None:
    first = _stack()[-1]
    second = _stack()[-1]

    assert first.payload() == second.payload()
    assert first.sha256 == second.sha256
    assert len(first.sha256) == 64
    assert first.targets("intent:commercial-investigation", "prefers")
    assert all(edge.evidence for edge in first.relations)
    assert any(entity.kind == "persona" for entity in first.entities)
    assert any(entity.kind == "cta" for entity in first.entities)


def test_graph_rejects_duplicate_unknown_and_self_relations() -> None:
    entity = KnowledgeEntity("query:one", "query", "one")
    with pytest.raises(CreativeKnowledgeGraphError, match="duplicate entity"):
        build_graph("page", (entity, entity), ())

    with pytest.raises(CreativeKnowledgeGraphError, match="unknown entity"):
        build_graph(
            "page",
            (entity,),
            (KnowledgeRelation("query:one", "suggests", "intent:missing", "test"),),
        )

    with pytest.raises(CreativeKnowledgeGraphError, match="Self-referential"):
        build_graph(
            "page",
            (entity,),
            (KnowledgeRelation("query:one", "suggests", "query:one", "test"),),
        )


def test_registry_is_scored_ranked_and_unique() -> None:
    registry = default_creative_registry()
    ranked = registry.ranked("interaction", minimum=80)
    assert ranked
    assert ranked[0].id == "decision-path-interaction"
    assert ranked[0].composite_score >= 80

    duplicate = registry.items[0]
    with pytest.raises(CreativeRegistryError, match="duplicate ids"):
        type(registry)((duplicate, duplicate))


def test_pattern_intelligence_rejects_unregistered_candidates() -> None:
    page, research, queries, competition, _, _ = _stack()
    broken_candidate = replace(research.pattern_candidates[0], id="unregistered-pattern")
    broken_research = replace(
        research,
        pattern_candidates=(broken_candidate,) + research.pattern_candidates[1:],
    )
    with pytest.raises(PatternIntelligenceError, match="missing from the creative registry"):
        select_patterns(page, broken_research, queries, competition)


def test_registry_score_is_embedded_in_pattern_decision() -> None:
    patterns = _stack()[4]
    assert all(item.registry_score >= 80 for item in patterns.selected)
    assert all("registry_score" in item.payload() for item in patterns.selected)

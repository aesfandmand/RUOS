from __future__ import annotations

from .creative_knowledge_graph import (
    CreativeKnowledgeGraph,
    KnowledgeEntity,
    KnowledgeRelation,
    build_graph,
)
from .creative_registry import CreativeRegistry, default_creative_registry
from .models import PageSpec
from .pattern_intelligence import PatternIntelligence
from .query_intelligence import QueryIntelligence
from .research_studio import ResearchBrief


def _ordered_queries(queries: QueryIntelligence) -> tuple[str, ...]:
    """Return the primary query followed by unique cluster queries in strategy order."""
    seen = {queries.primary_query}
    ordered = [queries.primary_query]
    for cluster in queries.clusters:
        for query in cluster.queries:
            if query not in seen:
                seen.add(query)
                ordered.append(query)
    return tuple(ordered)


def compose_studio_knowledge(
    page: PageSpec,
    research: ResearchBrief,
    queries: QueryIntelligence,
    patterns: PatternIntelligence,
    registry: CreativeRegistry | None = None,
) -> CreativeKnowledgeGraph:
    if len({page.slug, research.page_slug, queries.page_slug, patterns.page_slug}) != 1:
        raise ValueError("Knowledge inputs do not belong to the same page")

    registry = registry or default_creative_registry()
    entities: list[KnowledgeEntity] = [
        KnowledgeEntity("brand:" + page.brand, "brand", page.brand),
        KnowledgeEntity("industry:advertising-structures", "industry", "سازه‌های تبلیغاتی"),
        KnowledgeEntity(
            "intent:" + queries.search_intent,
            "intent",
            queries.search_intent,
        ),
    ]
    relations: list[KnowledgeRelation] = []

    brand_id = "brand:" + page.brand
    industry_id = "industry:advertising-structures"
    intent_id = "intent:" + queries.search_intent
    relations.append(KnowledgeRelation(brand_id, "fits", industry_id, "page-spec"))

    for index, query in enumerate(_ordered_queries(queries)):
        query_id = f"query:{index}:{query}"
        entities.append(KnowledgeEntity(query_id, "query", query))
        relations.append(KnowledgeRelation(query_id, "suggests", intent_id, "query-intelligence.json"))
        relations.append(KnowledgeRelation(query_id, "targets", industry_id, "research.json"))

    for index, hypothesis in enumerate(research.audience_hypotheses):
        persona_id = f"persona:{index}"
        entities.append(KnowledgeEntity(persona_id, "persona", hypothesis))
        relations.append(KnowledgeRelation(intent_id, "targets", persona_id, "research.json"))

    selected_ids = {item.id for item in patterns.selected}
    registry_ids = {item.id for item in registry.items}
    missing = selected_ids - registry_ids
    if missing:
        raise ValueError("Selected patterns are missing from creative registry: " + ", ".join(sorted(missing)))

    for selected in patterns.selected:
        registry_item = registry.get(selected.id)
        pattern_id = "pattern:" + selected.id
        entities.append(
            KnowledgeEntity(
                pattern_id,
                "pattern",
                selected.id,
                attributes=(
                    ("kind", selected.kind),
                    ("evidence_score", selected.score),
                    ("registry_score", registry_item.composite_score),
                    ("source_id", selected.source_id),
                ),
            )
        )
        relations.append(
            KnowledgeRelation(
                intent_id,
                "prefers",
                pattern_id,
                "pattern-selection.json",
                weight=registry_item.composite_score,
            )
        )
        relations.append(
            KnowledgeRelation(
                pattern_id,
                "constrains",
                brand_id,
                "creative-registry",
                weight=registry_item.rtl_score,
            )
        )

    cta_id = "cta:qualified-conversation"
    entities.append(KnowledgeEntity(cta_id, "cta", "qualified-conversation"))
    relations.append(KnowledgeRelation(intent_id, "advances", cta_id, "query-intelligence.json"))

    return build_graph(page.slug, entities, relations)

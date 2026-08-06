from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass

from .creative_intelligence import CreativeIntelligencePlan
from .models import PageSpec
from .research_studio import ResearchBrief


class QueryIntelligenceError(ValueError):
    """Raised when query evidence cannot support a production search strategy."""


@dataclass(frozen=True)
class QueryCluster:
    name: str
    intent: str
    queries: tuple[str, ...]
    journey_stage: str
    priority: int

    def payload(self) -> dict[str, object]:
        return {
            "name": self.name,
            "intent": self.intent,
            "queries": list(self.queries),
            "journey_stage": self.journey_stage,
            "priority": self.priority,
        }


@dataclass(frozen=True)
class QueryIntelligence:
    page_slug: str
    market: str
    language: str
    primary_query: str
    search_intent: str
    clusters: tuple[QueryCluster, ...]
    entities: tuple[str, ...]
    answer_targets: tuple[str, ...]
    evidence_source_ids: tuple[str, ...]
    limitations: tuple[str, ...]

    def payload(self) -> dict[str, object]:
        return {
            "page_slug": self.page_slug,
            "market": self.market,
            "language": self.language,
            "primary_query": self.primary_query,
            "search_intent": self.search_intent,
            "clusters": [cluster.payload() for cluster in self.clusters],
            "entities": list(self.entities),
            "answer_targets": list(self.answer_targets),
            "evidence_source_ids": list(self.evidence_source_ids),
            "limitations": list(self.limitations),
        }

    @property
    def sha256(self) -> str:
        canonical = json.dumps(self.payload(), ensure_ascii=False, sort_keys=True, separators=(",", ":"))
        return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def _normalise(values: tuple[str, ...]) -> tuple[str, ...]:
    seen: set[str] = set()
    ordered: list[str] = []
    for value in values:
        item = " ".join(value.split())
        if item and item not in seen:
            seen.add(item)
            ordered.append(item)
    return tuple(ordered)


def _classify(query: str) -> tuple[str, str, int]:
    lowered = query.casefold()
    if any(token in lowered for token in ("خرید", "قیمت", "سفارش")):
        return "commercial", "decision", 100
    if any(token in lowered for token in ("سرمایه", "اجاره", "بازده")):
        return "investment", "decision", 95
    if any(token in lowered for token in ("انواع", "مقایسه", "راهنما", "انتخاب")):
        return "comparison", "consideration", 85
    if any(token in lowered for token in ("ایندور", "اوتدور", "دیجیتال")):
        return "solution", "consideration", 80
    return "discovery", "awareness", 70


def build_query_intelligence(
    page: PageSpec,
    research: ResearchBrief,
    intelligence: CreativeIntelligencePlan,
) -> QueryIntelligence:
    if research.page_slug != page.slug or intelligence.page_slug != page.slug:
        raise QueryIntelligenceError("Query inputs do not belong to the same page")
    if research.evidence_status != "ready":
        raise QueryIntelligenceError("Query intelligence requires production-ready research")

    primary = " ".join(intelligence.query.primary_query.split())
    supporting = _normalise(intelligence.query.supporting_queries)
    if not primary:
        raise QueryIntelligenceError("Primary query cannot be empty")
    if primary in supporting:
        raise QueryIntelligenceError("Primary query must not be duplicated in supporting queries")
    if len(supporting) < 3:
        raise QueryIntelligenceError("At least three supporting queries are required")

    grouped: dict[str, list[tuple[str, str, int]]] = {}
    for query in supporting:
        cluster, stage, priority = _classify(query)
        grouped.setdefault(cluster, []).append((query, stage, priority))

    clusters = tuple(
        QueryCluster(
            name=name,
            intent="commercial-investigation" if name != "discovery" else "informational",
            queries=tuple(item[0] for item in items),
            journey_stage=items[0][1],
            priority=max(item[2] for item in items),
        )
        for name, items in sorted(grouped.items(), key=lambda item: (-max(x[2] for x in item[1]), item[0]))
    )

    evidence_ids = tuple(
        source.id for source in research.sources if source.kind in {"search-demand", "competitor", "market-source"}
    )
    if not evidence_ids:
        raise QueryIntelligenceError("No search or market evidence is available")

    entities = _normalise(tuple(intelligence.semantic.entities))
    answer_targets = _normalise(tuple(intelligence.semantic.answer_targets))
    return QueryIntelligence(
        page_slug=page.slug,
        market=research.market,
        language=page.lang,
        primary_query=primary,
        search_intent=intelligence.query.search_intent,
        clusters=clusters,
        entities=entities,
        answer_targets=answer_targets,
        evidence_source_ids=evidence_ids,
        limitations=research.limitations,
    )

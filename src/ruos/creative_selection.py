from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass

from .component_resolver import ComponentPlan
from .creative_knowledge_graph import CreativeKnowledgeGraph
from .models import PageSpec
from .pattern_intelligence import PatternIntelligence
from .query_intelligence import QueryIntelligence


class CreativeSelectionError(ValueError):
    """Raised when no production-safe creative candidate can be selected."""


@dataclass(frozen=True)
class LibraryCandidate:
    id: str
    category: str
    intents: tuple[str, ...]
    page_kinds: tuple[str, ...]
    rtl_score: int
    mobile_score: int
    accessibility_score: int
    performance_score: int
    conversion_score: int
    agency_score: int
    capabilities: tuple[str, ...]

    @property
    def quality_score(self) -> int:
        values = (
            self.rtl_score,
            self.mobile_score,
            self.accessibility_score,
            self.performance_score,
            self.conversion_score,
            self.agency_score,
        )
        return round(sum(values) / len(values))

    def payload(self) -> dict[str, object]:
        return {
            "id": self.id,
            "category": self.category,
            "intents": list(self.intents),
            "page_kinds": list(self.page_kinds),
            "scores": {
                "rtl": self.rtl_score,
                "mobile": self.mobile_score,
                "accessibility": self.accessibility_score,
                "performance": self.performance_score,
                "conversion": self.conversion_score,
                "agency": self.agency_score,
                "quality": self.quality_score,
            },
            "capabilities": list(self.capabilities),
        }


@dataclass(frozen=True)
class SelectionDecision:
    category: str
    candidate_id: str
    score: int
    reasons: tuple[str, ...]
    alternatives: tuple[tuple[str, int], ...]

    def payload(self) -> dict[str, object]:
        return {
            "category": self.category,
            "candidate_id": self.candidate_id,
            "score": self.score,
            "reasons": list(self.reasons),
            "alternatives": [
                {"candidate_id": candidate_id, "score": score}
                for candidate_id, score in self.alternatives
            ],
        }


@dataclass(frozen=True)
class CreativeSelectionPlan:
    page_slug: str
    decisions: tuple[SelectionDecision, ...]
    registry: tuple[LibraryCandidate, ...]
    knowledge_graph_sha256: str

    def payload(self) -> dict[str, object]:
        return {
            "page_slug": self.page_slug,
            "knowledge_graph_sha256": self.knowledge_graph_sha256,
            "decisions": [decision.payload() for decision in self.decisions],
            "registry": [candidate.payload() for candidate in self.registry],
        }

    @property
    def sha256(self) -> str:
        canonical = json.dumps(self.payload(), ensure_ascii=False, sort_keys=True, separators=(",", ":"))
        return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


_REGISTRY = (
    LibraryCandidate("hero-cinematic-orbit", "hero", ("commercial-investigation",), ("hero",), 96, 92, 90, 88, 91, 95, ("ambient-art", "scroll-cue", "primary-cta")),
    LibraryCandidate("hero-editorial-monument", "hero", ("commercial-investigation", "informational"), ("hero",), 98, 95, 96, 94, 88, 93, ("editorial-type", "progressive-reveal", "primary-cta")),
    LibraryCandidate("layout-chaptered-asymmetry", "layout", ("commercial-investigation",), ("story", "knowledge"), 97, 91, 92, 90, 90, 96, ("chapter-markers", "asymmetric-grid", "visual-pauses")),
    LibraryCandidate("layout-decision-path", "layout", ("commercial-investigation",), ("interaction", "conversion"), 96, 94, 96, 91, 97, 92, ("progressive-disclosure", "route-comparison", "state-feedback")),
    LibraryCandidate("type-persian-editorial", "typography", ("commercial-investigation", "informational"), ("hero", "story", "knowledge", "interaction", "conversion"), 100, 98, 97, 99, 90, 94, ("persian-readable", "display-to-body-scale", "numeric-clarity")),
    LibraryCandidate("motion-narrative-cues", "motion", ("commercial-investigation",), ("hero", "story", "knowledge"), 96, 92, 94, 88, 89, 95, ("chapter-entry", "focus-shift", "reduced-motion")),
    LibraryCandidate("motion-decision-feedback", "motion", ("commercial-investigation",), ("interaction", "conversion"), 97, 95, 98, 94, 96, 91, ("state-feedback", "route-confirmation", "reduced-motion")),
    LibraryCandidate("interaction-guided-comparison", "interaction", ("commercial-investigation",), ("interaction", "knowledge"), 98, 96, 98, 92, 97, 93, ("keyboard-ready", "semantic-state", "comparison")),
    LibraryCandidate("story-problem-to-decision", "story", ("commercial-investigation",), ("story", "knowledge", "conversion"), 98, 96, 97, 99, 96, 95, ("problem-framing", "proof-bridge", "decision-closure")),
)


def _score(candidate: LibraryCandidate, page: PageSpec, queries: QueryIntelligence, components: ComponentPlan, patterns: PatternIntelligence) -> tuple[int, tuple[str, ...]]:
    score = candidate.quality_score
    reasons: list[str] = [f"quality:{candidate.quality_score}"]
    if queries.search_intent in candidate.intents:
        score += 8
        reasons.append("intent-fit")
    available_kinds = {section.kind for section in page.sections}
    if set(candidate.page_kinds) & available_kinds:
        score += 4
        reasons.append("page-kind-fit")
    component_capabilities = {capability for component in components.components for capability in component.capabilities}
    overlap = set(candidate.capabilities) & component_capabilities
    if overlap:
        score += min(4, len(overlap))
        reasons.append("component-capability-fit")
    pattern_kinds = {pattern.kind for pattern in patterns.selected}
    if candidate.category in pattern_kinds or candidate.category in {"hero", "layout", "typography", "story"}:
        score += 2
        reasons.append("pattern-graph-fit")
    if page.direction == "rtl" and candidate.rtl_score >= 95:
        score += 3
        reasons.append("rtl-safe")
    return min(100, score), tuple(reasons)


def select_creative_library(
    page: PageSpec,
    queries: QueryIntelligence,
    components: ComponentPlan,
    patterns: PatternIntelligence,
    knowledge_graph: CreativeKnowledgeGraph,
) -> CreativeSelectionPlan:
    if len({page.slug, queries.page_slug, components.page_slug, patterns.page_slug, knowledge_graph.page_slug}) != 1:
        raise CreativeSelectionError("Creative selection inputs do not belong to the same page")

    categories = ("hero", "layout", "typography", "motion", "interaction", "story")
    decisions: list[SelectionDecision] = []
    for category in categories:
        ranked = sorted(
            (
                (candidate, *_score(candidate, page, queries, components, patterns))
                for candidate in _REGISTRY
                if candidate.category == category
            ),
            key=lambda item: (-item[1], item[0].id),
        )
        if not ranked:
            raise CreativeSelectionError(f"No registered candidate for category '{category}'")
        winner, score, reasons = ranked[0]
        if score < 88:
            raise CreativeSelectionError(f"Best candidate for '{category}' scored below production threshold")
        decisions.append(
            SelectionDecision(
                category=category,
                candidate_id=winner.id,
                score=score,
                reasons=reasons,
                alternatives=tuple((candidate.id, candidate_score) for candidate, candidate_score, _ in ranked[1:]),
            )
        )

    return CreativeSelectionPlan(
        page_slug=page.slug,
        decisions=tuple(decisions),
        registry=_REGISTRY,
        knowledge_graph_sha256=knowledge_graph.sha256,
    )

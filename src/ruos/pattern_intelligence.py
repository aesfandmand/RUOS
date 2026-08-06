from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass

from .competitive_intelligence import CompetitiveIntelligence
from .creative_registry import CreativeRegistry, default_creative_registry
from .models import PageSpec
from .query_intelligence import QueryIntelligence
from .research_studio import PatternCandidate, ResearchBrief


class PatternIntelligenceError(ValueError):
    """Raised when design patterns cannot be selected from traceable evidence."""


@dataclass(frozen=True)
class SelectedPattern:
    id: str
    kind: str
    source_id: str
    score: int
    rationale: str
    constraints: tuple[str, ...]
    registry_score: int

    def payload(self) -> dict[str, object]:
        return {
            "id": self.id,
            "kind": self.kind,
            "source_id": self.source_id,
            "score": self.score,
            "registry_score": self.registry_score,
            "rationale": self.rationale,
            "constraints": list(self.constraints),
        }


@dataclass(frozen=True)
class PatternIntelligence:
    page_slug: str
    selected: tuple[SelectedPattern, ...]
    rejected: tuple[dict[str, str], ...]
    selection_policy: str

    def payload(self) -> dict[str, object]:
        return {
            "page_slug": self.page_slug,
            "selected": [item.payload() for item in self.selected],
            "rejected": [dict(item) for item in self.rejected],
            "selection_policy": self.selection_policy,
        }

    @property
    def sha256(self) -> str:
        canonical = json.dumps(self.payload(), ensure_ascii=False, sort_keys=True, separators=(",", ":"))
        return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def _score(
    candidate: PatternCandidate,
    page: PageSpec,
    queries: QueryIntelligence,
    registry: CreativeRegistry,
) -> tuple[int, int]:
    try:
        registered = registry.get(candidate.id)
    except KeyError as exc:
        raise PatternIntelligenceError(
            f"Pattern '{candidate.id}' is missing from the creative registry"
        ) from exc

    if registered.kind != candidate.kind:
        raise PatternIntelligenceError(
            f"Pattern '{candidate.id}' kind does not match registry contract"
        )

    evidence_score = 65
    evidence_score += min(10, len(candidate.constraints) * 3)
    if page.direction == "rtl":
        evidence_score += round(registered.rtl_score * 0.08)
    if queries.search_intent == "commercial-investigation":
        evidence_score += round(registered.conversion_score * 0.08)

    blended = round(evidence_score * 0.45 + registered.composite_score * 0.55)
    return min(100, blended), registered.composite_score


def select_patterns(
    page: PageSpec,
    research: ResearchBrief,
    queries: QueryIntelligence,
    competition: CompetitiveIntelligence,
    registry: CreativeRegistry | None = None,
) -> PatternIntelligence:
    if len({page.slug, research.page_slug, queries.page_slug, competition.page_slug}) != 1:
        raise PatternIntelligenceError("Pattern inputs do not belong to the same page")

    registry = registry or default_creative_registry()
    ranked = sorted(
        (
            (candidate, *_score(candidate, page, queries, registry))
            for candidate in research.pattern_candidates
        ),
        key=lambda item: (-item[1], -item[2], item[0].kind, item[0].id),
    )
    selected: list[SelectedPattern] = []
    rejected: list[dict[str, str]] = []
    used_kinds: set[str] = set()
    for candidate, score, registry_score in ranked:
        if score < 75:
            rejected.append({"id": candidate.id, "reason": "score-below-75"})
            continue
        if candidate.kind in used_kinds:
            rejected.append({"id": candidate.id, "reason": "lower-ranked-duplicate-kind"})
            continue
        selected.append(
            SelectedPattern(
                id=candidate.id,
                kind=candidate.kind,
                source_id=candidate.source_id,
                score=score,
                registry_score=registry_score,
                rationale=candidate.rationale,
                constraints=candidate.constraints,
            )
        )
        used_kinds.add(candidate.kind)

    required = {"storytelling", "interaction"}
    missing = required - used_kinds
    if missing:
        raise PatternIntelligenceError("Required creative pattern kinds are missing: " + ", ".join(sorted(missing)))
    if len(selected) < 3:
        raise PatternIntelligenceError("At least three evidence-backed patterns must be selected")

    return PatternIntelligence(
        page_slug=page.slug,
        selected=tuple(selected),
        rejected=tuple(rejected),
        selection_policy=(
            "Resolve candidates through the scored creative registry, blend evidence and studio-quality "
            "scores, select one highest-ranked pattern per kind, and preserve RTL, mobile, accessibility, "
            "performance and conversion constraints."
        ),
    )

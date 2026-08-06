from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass

from .competitive_intelligence import CompetitiveIntelligence
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

    def payload(self) -> dict[str, object]:
        return {
            "id": self.id,
            "kind": self.kind,
            "source_id": self.source_id,
            "score": self.score,
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


def _score(candidate: PatternCandidate, page: PageSpec, queries: QueryIntelligence) -> int:
    score = 60
    if candidate.kind in {"storytelling", "scroll", "interaction", "motion"}:
        score += 12
    if page.direction == "rtl" and any("RTL" in constraint or "موبایل" in constraint for constraint in candidate.constraints):
        score += 10
    if queries.search_intent == "commercial-investigation" and candidate.kind in {"interaction", "conversion", "storytelling"}:
        score += 10
    if candidate.constraints:
        score += min(8, len(candidate.constraints) * 2)
    return min(100, score)


def select_patterns(
    page: PageSpec,
    research: ResearchBrief,
    queries: QueryIntelligence,
    competition: CompetitiveIntelligence,
) -> PatternIntelligence:
    if len({page.slug, research.page_slug, queries.page_slug, competition.page_slug}) != 1:
        raise PatternIntelligenceError("Pattern inputs do not belong to the same page")

    ranked = sorted(
        ((candidate, _score(candidate, page, queries)) for candidate in research.pattern_candidates),
        key=lambda item: (-item[1], item[0].kind, item[0].id),
    )
    selected: list[SelectedPattern] = []
    rejected: list[dict[str, str]] = []
    used_kinds: set[str] = set()
    for candidate, score in ranked:
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
        selection_policy="Select one highest-scoring pattern per kind; require storytelling and interaction; preserve RTL, mobile, accessibility and performance constraints.",
    )

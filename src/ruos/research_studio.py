from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from typing import Mapping, Sequence

from .creative_intelligence import CreativeIntelligencePlan
from .models import PageSpec


class ResearchStudioError(ValueError):
    """Raised when a page lacks enough traceable evidence for studio decisions."""


_ALLOWED_SOURCE_KINDS = {
    "search-demand",
    "competitor",
    "design-reference",
    "ux-research",
    "brand-source",
    "market-source",
}

_ALLOWED_PATTERN_KINDS = {
    "hero",
    "layout",
    "storytelling",
    "scroll",
    "motion",
    "typography",
    "interaction",
    "conversion",
    "data-visualization",
}


@dataclass(frozen=True)
class ResearchSource:
    id: str
    kind: str
    title: str
    url: str
    market: str
    language: str
    notes: str

    def payload(self) -> dict[str, str]:
        return {
            "id": self.id,
            "kind": self.kind,
            "title": self.title,
            "url": self.url,
            "market": self.market,
            "language": self.language,
            "notes": self.notes,
        }


@dataclass(frozen=True)
class PatternCandidate:
    id: str
    kind: str
    name: str
    source_id: str
    rationale: str
    constraints: tuple[str, ...]

    def payload(self) -> dict[str, object]:
        return {
            "id": self.id,
            "kind": self.kind,
            "name": self.name,
            "source_id": self.source_id,
            "rationale": self.rationale,
            "constraints": list(self.constraints),
        }


@dataclass(frozen=True)
class ResearchBrief:
    page_slug: str
    market: str
    language: str
    primary_query: str
    supporting_queries: tuple[str, ...]
    audience_hypotheses: tuple[str, ...]
    sources: tuple[ResearchSource, ...]
    pattern_candidates: tuple[PatternCandidate, ...]
    evidence_score: int
    evidence_status: str
    limitations: tuple[str, ...]
    provenance: Mapping[str, object] | None = None

    def payload(self) -> dict[str, object]:
        payload: dict[str, object] = {
            "page_slug": self.page_slug,
            "market": self.market,
            "language": self.language,
            "primary_query": self.primary_query,
            "supporting_queries": list(self.supporting_queries),
            "audience_hypotheses": list(self.audience_hypotheses),
            "sources": [source.payload() for source in self.sources],
            "pattern_candidates": [candidate.payload() for candidate in self.pattern_candidates],
            "evidence_score": self.evidence_score,
            "evidence_status": self.evidence_status,
            "limitations": list(self.limitations),
        }
        if self.provenance is not None:
            payload["provenance"] = dict(self.provenance)
        return payload

    @property
    def sha256(self) -> str:
        canonical = json.dumps(self.payload(), ensure_ascii=False, sort_keys=True, separators=(",", ":"))
        return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def _require_text(value: object, field: str) -> str:
    text = str(value or "").strip()
    if not text:
        raise ResearchStudioError(f"Research field '{field}' cannot be empty")
    return text


def _as_sequence(value: object, field: str) -> Sequence[object]:
    if not isinstance(value, (list, tuple)):
        raise ResearchStudioError(f"Research field '{field}' must be a list")
    return value


def _parse_sources(raw: object) -> tuple[ResearchSource, ...]:
    sources: list[ResearchSource] = []
    seen: set[str] = set()
    for index, item in enumerate(_as_sequence(raw, "sources"), start=1):
        if not isinstance(item, Mapping):
            raise ResearchStudioError(f"Research source #{index} must be an object")
        source = ResearchSource(
            id=_require_text(item.get("id"), f"sources[{index}].id"),
            kind=_require_text(item.get("kind"), f"sources[{index}].kind"),
            title=_require_text(item.get("title"), f"sources[{index}].title"),
            url=_require_text(item.get("url"), f"sources[{index}].url"),
            market=_require_text(item.get("market"), f"sources[{index}].market"),
            language=_require_text(item.get("language"), f"sources[{index}].language"),
            notes=_require_text(item.get("notes"), f"sources[{index}].notes"),
        )
        if source.kind not in _ALLOWED_SOURCE_KINDS:
            raise ResearchStudioError(f"Unsupported research source kind: {source.kind}")
        if not source.url.startswith(("https://", "http://")):
            raise ResearchStudioError(f"Research source '{source.id}' must use an absolute URL")
        if source.id in seen:
            raise ResearchStudioError(f"Duplicate research source id: {source.id}")
        seen.add(source.id)
        sources.append(source)
    return tuple(sources)


def _parse_patterns(raw: object, source_ids: set[str]) -> tuple[PatternCandidate, ...]:
    candidates: list[PatternCandidate] = []
    seen: set[str] = set()
    for index, item in enumerate(_as_sequence(raw, "patterns"), start=1):
        if not isinstance(item, Mapping):
            raise ResearchStudioError(f"Pattern candidate #{index} must be an object")
        constraints = tuple(
            _require_text(value, f"patterns[{index}].constraints")
            for value in _as_sequence(item.get("constraints", []), f"patterns[{index}].constraints")
        )
        candidate = PatternCandidate(
            id=_require_text(item.get("id"), f"patterns[{index}].id"),
            kind=_require_text(item.get("kind"), f"patterns[{index}].kind"),
            name=_require_text(item.get("name"), f"patterns[{index}].name"),
            source_id=_require_text(item.get("source_id"), f"patterns[{index}].source_id"),
            rationale=_require_text(item.get("rationale"), f"patterns[{index}].rationale"),
            constraints=constraints,
        )
        if candidate.kind not in _ALLOWED_PATTERN_KINDS:
            raise ResearchStudioError(f"Unsupported pattern kind: {candidate.kind}")
        if candidate.source_id not in source_ids:
            raise ResearchStudioError(
                f"Pattern '{candidate.id}' references unknown source '{candidate.source_id}'"
            )
        if candidate.id in seen:
            raise ResearchStudioError(f"Duplicate pattern candidate id: {candidate.id}")
        seen.add(candidate.id)
        candidates.append(candidate)
    return tuple(candidates)


def _evidence_score(sources: tuple[ResearchSource, ...], patterns: tuple[PatternCandidate, ...]) -> int:
    kinds = {source.kind for source in sources}
    markets = {source.market.lower() for source in sources}
    pattern_kinds = {pattern.kind for pattern in patterns}
    score = 30
    score += min(24, len(sources) * 4)
    score += min(18, len(kinds) * 3)
    score += 12 if "iran" in markets or "ایران" in markets else 0
    score += min(16, len(pattern_kinds) * 2)
    return min(100, score)


def conduct_research(page: PageSpec, intelligence: CreativeIntelligencePlan) -> ResearchBrief:
    research = page.metadata.get("research")
    if not isinstance(research, Mapping):
        raise ResearchStudioError("Page metadata must include a 'research' object")

    sources = _parse_sources(research.get("sources", []))
    patterns = _parse_patterns(research.get("patterns", []), {source.id for source in sources})
    audience_hypotheses = tuple(
        _require_text(value, "audience_hypotheses")
        for value in _as_sequence(research.get("audience_hypotheses", []), "audience_hypotheses")
    )
    limitations = tuple(
        _require_text(value, "limitations")
        for value in _as_sequence(research.get("limitations", []), "limitations")
    )

    source_kinds = {source.kind for source in sources}
    required_source_kinds = {"search-demand", "competitor", "design-reference"}
    missing_kinds = sorted(required_source_kinds - source_kinds)
    if missing_kinds:
        raise ResearchStudioError(
            "Research evidence is missing required source kinds: " + ", ".join(missing_kinds)
        )
    if len(sources) < 5:
        raise ResearchStudioError("Research Studio requires at least five traceable sources")
    if len(patterns) < 3:
        raise ResearchStudioError("Research Studio requires at least three pattern candidates")
    if not audience_hypotheses:
        raise ResearchStudioError("Research Studio requires at least one audience hypothesis")

    score = _evidence_score(sources, patterns)
    status = "ready" if score >= 75 else "provisional"
    if status != "ready":
        raise ResearchStudioError(f"Research evidence score {score} is below production threshold 75")

    provenance = page.metadata.get("verified_live_research")
    if provenance is not None and not isinstance(provenance, Mapping):
        raise ResearchStudioError("Verified live research provenance must be an object")
    if isinstance(provenance, Mapping):
        status = "verified-live"

    return ResearchBrief(
        page_slug=page.slug,
        market=_require_text(page.metadata.get("market", "iran"), "market"),
        language=page.lang,
        primary_query=intelligence.query.primary_query,
        supporting_queries=intelligence.query.supporting_queries,
        audience_hypotheses=audience_hypotheses,
        sources=sources,
        pattern_candidates=patterns,
        evidence_score=score,
        evidence_status=status,
        limitations=limitations,
        provenance=dict(provenance) if isinstance(provenance, Mapping) else None,
    )

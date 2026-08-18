"""RUOS Content Intelligence research collector primitives.

Collectors return normalized evidence only. They do not invent metrics and do not
classify an item as a winner. Pattern mining happens downstream after validation.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from hashlib import sha256
from typing import Any, Iterable, Protocol
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

TRACKING_PARAMS = {"utm_source", "utm_medium", "utm_campaign", "utm_term", "utm_content", "fbclid", "gclid"}


def canonicalize_url(url: str | None) -> str | None:
    if not url:
        return None
    parts = urlsplit(url.strip())
    query = [(k, v) for k, v in parse_qsl(parts.query, keep_blank_values=True) if k.lower() not in TRACKING_PARAMS]
    path = parts.path.rstrip("/") or "/"
    return urlunsplit((parts.scheme.lower(), parts.netloc.lower(), path, urlencode(query), ""))


def evidence_fingerprint(project_id: str, source: str, canonical_url: str | None, topic: str, title: str | None = None) -> str:
    raw = "|".join([project_id.strip().lower(), source.strip().lower(), canonical_url or "", topic.strip().lower(), (title or "").strip().lower()])
    return sha256(raw.encode("utf-8")).hexdigest()


@dataclass(slots=True)
class ResearchEvidence:
    project_id: str
    source: str
    source_class: str
    topic: str
    confidence: float
    observed_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    canonical_url: str | None = None
    source_identifier: str | None = None
    title: str | None = None
    published_at: str | None = None
    language: str | None = None
    geography: str | None = None
    query: str | None = None
    intent: str | None = None
    funnel_stage: str | None = None
    pain: str | None = None
    question: str | None = None
    objection: str | None = None
    hook: str | None = None
    format: str | None = None
    angle: str | None = None
    visible_metrics: dict[str, int | float | None] = field(default_factory=dict)
    outlier_ratio: float | None = None
    evidence_summary: str | None = None
    commercial_relevance: float | None = None
    corroboration_status: str = "single_source"
    evidence_ids: list[str] = field(default_factory=list)

    def normalize(self) -> "ResearchEvidence":
        self.canonical_url = canonicalize_url(self.canonical_url)
        self.confidence = max(0.0, min(1.0, float(self.confidence)))
        if self.commercial_relevance is not None:
            self.commercial_relevance = max(0.0, min(10.0, float(self.commercial_relevance)))
        return self

    @property
    def fingerprint(self) -> str:
        return evidence_fingerprint(self.project_id, self.source, self.canonical_url, self.topic, self.title)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self.normalize())


class ResearchCollector(Protocol):
    source: str
    source_class: str

    def collect(self, *, project_id: str, queries: Iterable[str]) -> list[ResearchEvidence]: ...


class SearchCollectorAdapter:
    source = "google_search"
    source_class = "search"

    @staticmethod
    def from_web_result(*, project_id: str, query: str, title: str, url: str, summary: str, language: str = "fa", confidence: float = 0.7) -> ResearchEvidence:
        return ResearchEvidence(project_id=project_id, source=SearchCollectorAdapter.source, source_class=SearchCollectorAdapter.source_class, topic=query, query=query, title=title, canonical_url=url, evidence_summary=summary, language=language, confidence=confidence)


class RedditCollectorAdapter:
    source = "reddit"
    source_class = "community"

    @staticmethod
    def from_discussion(*, project_id: str, topic: str, title: str, url: str, summary: str, question: str | None = None, pain: str | None = None, confidence: float = 0.65) -> ResearchEvidence:
        return ResearchEvidence(project_id=project_id, source=RedditCollectorAdapter.source, source_class=RedditCollectorAdapter.source_class, topic=topic, title=title, canonical_url=url, evidence_summary=summary, question=question, pain=pain, language="en", confidence=confidence, corroboration_status="hypothesis_only")


class YouTubeCollectorAdapter:
    source = "youtube"
    source_class = "competitive"

    @staticmethod
    def from_public_video(*, project_id: str, topic: str, title: str, url: str, summary: str, visible_metrics: dict[str, int | float | None] | None = None, confidence: float = 0.65) -> ResearchEvidence:
        return ResearchEvidence(project_id=project_id, source=YouTubeCollectorAdapter.source, source_class=YouTubeCollectorAdapter.source_class, topic=topic, title=title, canonical_url=url, evidence_summary=summary, visible_metrics=visible_metrics or {}, confidence=confidence)


def deduplicate(items: Iterable[ResearchEvidence]) -> list[ResearchEvidence]:
    seen: set[str] = set()
    output: list[ResearchEvidence] = []
    for item in items:
        item.normalize()
        if item.fingerprint in seen:
            continue
        seen.add(item.fingerprint)
        output.append(item)
    return output

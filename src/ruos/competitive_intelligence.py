from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from urllib.parse import urlparse

from .models import PageSpec
from .research_studio import ResearchBrief


class CompetitiveIntelligenceError(ValueError):
    """Raised when competitor evidence is insufficient or inconsistent."""


@dataclass(frozen=True)
class CompetitiveSignal:
    source_id: str
    market: str
    signal_type: str
    observation: str
    implication: str

    def payload(self) -> dict[str, str]:
        return {
            "source_id": self.source_id,
            "market": self.market,
            "signal_type": self.signal_type,
            "observation": self.observation,
            "implication": self.implication,
        }


@dataclass(frozen=True)
class DiscoveredCompetitor:
    rank: int
    title: str
    url: str
    domain: str
    snippet: str

    def payload(self) -> dict[str, object]:
        return {
            "rank": self.rank,
            "title": self.title,
            "url": self.url,
            "domain": self.domain,
            "snippet": self.snippet,
        }


@dataclass(frozen=True)
class CompetitorPageEvidence:
    rank: int
    requested_url: str
    final_url: str
    domain: str
    fetched_at: str
    content_sha256: str
    title: str
    excerpt: str
    byte_length: int

    def payload(self) -> dict[str, object]:
        return {
            "rank": self.rank,
            "requested_url": self.requested_url,
            "final_url": self.final_url,
            "domain": self.domain,
            "fetched_at": self.fetched_at,
            "content_sha256": self.content_sha256,
            "title": self.title,
            "excerpt": self.excerpt,
            "byte_length": self.byte_length,
        }


@dataclass(frozen=True)
class CompetitiveIntelligence:
    page_slug: str
    local_sources: tuple[str, ...]
    global_sources: tuple[str, ...]
    signals: tuple[CompetitiveSignal, ...]
    opportunity_gaps: tuple[str, ...]
    non_copying_policy: str
    discovery_provider: str = ""
    discovery_sha256: str = ""
    discovered_competitors: tuple[DiscoveredCompetitor, ...] = ()
    competitor_page_evidence: tuple[CompetitorPageEvidence, ...] = ()

    def payload(self) -> dict[str, object]:
        payload: dict[str, object] = {
            "page_slug": self.page_slug,
            "local_sources": list(self.local_sources),
            "global_sources": list(self.global_sources),
            "signals": [signal.payload() for signal in self.signals],
            "opportunity_gaps": list(self.opportunity_gaps),
            "non_copying_policy": self.non_copying_policy,
        }
        if self.discovery_provider:
            payload["discovery_provider"] = self.discovery_provider
            payload["discovery_sha256"] = self.discovery_sha256
            payload["discovered_competitors"] = [item.payload() for item in self.discovered_competitors]
        if self.competitor_page_evidence:
            payload["competitor_page_evidence"] = [item.payload() for item in self.competitor_page_evidence]
        return payload

    @property
    def sha256(self) -> str:
        canonical = json.dumps(self.payload(), ensure_ascii=False, sort_keys=True, separators=(",", ":"))
        return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def _parse_discovery(research: ResearchBrief) -> tuple[str, str, tuple[DiscoveredCompetitor, ...]]:
    provenance = research.provenance or {}
    raw = provenance.get("search_discovery")
    if not isinstance(raw, dict):
        return "", "", ()
    provider = str(raw.get("provider", "")).strip()
    sha256 = str(raw.get("sha256", "")).strip()
    rows = raw.get("results", [])
    if not provider or len(sha256) != 64 or not isinstance(rows, list):
        raise CompetitiveIntelligenceError("Verified search discovery provenance is incomplete")
    results: list[DiscoveredCompetitor] = []
    seen: set[str] = set()
    for index, item in enumerate(rows, start=1):
        if not isinstance(item, dict):
            raise CompetitiveIntelligenceError(f"Discovery result #{index} must be an object")
        rank = int(item.get("rank", 0))
        title = str(item.get("title", "")).strip()
        url = str(item.get("url", "")).strip()
        snippet = str(item.get("snippet", "")).strip()
        domain = (urlparse(url).hostname or "").lower()
        if rank != index or not title or not url.startswith("https://") or not domain:
            raise CompetitiveIntelligenceError(f"Discovery result #{index} is invalid")
        if url in seen:
            raise CompetitiveIntelligenceError("Discovery results contain duplicate URLs")
        seen.add(url)
        results.append(DiscoveredCompetitor(rank, title, url, domain, snippet))
    return provider, sha256, tuple(results)


def _parse_page_evidence(research: ResearchBrief) -> tuple[CompetitorPageEvidence, ...]:
    provenance = research.provenance or {}
    raw = provenance.get("competitor_page_evidence")
    if raw is None:
        return ()
    if not isinstance(raw, list):
        raise CompetitiveIntelligenceError("Competitor page evidence must be a list")
    evidence: list[CompetitorPageEvidence] = []
    seen: set[str] = set()
    for index, item in enumerate(raw, start=1):
        if not isinstance(item, dict):
            raise CompetitiveIntelligenceError(f"Competitor page evidence #{index} must be an object")
        requested_url = str(item.get("requested_url", "")).strip()
        final_url = str(item.get("final_url", "")).strip()
        domain = (urlparse(final_url).hostname or "").lower()
        content_sha256 = str(item.get("content_sha256", "")).strip()
        if not requested_url.startswith("https://") or not final_url.startswith("https://"):
            raise CompetitiveIntelligenceError("Competitor page evidence URLs must use HTTPS")
        if len(content_sha256) != 64 or not domain:
            raise CompetitiveIntelligenceError("Competitor page evidence is incomplete")
        if requested_url in seen:
            raise CompetitiveIntelligenceError("Competitor page evidence contains duplicate URLs")
        seen.add(requested_url)
        evidence.append(
            CompetitorPageEvidence(
                rank=int(item.get("rank", index)),
                requested_url=requested_url,
                final_url=final_url,
                domain=domain,
                fetched_at=str(item.get("fetched_at", "")).strip(),
                content_sha256=content_sha256,
                title=str(item.get("title", "")).strip(),
                excerpt=str(item.get("excerpt", "")).strip(),
                byte_length=int(item.get("byte_length", 0)),
            )
        )
    return tuple(evidence)


def build_competitive_intelligence(page: PageSpec, research: ResearchBrief) -> CompetitiveIntelligence:
    if page.slug != research.page_slug:
        raise CompetitiveIntelligenceError("Competitive research does not belong to this page")

    competitor_sources = tuple(source for source in research.sources if source.kind == "competitor")
    design_sources = tuple(source for source in research.sources if source.kind == "design-reference")
    if not competitor_sources:
        raise CompetitiveIntelligenceError("At least one competitor evidence source is required")
    if not design_sources:
        raise CompetitiveIntelligenceError("At least one global design reference is required")

    local = tuple(source.id for source in competitor_sources if source.market.casefold() in {"iran", "ایران"})
    global_refs = tuple(source.id for source in design_sources)
    if not local:
        raise CompetitiveIntelligenceError("Competitive intelligence requires an Iran-market source")

    provider, discovery_sha256, discovered = _parse_discovery(research)
    page_evidence = _parse_page_evidence(research)
    if page_evidence and discovered:
        discovered_urls = {item.url for item in discovered}
        if any(item.requested_url not in discovered_urls for item in page_evidence):
            raise CompetitiveIntelligenceError("Competitor page evidence is not traceable to verified discovery")

    signals: list[CompetitiveSignal] = []
    for source in competitor_sources:
        signals.append(CompetitiveSignal(source.id, source.market, "declared-market-source", source.notes, "Treat this as a declared research hypothesis until directly observed."))
    for source in design_sources:
        signals.append(CompetitiveSignal(source.id, source.market, "creative-reference", source.notes, "Extract principles only; reinterpret through brand, RTL and performance constraints."))
    for item in discovered:
        signals.append(CompetitiveSignal(f"search-result:{item.rank}", "iran", "observed-search-result", f"Rank {item.rank}: {item.title} — {item.domain}. Snippet: {item.snippet}", "Fetch and inspect the page before making claims about its content, UX or visual quality."))
    for item in page_evidence:
        signals.append(CompetitiveSignal(f"competitor-page:{item.rank}", "iran", "observed-page-content", f"Fetched {item.domain}; title: {item.title}; excerpt: {item.excerpt}", "Use only directly observed text and metadata; do not infer visual quality without rendered evidence."))

    gaps = (
        "ترکیب راهنمای تصمیم، مقایسه فنی و مسیر تجاری در یک روایت واحد",
        "توضیح روشن تفاوت خرید، اجاره و سرمایه‌گذاری بدون فشار فروش",
        "تجربه RTL خلاق با حفظ دسترسی مستقیم به اطلاعات و عملکرد موبایل",
    )
    return CompetitiveIntelligence(
        page.slug,
        local,
        global_refs,
        tuple(signals),
        gaps,
        "Use sources to derive principles and gaps; never copy layout, copywriting, code or branded assets.",
        provider,
        discovery_sha256,
        discovered,
        page_evidence,
    )

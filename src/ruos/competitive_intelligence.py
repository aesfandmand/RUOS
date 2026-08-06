from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from typing import Mapping, Sequence
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
class CompetitiveIntelligence:
    page_slug: str
    local_sources: tuple[str, ...]
    global_sources: tuple[str, ...]
    signals: tuple[CompetitiveSignal, ...]
    discovered_competitors: tuple[DiscoveredCompetitor, ...]
    discovery_provider: str | None
    discovery_sha256: str | None
    opportunity_gaps: tuple[str, ...]
    non_copying_policy: str

    def payload(self) -> dict[str, object]:
        return {
            "page_slug": self.page_slug,
            "local_sources": list(self.local_sources),
            "global_sources": list(self.global_sources),
            "signals": [signal.payload() for signal in self.signals],
            "discovered_competitors": [item.payload() for item in self.discovered_competitors],
            "discovery_provider": self.discovery_provider,
            "discovery_sha256": self.discovery_sha256,
            "opportunity_gaps": list(self.opportunity_gaps),
            "non_copying_policy": self.non_copying_policy,
        }

    @property
    def sha256(self) -> str:
        canonical = json.dumps(self.payload(), ensure_ascii=False, sort_keys=True, separators=(",", ":"))
        return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def _discovery_payload(research: ResearchBrief) -> Mapping[str, object] | None:
    provenance = research.provenance
    if not isinstance(provenance, Mapping):
        return None
    discovery = provenance.get("search_discovery")
    return discovery if isinstance(discovery, Mapping) else None


def _parse_discovered_competitors(raw: object) -> tuple[DiscoveredCompetitor, ...]:
    if raw is None:
        return ()
    if not isinstance(raw, Sequence) or isinstance(raw, (str, bytes)):
        raise CompetitiveIntelligenceError("Verified discovery results must be a list")
    competitors: list[DiscoveredCompetitor] = []
    seen_urls: set[str] = set()
    for index, item in enumerate(raw, start=1):
        if not isinstance(item, Mapping):
            raise CompetitiveIntelligenceError(f"Discovery result #{index} must be an object")
        try:
            rank = int(item.get("rank", index))
        except (TypeError, ValueError) as exc:
            raise CompetitiveIntelligenceError(f"Discovery result #{index} has an invalid rank") from exc
        title = str(item.get("title", "")).strip()
        url = str(item.get("url", "")).strip()
        snippet = str(item.get("snippet", "")).strip()
        domain = (urlparse(url).hostname or "").lower()
        if rank != index:
            raise CompetitiveIntelligenceError("Discovery result ranks must be contiguous")
        if not title or not url.startswith("https://") or not domain:
            raise CompetitiveIntelligenceError(f"Discovery result #{index} is incomplete")
        if url in seen_urls:
            raise CompetitiveIntelligenceError("Discovery results contain duplicate URLs")
        seen_urls.add(url)
        competitors.append(DiscoveredCompetitor(rank, title, url, domain, snippet))
    return tuple(competitors)


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

    signals: list[CompetitiveSignal] = []
    for source in competitor_sources:
        signals.append(
            CompetitiveSignal(
                source_id=source.id,
                market=source.market,
                signal_type="declared-market-source",
                observation=source.notes,
                implication="Treat this as a declared research hypothesis until corroborated by fetched evidence.",
            )
        )
    for source in design_sources:
        signals.append(
            CompetitiveSignal(
                source_id=source.id,
                market=source.market,
                signal_type="creative-reference",
                observation=source.notes,
                implication="Extract the design principle, then reinterpret it through brand, RTL and performance constraints.",
            )
        )

    discovery = _discovery_payload(research)
    discovered = _parse_discovered_competitors(discovery.get("results") if discovery else None)
    provider = str(discovery.get("provider", "")).strip() if discovery else ""
    discovery_sha = str(discovery.get("sha256", "")).strip() if discovery else ""
    if discovery is not None:
        if not provider or len(discovery_sha) != 64:
            raise CompetitiveIntelligenceError("Verified discovery provenance is incomplete")
        for item in discovered:
            signals.append(
                CompetitiveSignal(
                    source_id=f"search-discovery:{provider}:{item.rank}",
                    market=research.market,
                    signal_type="observed-search-result",
                    observation=f"Rank {item.rank}: {item.title} — {item.snippet}".strip(" —"),
                    implication="Use this observed result to map visible SERP framing; fetch the page before making content or UX claims about it.",
                )
            )

    gaps = (
        "ترکیب راهنمای تصمیم، مقایسه فنی و مسیر تجاری در یک روایت واحد",
        "توضیح روشن تفاوت خرید، اجاره و سرمایه‌گذاری بدون فشار فروش",
        "تجربه RTL خلاق با حفظ دسترسی مستقیم به اطلاعات و عملکرد موبایل",
    )
    return CompetitiveIntelligence(
        page_slug=page.slug,
        local_sources=local,
        global_sources=global_refs,
        signals=tuple(signals),
        discovered_competitors=discovered,
        discovery_provider=provider or None,
        discovery_sha256=discovery_sha or None,
        opportunity_gaps=gaps,
        non_copying_policy="Use sources to derive principles and gaps; never copy layout, copywriting, code or branded assets.",
    )

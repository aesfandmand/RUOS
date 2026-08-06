from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass

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
class CompetitiveIntelligence:
    page_slug: str
    local_sources: tuple[str, ...]
    global_sources: tuple[str, ...]
    signals: tuple[CompetitiveSignal, ...]
    opportunity_gaps: tuple[str, ...]
    non_copying_policy: str

    def payload(self) -> dict[str, object]:
        return {
            "page_slug": self.page_slug,
            "local_sources": list(self.local_sources),
            "global_sources": list(self.global_sources),
            "signals": [signal.payload() for signal in self.signals],
            "opportunity_gaps": list(self.opportunity_gaps),
            "non_copying_policy": self.non_copying_policy,
        }

    @property
    def sha256(self) -> str:
        canonical = json.dumps(self.payload(), ensure_ascii=False, sort_keys=True, separators=(",", ":"))
        return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


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
                signal_type="market-structure",
                observation=source.notes,
                implication="Page structure must answer the visible market intent while exposing a clearer decision path.",
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
        opportunity_gaps=gaps,
        non_copying_policy="Use sources to derive principles and gaps; never copy layout, copywriting, code or branded assets.",
    )

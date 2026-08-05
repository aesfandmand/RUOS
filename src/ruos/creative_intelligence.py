from __future__ import annotations

from dataclasses import dataclass
from types import MappingProxyType
from typing import Mapping

from .content_composer import ContentPlan
from .models import PageSpec


class CreativeIntelligenceError(ValueError):
    """Raised when strategy signals cannot form a production intelligence plan."""


@dataclass(frozen=True)
class QueryIntent:
    primary_query: str
    supporting_queries: tuple[str, ...]
    search_intent: str
    journey_stage: str


@dataclass(frozen=True)
class SalesStrategy:
    conversion_goal: str
    value_proposition: str
    friction_policy: str
    proof_requirements: tuple[str, ...]
    cta_sequence: tuple[str, ...]


@dataclass(frozen=True)
class SemanticStrategy:
    primary_entity: str
    entities: tuple[str, ...]
    schema_types: tuple[str, ...]
    answer_targets: tuple[str, ...]
    ai_summary: str


@dataclass(frozen=True)
class CreativeStrategy:
    emotional_curve: tuple[str, ...]
    narrative_model: str
    persuasion_principles: tuple[str, ...]
    visual_direction: str
    attributes: Mapping[str, str]


@dataclass(frozen=True)
class CreativeIntelligencePlan:
    page_slug: str
    query: QueryIntent
    sales: SalesStrategy
    semantic: SemanticStrategy
    creative: CreativeStrategy

    def fingerprint_payload(self) -> tuple[tuple[str, object], ...]:
        return (
            ("page_slug", self.page_slug),
            ("query", self.query),
            ("sales", self.sales),
            ("semantic", self.semantic),
            ("creative", self.creative),
        )


def _freeze(values: Mapping[str, str]) -> Mapping[str, str]:
    return MappingProxyType(dict(values))


def _normalize_query(value: str) -> str:
    return " ".join(value.replace("-", " ").split()).strip()


def build_creative_intelligence(page: PageSpec, content: ContentPlan) -> CreativeIntelligencePlan:
    pillar = _normalize_query(str(page.metadata.get("pillar", page.slug)))
    journey = str(page.metadata.get("journey", "discover-compare-decide"))
    conversion = str(page.metadata.get("primary_conversion", "qualified-conversation"))
    if not pillar:
        raise CreativeIntelligenceError("A primary query or pillar is required")

    knowledge_entities = tuple(
        sorted({entity for block in content.blocks for entity in block.entities if entity})
    )
    if not knowledge_entities:
        raise CreativeIntelligenceError("Creative intelligence requires at least one explicit entity")

    supporting = tuple(
        dict.fromkeys(
            [
                f"انواع {pillar}",
                f"راهنمای انتخاب {pillar}",
                f"خرید {pillar}",
                f"سرمایه گذاری در {pillar}",
                *knowledge_entities,
            ]
        )
    )
    primary_query = pillar
    search_intent = "commercial-investigation"
    journey_stage = "discover-compare-route" if "discover" in journey else journey

    proof_requirements = (
        "نمونه‌کار واقعی",
        "معیارهای فنی قابل مقایسه",
        "شفافیت مسیر خرید یا سرمایه‌گذاری",
    )
    cta_sequence = tuple(
        block.cta_label for block in content.blocks if block.cta_label
    )
    if not cta_sequence:
        raise CreativeIntelligenceError("Sales strategy requires at least one contextual CTA")

    answer_targets = (
        f"{pillar} چیست؟",
        f"چه انواعی از {pillar} وجود دارد؟",
        f"چطور {pillar} مناسب را انتخاب کنیم؟",
        f"مسیر خرید، اجاره یا سرمایه‌گذاری در {pillar} چیست؟",
    )
    ai_summary = (
        f"این صفحه مرجع تصمیم‌گیری درباره {pillar} است؛ انواع، معیارهای انتخاب و مسیرهای "
        "خرید، اجاره یا سرمایه‌گذاری را به‌صورت ساختاریافته توضیح می‌دهد."
    )

    emotional_curve = ("کنجکاوی", "درک", "اعتماد", "وضوح تصمیم", "اقدام")
    if len(content.blocks) != len(emotional_curve):
        raise CreativeIntelligenceError(
            "The current narrative model requires five aligned content beats"
        )

    return CreativeIntelligencePlan(
        page_slug=page.slug,
        query=QueryIntent(
            primary_query=primary_query,
            supporting_queries=supporting,
            search_intent=search_intent,
            journey_stage=journey_stage,
        ),
        sales=SalesStrategy(
            conversion_goal=conversion,
            value_proposition=page.description.strip(),
            friction_policy="phone-first-minimal-form",
            proof_requirements=proof_requirements,
            cta_sequence=cta_sequence,
        ),
        semantic=SemanticStrategy(
            primary_entity=primary_query,
            entities=knowledge_entities,
            schema_types=("WebPage", "ItemList", "FAQPage", "BreadcrumbList"),
            answer_targets=answer_targets,
            ai_summary=ai_summary,
        ),
        creative=CreativeStrategy(
            emotional_curve=emotional_curve,
            narrative_model="customer-as-hero-guide-led-decision",
            persuasion_principles=(
                "clarity-before-persuasion",
                "specificity",
                "progressive-commitment",
                "ethical-risk-reversal",
            ),
            visual_direction=page.visual_profile,
            attributes=_freeze(
                {
                    "query_alignment": "explicit",
                    "sales_orientation": "consultative",
                    "seo_depth": "pillar-cluster-ready",
                    "ai_readiness": "entity-answer-structured",
                }
            ),
        ),
    )

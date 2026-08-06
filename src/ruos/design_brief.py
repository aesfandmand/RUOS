from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass

from .competitive_intelligence import CompetitiveIntelligence
from .models import PageSpec
from .pattern_intelligence import PatternIntelligence
from .query_intelligence import QueryIntelligence
from .research_studio import ResearchBrief
from .voice_studio import VoiceDecision


class DesignBriefError(ValueError):
    """Raised when research cannot be compiled into an actionable design brief."""


@dataclass(frozen=True)
class DesignBrief:
    page_slug: str
    objective: str
    audience: tuple[str, ...]
    primary_query: str
    conversion_goal: str
    desired_emotions: tuple[str, ...]
    reading_strategy: str
    visual_strategy: str
    interaction_strategy: str
    selected_patterns: tuple[str, ...]
    opportunity_gaps: tuple[str, ...]
    voice_id: str
    constraints: tuple[str, ...]
    source_hashes: dict[str, str]

    def payload(self) -> dict[str, object]:
        return {
            "page_slug": self.page_slug,
            "objective": self.objective,
            "audience": list(self.audience),
            "primary_query": self.primary_query,
            "conversion_goal": self.conversion_goal,
            "desired_emotions": list(self.desired_emotions),
            "reading_strategy": self.reading_strategy,
            "visual_strategy": self.visual_strategy,
            "interaction_strategy": self.interaction_strategy,
            "selected_patterns": list(self.selected_patterns),
            "opportunity_gaps": list(self.opportunity_gaps),
            "voice_id": self.voice_id,
            "constraints": list(self.constraints),
            "source_hashes": dict(sorted(self.source_hashes.items())),
        }

    @property
    def sha256(self) -> str:
        canonical = json.dumps(self.payload(), ensure_ascii=False, sort_keys=True, separators=(",", ":"))
        return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def compile_design_brief(
    page: PageSpec,
    research: ResearchBrief,
    queries: QueryIntelligence,
    competition: CompetitiveIntelligence,
    patterns: PatternIntelligence,
    voice: VoiceDecision,
) -> DesignBrief:
    if len({page.slug, research.page_slug, queries.page_slug, competition.page_slug, patterns.page_slug, voice.page_slug}) != 1:
        raise DesignBriefError("Design brief inputs do not belong to the same page")
    if voice.approval_status != "approved":
        raise DesignBriefError("Design brief requires an approved content voice")
    if research.evidence_status != "ready":
        raise DesignBriefError("Design brief requires production-ready research")

    selected_ids = tuple(item.id for item in patterns.selected)
    constraints = tuple(
        sorted(
            {
                constraint
                for item in patterns.selected
                for constraint in item.constraints
            }
            | {
                "Responsive single-codebase implementation",
                "Keyboard-operable interactions",
                "Reduced-motion equivalent experience",
                "No unverified search-volume claims",
                "No copied layouts, code, copy or branded assets",
            }
        )
    )
    if not selected_ids:
        raise DesignBriefError("Design brief requires selected patterns")

    return DesignBrief(
        page_slug=page.slug,
        objective=str(page.metadata.get("journey", "discover-understand-decide-act")),
        audience=research.audience_hypotheses,
        primary_query=queries.primary_query,
        conversion_goal=str(page.metadata.get("primary_conversion", "qualified-action")),
        desired_emotions=("کنجکاوی", "وضوح", "اعتماد", "آمادگی برای تصمیم"),
        reading_strategy="Answer-first Persian editorial flow with chaptered disclosure and concise decision summaries.",
        visual_strategy="Create a distinctive RTL visual story with asymmetric rhythm, strong hierarchy and brand-specific motion rather than repeated cards.",
        interaction_strategy="Use progressive, keyboard-accessible decision interactions that clarify commercial routes without hiding essential information.",
        selected_patterns=selected_ids,
        opportunity_gaps=competition.opportunity_gaps,
        voice_id=voice.approved_voice_id,
        constraints=constraints,
        source_hashes={
            "research": research.sha256,
            "query_intelligence": queries.sha256,
            "competitive_intelligence": competition.sha256,
            "pattern_intelligence": patterns.sha256,
            "voice": voice.sha256,
        },
    )

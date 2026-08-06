from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass

from .art_director import ArtDirectionDecision
from .component_resolver import ComponentPlan
from .models import PageSpec
from .pattern_resolver import PatternPlan


class UXDirectorError(ValueError):
    """Raised when a coherent user journey cannot be directed."""


@dataclass(frozen=True)
class UXStage:
    section_id: str
    chapter: int
    user_question: str
    desired_state: str
    attention_goal: str
    trust_goal: str
    decision_goal: str
    interaction_mode: str
    exit_condition: str

    def payload(self) -> dict[str, object]:
        return {
            "section_id": self.section_id,
            "chapter": self.chapter,
            "user_question": self.user_question,
            "desired_state": self.desired_state,
            "attention_goal": self.attention_goal,
            "trust_goal": self.trust_goal,
            "decision_goal": self.decision_goal,
            "interaction_mode": self.interaction_mode,
            "exit_condition": self.exit_condition,
        }


@dataclass(frozen=True)
class UXDirectionDecision:
    page_slug: str
    journey_model: str
    stages: tuple[UXStage, ...]
    reading_contract: tuple[str, ...]
    trust_sequence: tuple[str, ...]
    conversion_sequence: tuple[str, ...]
    mobile_behavior: tuple[str, ...]
    accessibility_contract: tuple[str, ...]
    art_decision_sha256: str

    def payload(self) -> dict[str, object]:
        return {
            "page_slug": self.page_slug,
            "journey_model": self.journey_model,
            "stages": [stage.payload() for stage in self.stages],
            "reading_contract": list(self.reading_contract),
            "trust_sequence": list(self.trust_sequence),
            "conversion_sequence": list(self.conversion_sequence),
            "mobile_behavior": list(self.mobile_behavior),
            "accessibility_contract": list(self.accessibility_contract),
            "art_decision_sha256": self.art_decision_sha256,
        }

    @property
    def sha256(self) -> str:
        canonical = json.dumps(self.payload(), ensure_ascii=False, sort_keys=True, separators=(",", ":"))
        return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


_STAGE_RULES = {
    "hero": (
        "آیا این صفحه مسئله من را می‌فهمد؟",
        "curious-and-oriented",
        "establish scale and relevance without delaying the proposition",
        "signal expertise through a precise promise rather than claims",
        "choose to continue into comparison",
        "direct-scroll with one contextual CTA",
        "the user understands what will be compared and why it matters",
    ),
    "story": (
        "چرا انتخاب سازه فقط مقایسه ظاهر و قیمت نیست؟",
        "reflective-and-convinced",
        "slow the pace for one causal explanation",
        "connect engineering, visibility and commercial outcome",
        "accept the decision framework",
        "editorial reading pause",
        "the user understands the cause-and-effect model",
    ),
    "knowledge": (
        "چه گزینه‌هایی دارم و تفاوت واقعی آن‌ها چیست؟",
        "informed-and-comparing",
        "support scanning first and deeper inspection second",
        "show practical constraints and use cases consistently",
        "reduce the option set to relevant families",
        "progressive comparison with semantic list fallback",
        "the user can name at least one relevant structure family",
    ),
    "interaction": (
        "کدام مسیر برای شرایط من مناسب‌تر است؟",
        "active-and-deciding",
        "focus attention on one choice at a time",
        "make criteria, state and consequences visible",
        "select a commercial route without hidden commitment",
        "keyboard-operable guided decision path",
        "a route is selected and its rationale is understood",
    ),
    "conversion": (
        "قدم بعدی کم‌ریسک و منطقی چیست؟",
        "confident-and-ready",
        "present one primary action after proof",
        "state what will happen after contact and avoid false urgency",
        "start a qualified conversation",
        "single high-contrast CTA with supporting expectation copy",
        "the user knows the next step, effort and expected outcome",
    ),
}


def direct_ux(
    page: PageSpec,
    components: ComponentPlan,
    patterns: PatternPlan,
    art: ArtDirectionDecision,
) -> UXDirectionDecision:
    if len({page.slug, components.page_slug, patterns.page_slug, art.page_slug}) != 1:
        raise UXDirectorError("UX direction inputs do not belong to the same page")
    if len(page.sections) != len(components.components) or len(page.sections) != len(patterns.sections):
        raise UXDirectorError("UX direction requires one component and pattern per section")

    stages: list[UXStage] = []
    for chapter, section in enumerate(page.sections, start=1):
        if section.kind not in _STAGE_RULES:
            raise UXDirectorError(f"No UX direction rule for section kind '{section.kind}'")
        component = components.for_section(section.id)
        pattern = patterns.for_section(section.id)
        if component.section_id != pattern.section_id:
            raise UXDirectorError(f"Component and pattern diverge for section '{section.id}'")
        question, state, attention, trust, decision, interaction, exit_condition = _STAGE_RULES[section.kind]
        stages.append(
            UXStage(
                section_id=section.id,
                chapter=chapter,
                user_question=question,
                desired_state=state,
                attention_goal=attention,
                trust_goal=trust,
                decision_goal=decision,
                interaction_mode=interaction,
                exit_condition=exit_condition,
            )
        )

    if page.sections[0].kind != "hero" or page.sections[-1].kind != "conversion":
        raise UXDirectorError("UX journey must open with hero and close with conversion")

    return UXDirectionDecision(
        page_slug=page.slug,
        journey_model="orient-understand-compare-decide-act",
        stages=tuple(stages),
        reading_contract=(
            "answer the section question before expanding detail",
            "alternate dense evidence with deliberate visual pauses",
            "preserve direct access to essential information without forced interaction",
            "keep Persian line length and heading transitions readable",
        ),
        trust_sequence=(
            "relevance through a precise opening proposition",
            "competence through causal explanation",
            "credibility through comparable criteria and constraints",
            "control through transparent interaction state",
            "commitment clarity before contact",
        ),
        conversion_sequence=(
            "contextual exploration CTA in the hero",
            "no disruptive CTA during the explanatory story",
            "route selection after comparison",
            "qualified-conversation CTA only after decision support",
        ),
        mobile_behavior=(
            "preserve the same narrative order and hero-first entry",
            "convert pinned or horizontal scenes into touch-safe snap or linear chapters",
            "keep bottom navigation outside content reading order",
            "never hide essential comparison data behind hover",
            "maintain visible progress and clear return paths",
        ),
        accessibility_contract=(
            "all controls keyboard operable with visible focus",
            "selection state announced programmatically",
            "motion never carries unique information",
            "reduced-motion mode preserves narrative order and state feedback",
            "touch targets and contrast meet production accessibility thresholds",
        ),
        art_decision_sha256=art.sha256,
    )

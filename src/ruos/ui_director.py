from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass

from .art_director import ArtDirectionDecision
from .component_resolver import ComponentPlan
from .models import PageSpec
from .ux_director import UXDirectionDecision


class UIDirectorError(ValueError):
    """Raised when a coherent production UI system cannot be directed."""


@dataclass(frozen=True)
class UISectionDecision:
    section_id: str
    chapter: int
    composition: str
    hierarchy: tuple[str, ...]
    content_density: str
    media_role: str
    interaction_state: str
    desktop_behavior: str
    mobile_behavior: str
    accessibility_requirements: tuple[str, ...]

    def payload(self) -> dict[str, object]:
        return {
            "section_id": self.section_id,
            "chapter": self.chapter,
            "composition": self.composition,
            "hierarchy": list(self.hierarchy),
            "content_density": self.content_density,
            "media_role": self.media_role,
            "interaction_state": self.interaction_state,
            "desktop_behavior": self.desktop_behavior,
            "mobile_behavior": self.mobile_behavior,
            "accessibility_requirements": list(self.accessibility_requirements),
        }


@dataclass(frozen=True)
class UIDirectionDecision:
    page_slug: str
    system_model: str
    sections: tuple[UISectionDecision, ...]
    component_rules: tuple[str, ...]
    responsive_rules: tuple[str, ...]
    anti_patterns: tuple[str, ...]
    art_decision_sha256: str
    ux_decision_sha256: str

    def payload(self) -> dict[str, object]:
        return {
            "page_slug": self.page_slug,
            "system_model": self.system_model,
            "sections": [section.payload() for section in self.sections],
            "component_rules": list(self.component_rules),
            "responsive_rules": list(self.responsive_rules),
            "anti_patterns": list(self.anti_patterns),
            "art_decision_sha256": self.art_decision_sha256,
            "ux_decision_sha256": self.ux_decision_sha256,
        }

    @property
    def sha256(self) -> str:
        canonical = json.dumps(self.payload(), ensure_ascii=False, sort_keys=True, separators=(",", ":"))
        return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


_SECTION_UI = {
    "hero": (
        "asymmetric monumental split with structural media occupying the dominant field",
        ("eyebrow", "single decisive heading", "short proposition", "primary CTA", "scroll cue"),
        "low-copy-high-impact",
        "establish scale, material and spatial depth",
        "idle-to-exploration",
        "full-viewport composition with controlled depth and no competing panels",
        "hero remains first; media becomes contained and copy stays readable without horizontal overflow",
    ),
    "story": (
        "editorial offset with one oversized statement and one supporting visual axis",
        ("chapter marker", "causal heading", "reading copy", "visual pause"),
        "measured-editorial",
        "support the causal explanation rather than decorate it",
        "reading-focus",
        "wide whitespace and restrained line length; no card treatment",
        "single-column reading flow with preserved pause and clear chapter separation",
    ),
    "knowledge": (
        "progressive comparison field with one active family and visible alternatives",
        ("comparison heading", "criteria index", "active structure", "technical details", "alternative options"),
        "scan-then-deepen",
        "show structural families, context and technical distinctions",
        "browse-compare-focus",
        "asymmetric comparison canvas; alternatives remain visible without equal-weight card repetition",
        "touch-safe snap or linear chapters with all details present in semantic order",
    ),
    "interaction": (
        "focused decision console with one question and one state transition at a time",
        ("decision prompt", "criteria controls", "current state", "recommendation rationale", "route action"),
        "focused-progressive",
        "use diagrams or contextual previews only when they clarify the selected state",
        "unselected-selected-confirmed",
        "sticky console allowed only while controls and result remain fully operable",
        "linear step flow with persistent state, large targets and no hover dependency",
    ),
    "conversion": (
        "high-contrast closing stage with one dominant action and explicit expectation copy",
        ("closing claim", "next-step explanation", "primary CTA", "supporting reassurance"),
        "minimal-decisive",
        "reinforce confidence; never introduce unrelated imagery",
        "ready-to-act",
        "large closing field after proof with no competing CTA cluster",
        "compact closing stage above bottom navigation with comfortable thumb reach",
    ),
}


def direct_ui(
    page: PageSpec,
    components: ComponentPlan,
    art: ArtDirectionDecision,
    ux: UXDirectionDecision,
) -> UIDirectionDecision:
    if len({page.slug, components.page_slug, art.page_slug, ux.page_slug}) != 1:
        raise UIDirectorError("UI direction inputs do not belong to the same page")
    if len(page.sections) != len(components.components) or len(page.sections) != len(ux.stages):
        raise UIDirectorError("UI direction requires one component and UX stage per section")

    ux_by_section = {stage.section_id: stage for stage in ux.stages}
    decisions: list[UISectionDecision] = []
    for chapter, section in enumerate(page.sections, start=1):
        component = components.for_section(section.id)
        if section.id not in ux_by_section:
            raise UIDirectorError(f"Missing UX stage for section '{section.id}'")
        if section.kind not in _SECTION_UI:
            raise UIDirectorError(f"No UI direction rule for section kind '{section.kind}'")
        composition, hierarchy, density, media, state, desktop, mobile = _SECTION_UI[section.kind]
        decisions.append(
            UISectionDecision(
                section_id=section.id,
                chapter=chapter,
                composition=composition,
                hierarchy=hierarchy,
                content_density=density,
                media_role=media,
                interaction_state=state,
                desktop_behavior=desktop,
                mobile_behavior=mobile,
                accessibility_requirements=(
                    "semantic source order matches visual reading order",
                    "visible focus and keyboard parity for every interactive state",
                    "text contrast and touch targets meet production thresholds",
                    "motion and imagery never carry unique required information",
                    f"component-capabilities:{','.join(component.capabilities)}",
                ),
            )
        )

    return UIDirectionDecision(
        page_slug=page.slug,
        system_model="art-led-ux-governed-responsive-interface",
        sections=tuple(decisions),
        component_rules=(
            "each section must express one dominant visual idea",
            "use composition changes to mark narrative chapters",
            "reuse tokens and behavior contracts, not identical visible layouts",
            "technical information remains structured and extractable",
            "CTA hierarchy follows the approved UX conversion sequence",
        ),
        responsive_rules=(
            "desktop asymmetry translates to explicit mobile order, never accidental stacking",
            "mobile hero remains the first meaningful visual state",
            "pinned and horizontal scenes require touch-safe linear or snap equivalents",
            "bottom navigation must not obscure content or primary actions",
            "Persian measure, line height and heading scale remain readable at every viewport",
        ),
        anti_patterns=(
            "repetitive equal-weight card wall",
            "generic dashboard treatment for narrative content",
            "decorative glass panels without information purpose",
            "desktop-only composition without mobile equivalent",
            "hover-only disclosure",
            "multiple competing primary CTAs",
        ),
        art_decision_sha256=art.sha256,
        ux_decision_sha256=ux.sha256,
    )

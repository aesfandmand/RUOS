from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping, Sequence

from .content_composer import ContentPlan
from .creative_intelligence import CreativeIntelligencePlan
from .models import PageSpec
from .motion_composer import MotionPlan
from .pattern_resolver import PatternPlan


APPROVED_REFERENCES: tuple[dict[str, str], ...] = (
    {
        "name": "Fort Vega",
        "url": "https://www.awwwards.com/inspiration/website-scroll-fort-vega",
        "principle": "scroll-led spatial choreography and controlled depth",
        "translation": "Use scroll to reveal hierarchy and spatial relationships only where it improves comprehension.",
    },
    {
        "name": "Sky Clinics",
        "url": "https://www.awwwards.com/sites/sky-clinics",
        "principle": "cinematic scroll-driven storytelling",
        "translation": "Use cinematic pacing to move the user through a clear decision sequence rather than decorative scenes.",
    },
    {
        "name": "Bucks Sauce",
        "url": "https://www.awwwards.com/sites/bucks-sauce",
        "principle": "bold product presentation and animated browsing systems",
        "translation": "Use strong product hierarchy, expressive navigation and motion while preserving task clarity.",
    },
    {
        "name": "NRG Build Your Data Center",
        "url": "https://www.awwwards.com/sites/nrg-build-your-data-center",
        "principle": "progressive system construction, nodes and staged technical reveal",
        "translation": "For structure/catalog pages, progressively assemble the anatomy, options and relationships of the advertising structure.",
    },
    {
        "name": "Oryzo AI",
        "url": "https://www.awwwards.com/sites/oryzo-ai",
        "principle": "presentation-grade transitions with 2D/3D continuity",
        "translation": "Use a coherent reveal and transition language across chapters instead of disconnected section animations.",
    },
    {
        "name": "Xurya Manufacture",
        "url": "https://dribbble.com/shots/24874505-Xurya-Manufacture-Landing-Page",
        "principle": "industrial manufacturing visual language",
        "translation": "Express material, engineering and production credibility through industrial composition and technical detail.",
    },
    {
        "name": "Construction Insurtech B2B",
        "url": "https://dribbble.com/shots/27435782-Construction-Insurtech-B2B-Web-Design-SaaS-Landing-Page-UI",
        "principle": "architectural grid and modular B2B clarity",
        "translation": "Use modular information architecture and blueprint-like organization for dense B2B decision content.",
    },
)

STRUCTURE_PAGE_TYPES = {"structure", "catalog", "investment-asset", "outdoor-structure", "indoor-structure"}
MOTION_PURPOSES = {
    "reveal_information",
    "show_progress",
    "show_relationship",
    "show_state_change",
    "show_scale_or_depth",
    "focus_attention",
    "transition_context",
    "simulate_configuration",
}


@dataclass(frozen=True)
class CIEGateResult:
    status: str
    score: int
    failed_rules: tuple[str, ...]
    conditions: tuple[str, ...]
    remediation_actions: tuple[str, ...]
    evidence_needed: tuple[str, ...]

    @property
    def build_allowed(self) -> bool:
        return self.status in {"pass", "pass_with_conditions"}


def _page_type(page: PageSpec) -> str:
    return str(page.metadata.get("page_type", page.metadata.get("type", "content"))).strip().lower() or "content"


def _reference_catalog(page: PageSpec) -> tuple[dict[str, str], ...]:
    configured = page.metadata.get("approved_references")
    if not configured:
        return APPROVED_REFERENCES
    if not isinstance(configured, Sequence) or isinstance(configured, (str, bytes)):
        return APPROVED_REFERENCES
    selected: list[dict[str, str]] = []
    for item in configured:
        text = str(item).strip().lower()
        for reference in APPROVED_REFERENCES:
            if text in {reference["name"].lower(), reference["url"].lower()}:
                selected.append(reference)
                break
    return tuple(selected) or APPROVED_REFERENCES


def _semantic_motion_purpose(effect: str, index: int) -> str:
    value = effect.lower()
    if "stagger" in value or "reveal" in value or "fade" in value:
        return "reveal_information"
    if "expand" in value or "scale" in value:
        return "show_scale_or_depth"
    if "focus" in value:
        return "focus_attention"
    return ("show_progress", "transition_context", "show_relationship")[index % 3]


def build_creative_blueprint(
    page: PageSpec,
    content: ContentPlan,
    intelligence: CreativeIntelligencePlan,
    patterns: PatternPlan,
    motion: MotionPlan,
) -> dict[str, Any]:
    page_type = _page_type(page)
    references = _reference_catalog(page)
    if page_type in STRUCTURE_PAGE_TYPES:
        references = tuple(sorted(references, key=lambda item: item["name"] != "NRG Build Your Data Center"))

    journey = []
    for index, block in enumerate(content.blocks):
        journey.append(
            {
                "stage": block.role or f"stage-{index + 1}",
                "user_question": block.intent or block.title,
                "desired_state": block.title,
                "cta": block.cta_label or None,
            }
        )
    if len(journey) < 2:
        journey.extend(
            [
                {"stage": "understand", "user_question": "What is this?", "desired_state": "understand the offer", "cta": None},
                {"stage": "decide", "user_question": "What should I do next?", "desired_state": "choose a next step", "cta": None},
            ][: 2 - len(journey)]
        )

    narrative = []
    for index, block in enumerate(content.blocks):
        section_pattern = patterns.sections[index] if index < len(patterns.sections) else None
        narrative.append(
            {
                "id": block.section_id,
                "purpose": block.intent or block.role,
                "content_role": block.role,
                "visual_role": section_pattern.motif if section_pattern else page.visual_profile,
                "interaction_role": section_pattern.transition if section_pattern else "progressive reveal",
            }
        )
    while len(narrative) < 3:
        narrative.append(
            {
                "id": f"support-{len(narrative)+1}",
                "purpose": "support decision clarity",
                "content_role": "support",
                "visual_role": page.visual_profile,
                "interaction_role": "progressive reveal",
            }
        )

    motion_grammar = []
    for index, cue in enumerate(motion.cues):
        motion_grammar.append(
            {
                "purpose": _semantic_motion_purpose(cue.effect, index),
                "trigger": cue.trigger,
                "behavior": f"{cue.effect} on {cue.target}",
                "fallback": cue.reduced_effect or "static visible state with no required motion",
            }
        )
    if not motion_grammar:
        motion_grammar.append(
            {
                "purpose": "reveal_information",
                "trigger": "section enters viewport",
                "behavior": "progressively reveal the next information state",
                "fallback": "render all information statically",
            }
        )

    reference_translation = [
        {
            "reference": item["name"],
            "observed_principle": item["principle"],
            "page_translation": item["translation"],
            "anti_copy_constraint": "Do not reproduce source layout, assets, geometry, copy, signature sequence or branded interaction verbatim.",
            "source_url": item["url"],
        }
        for item in references
    ]

    primary_intent = content.primary_intent or intelligence.query.search_intent
    conversion_goal = intelligence.sales.conversion_goal
    creative_thesis = (
        f"Turn {page.title} into a guided decision experience for '{primary_intent}', using {page.visual_profile} "
        f"to make complexity legible and move the visitor toward {conversion_goal} without imitating reference compositions."
    )

    blueprint: dict[str, Any] = {
        "version": "1.0",
        "project_id": str(page.metadata.get("project_id", page.brand or "ruos")),
        "page_id": page.slug,
        "page_type": page_type,
        "creative_thesis": creative_thesis,
        "primary_intent": primary_intent,
        "conversion_goal": conversion_goal,
        "user_journey": journey,
        "narrative_architecture": narrative,
        "visual_system": {
            "composition": f"page-specific {patterns.scroll_model} composition; avoid generic card-grid-only treatment",
            "typography": "high-legibility Persian-first hierarchy with display scale reserved for narrative emphasis",
            "imagery": "evidence-led product, structure, process or project imagery; no decorative stock dependency",
            "depth": "progressive spatial depth only where it clarifies hierarchy, anatomy or state",
            "materiality": "brand-consistent physical/industrial material cues where relevant",
            "color_logic": f"derive from visual profile {page.visual_profile} and locked brand tokens",
        },
        "motion_grammar": motion_grammar,
        "interaction_model": {
            "desktop": "scroll-led progressive narrative with keyboard-safe controls and explicit state changes",
            "mobile": "touch-first vertical/snap translation of the same narrative; no hover dependency",
            "reduced_motion": "remove cinematic transforms and preserve content/state order with instant or short opacity changes",
            "keyboard": "interactive controls remain focusable and operable without pointer input",
            "touch": "minimum touch target and tap alternatives for every hover or pointer affordance",
        },
        "responsive_strategy": {
            "single_codebase": True,
            "desktop_to_mobile_translation": [
                "pinned or horizontal desktop sequences become touch-first vertical/snap sequences",
                "hover states become tap/focus states",
                "high-cost 3D can degrade to DOM/SVG or pre-rendered states",
            ],
            "breakpoint_notes": ["preserve narrative order", "preserve CTA availability", "preserve semantic content parity"],
        },
        "reference_translation": reference_translation,
        "implementation": {
            "recommended_stack": ["semantic HTML", "CSS", "vanilla JavaScript", "progressive enhancement"],
            "progressive_enhancement": "Core content, navigation and conversion remain functional without advanced motion or 3D.",
            "performance_budget": "Do not make WebGL, video or large motion assets prerequisites for understanding or conversion.",
            "fallbacks": ["reduced-motion mode", "low-power static state", "touch-first alternative", "no-JS readable content"],
        },
        "evidence": [
            {"claim": f"Approved reference principle: {item['principle']}", "source": item["url"], "confidence": 1.0}
            for item in references
        ],
        "risks": [
            "overusing cinematic motion can obscure the user journey",
            "reference similarity can become imitation if layout or signature sequences are copied",
            "technical values must remain unknown until supported by project evidence",
        ],
        "gate": {"status": "blocked", "failed_rules": [], "conditions": []},
    }
    gate = evaluate_cie_gate(blueprint, page)
    blueprint["gate"] = {
        "status": gate.status,
        "failed_rules": list(gate.failed_rules),
        "conditions": list(gate.conditions),
    }
    blueprint["gate_report"] = {
        "score": gate.score,
        "remediation_actions": list(gate.remediation_actions),
        "evidence_needed": list(gate.evidence_needed),
    }
    return blueprint


def _schema_shape_valid(blueprint: Mapping[str, Any]) -> bool:
    required = {
        "version", "project_id", "page_id", "creative_thesis", "user_journey", "narrative_architecture",
        "visual_system", "motion_grammar", "interaction_model", "responsive_strategy", "reference_translation",
        "implementation", "risks", "gate",
    }
    if not required.issubset(blueprint):
        return False
    if len(str(blueprint.get("creative_thesis", ""))) < 20:
        return False
    if len(blueprint.get("user_journey", [])) < 2 or len(blueprint.get("narrative_architecture", [])) < 3:
        return False
    if not blueprint.get("responsive_strategy", {}).get("single_codebase") is True:
        return False
    purposes = {item.get("purpose") for item in blueprint.get("motion_grammar", []) if isinstance(item, Mapping)}
    return bool(purposes) and purposes.issubset(MOTION_PURPOSES)


def evaluate_cie_gate(blueprint: Mapping[str, Any], page: PageSpec) -> CIEGateResult:
    failures: list[str] = []
    conditions: list[str] = []
    remediation: list[str] = []
    evidence_needed: list[str] = []

    def fail(rule: str, action: str, evidence: str = "") -> None:
        failures.append(rule)
        remediation.append(action)
        if evidence:
            evidence_needed.append(evidence)

    if not str(blueprint.get("primary_intent", "")).strip() or not str(blueprint.get("conversion_goal", "")).strip():
        fail("CIE-001", "Define a clear page intent and conversion goal.")
    thesis = str(blueprint.get("creative_thesis", ""))
    if len(thesis) < 40 or page.title not in thesis:
        fail("CIE-002", "Rewrite the creative thesis so it is page-specific and tied to the user journey.")
    translations = blueprint.get("reference_translation", [])
    if not translations:
        fail("CIE-003", "Analyze approved references and translate each major principle to this page.", "approved reference analysis")
    elif any(not str(item.get("anti_copy_constraint", "")).strip() for item in translations if isinstance(item, Mapping)):
        fail("CIE-004", "Add explicit anti-copy constraints to every reference translation.")
    if not blueprint.get("evidence"):
        fail("CIE-005", "Attach provenance to provider/reference evidence.", "provider or reference provenance")
    unsupported = page.metadata.get("unsupported_claims")
    if unsupported:
        fail("CIE-006", "Remove, source or mark unsupported claims as unresolved.", "source for unsupported claims")
    interaction = blueprint.get("interaction_model", {})
    if not interaction.get("mobile") or not interaction.get("touch"):
        fail("CIE-007", "Define mobile and touch-first behavior for each core interaction.")
    if not interaction.get("reduced_motion") or not blueprint.get("implementation", {}).get("fallbacks"):
        fail("CIE-008", "Define reduced-motion and progressive enhancement fallbacks.")
    if blueprint.get("responsive_strategy", {}).get("single_codebase") is not True:
        fail("CIE-009", "Use one responsive implementation contract for desktop and mobile.")
    if not _schema_shape_valid(blueprint):
        fail("CIE-010", "Repair the Creative Blueprint until required schema shape and controlled motion purposes validate.")
    if any(item.get("purpose") not in MOTION_PURPOSES for item in blueprint.get("motion_grammar", []) if isinstance(item, Mapping)):
        fail("CIE-011", "Give every core motion cue a semantic purpose or remove it.")
    composition = str(blueprint.get("visual_system", {}).get("composition", ""))
    if "card-grid-only" not in composition:
        fail("CIE-012", "Document a page-specific narrative/interaction system and explicitly reject generic card-grid-only composition.")

    page_type = _page_type(page)
    names = {str(item.get("reference")) for item in translations if isinstance(item, Mapping)}
    if page_type in STRUCTURE_PAGE_TYPES and "NRG Build Your Data Center" not in names:
        conditions.append("RU-CIE-002: document why another interaction model better serves this structure/catalog page.")
    if not blueprint.get("motion_grammar"):
        conditions.append("RU-CIE-003: define a coherent presentation transition system before implementation.")

    score = max(0, 100 - len(failures) * 12 - len(conditions) * 5)
    if failures:
        status = "blocked"
    elif score >= 85 and not conditions:
        status = "pass"
    elif score >= 75:
        status = "pass_with_conditions"
    else:
        status = "blocked"

    return CIEGateResult(
        status=status,
        score=score,
        failed_rules=tuple(failures),
        conditions=tuple(conditions),
        remediation_actions=tuple(dict.fromkeys(remediation)),
        evidence_needed=tuple(dict.fromkeys(evidence_needed)),
    )

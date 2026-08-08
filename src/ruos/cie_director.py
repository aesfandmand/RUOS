from __future__ import annotations

from typing import Any, Mapping

from .content_composer import ContentPlan
from .creative_intelligence import CreativeIntelligencePlan
from .models import PageSpec
from .motion_composer import MotionPlan
from .pattern_resolver import PatternPlan


def _provider_recommendations(provider_pipeline: Mapping[str, Any]) -> dict[str, list[str]]:
    by_domain: dict[str, list[str]] = {}
    for provider in provider_pipeline.get("providers", []):
        if not isinstance(provider, Mapping):
            continue
        domain = str(provider.get("domain", "general"))
        recommendations = provider.get("page_specific_recommendations", [])
        for item in recommendations:
            if isinstance(item, Mapping) and str(item.get("recommendation", "")).strip():
                by_domain.setdefault(domain, []).append(str(item["recommendation"]).strip())
    return by_domain


def build_creative_director_plan(
    page: PageSpec,
    content: ContentPlan,
    intelligence: CreativeIntelligencePlan,
    patterns: PatternPlan,
    motion: MotionPlan,
    provider_pipeline: Mapping[str, Any],
) -> dict[str, Any]:
    synthesis = provider_pipeline.get("synthesis", {})
    if not isinstance(synthesis, Mapping) or synthesis.get("status") != "ready":
        return {"version": "1.0", "status": "blocked", "sections": [], "blockers": ["provider synthesis is not ready"]}

    provider_guidance = _provider_recommendations(provider_pipeline)
    motion_by_section = {cue.section_id: cue for cue in motion.cues}
    decisions: list[dict[str, Any]] = []

    for block in content.blocks:
        pattern = patterns.for_section(block.section_id)
        cue = motion_by_section.get(block.section_id)
        entities = list(block.entities) or list(intelligence.semantic.entities[:4])
        visual_treatment = (
            f"{pattern.motif} motif with {pattern.alignment} alignment, {pattern.pacing} pacing, "
            f"and {pattern.attributes.get('contrast', 'brand')} contrast"
        )
        interaction = pattern.transition
        motion_instruction = None
        fallback = "static semantic layout preserving content order and CTA availability"
        if cue is not None:
            motion_instruction = {
                "trigger": cue.trigger,
                "target": cue.target,
                "effect": cue.effect,
                "duration_ms": cue.duration_ms,
                "easing": cue.easing,
                "semantic_purpose": "reveal or clarify section state",
            }
            fallback = cue.reduced_effect or fallback

        mobile = (
            "translate the same decision state into a touch-first vertical sequence; preserve heading, evidence, entity labels and CTA parity; "
            "replace hover/pinned behavior with tap/focus or vertical/snap progression"
        )
        evidence = [f"query:{intelligence.query.primary_query}"] + [f"entity:{entity}" for entity in entities[:6]]
        if page.metadata.get("page_type") in {"structure", "catalog", "investment-asset", "outdoor-structure", "indoor-structure"} or page.slug in {"structures", "structure", "catalog"}:
            evidence.append("industrial-product-provider-required")

        decisions.append(
            {
                "section_id": block.section_id,
                "chapter": pattern.chapter,
                "intent": block.intent,
                "content_role": block.role,
                "heading": block.title,
                "content_instruction": "Answer the section intent directly, then support the next decision with evidence and a clear transition.",
                "visual_treatment": visual_treatment,
                "interaction": interaction,
                "motion": motion_instruction,
                "mobile_translation": mobile,
                "fallback": fallback,
                "cta": {"label": block.cta_label or None, "href": block.cta_href or None},
                "entity_mapping": entities,
                "schema_mapping": list(intelligence.semantic.schema_types),
                "evidence": evidence,
                "provider_guidance": {
                    key: values for key, values in provider_guidance.items()
                    if key in {"visual_direction", "motion_interaction", "ux_storytelling", "industrial_product", "brand_editorial", "performance_accessibility", "seo_ai_knowledge_graph"}
                },
            }
        )

    status = "ready" if decisions and len(decisions) == len(content.blocks) else "blocked"
    blockers = [] if status == "ready" else ["every content block must have one executable section decision"]
    return {
        "version": "1.0",
        "status": status,
        "page_id": page.slug,
        "creative_thesis": f"Execute {page.title} as a chaptered decision system that aligns intent, evidence, interaction and conversion.",
        "global_rules": {
            "single_codebase": True,
            "semantic_parity": True,
            "mobile_touch_first": True,
            "reduced_motion_required": True,
            "anti_copy": True,
        },
        "sections": decisions,
        "blockers": blockers,
    }

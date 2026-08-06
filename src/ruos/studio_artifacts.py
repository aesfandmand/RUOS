from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from typing import Mapping

from .component_resolver import ComponentPlan
from .content_composer import ContentPlan
from .creative_intelligence import CreativeIntelligencePlan
from .models import GateResult, PageSpec
from .motion_composer import MotionPlan
from .pattern_resolver import PatternPlan
from .quality_score import AgencyQualityScore
from .research_studio import conduct_research
from .virtual_studio import conduct_virtual_studio_review
from .visual_dna import VisualDNA
from .voice_studio import select_voice


class StudioArtifactError(ValueError):
    pass


@dataclass(frozen=True)
class DecisionArtifact:
    name: str
    owner: str
    dependencies: tuple[str, ...]
    payload: Mapping[str, object]

    def canonical_json(self) -> str:
        return json.dumps(self.payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"))

    @property
    def sha256(self) -> str:
        return hashlib.sha256(self.canonical_json().encode("utf-8")).hexdigest()


@dataclass(frozen=True)
class StudioArtifactBundle:
    page_slug: str
    artifacts: tuple[DecisionArtifact, ...]

    def by_name(self, name: str) -> DecisionArtifact:
        for artifact in self.artifacts:
            if artifact.name == name:
                return artifact
        raise KeyError(name)

    def manifest(self) -> dict[str, object]:
        return {
            "page_slug": self.page_slug,
            "pipeline": [artifact.name for artifact in self.artifacts],
            "artifacts": {
                artifact.name: {
                    "owner": artifact.owner,
                    "dependencies": list(artifact.dependencies),
                    "sha256": artifact.sha256,
                }
                for artifact in self.artifacts
            },
        }


_REQUIRED_ORDER = (
    "research.json",
    "creative-direction.json",
    "art-direction.json",
    "ux-plan.json",
    "ui-plan.json",
    "motion-plan.json",
    "content-plan.json",
    "seo-plan.json",
    "cro-plan.json",
    "agency-review.json",
)


def _artifact(name: str, owner: str, dependencies: tuple[str, ...], payload: dict[str, object]) -> DecisionArtifact:
    if not payload:
        raise StudioArtifactError(f"{name} cannot be empty")
    return DecisionArtifact(name=name, owner=owner, dependencies=dependencies, payload=payload)


def build_studio_artifacts(
    page: PageSpec,
    dna: VisualDNA,
    components: ComponentPlan,
    patterns: PatternPlan,
    motion: MotionPlan,
    content: ContentPlan,
    intelligence: CreativeIntelligencePlan,
    gates: tuple[GateResult, ...],
    quality: AgencyQualityScore,
) -> StudioArtifactBundle:
    query = intelligence.query
    sales = intelligence.sales
    semantic = intelligence.semantic
    creative = intelligence.creative
    research = conduct_research(page, intelligence)
    voice = select_voice(page)
    studio_review = conduct_virtual_studio_review(page, research, gates, quality)

    artifacts = (
        _artifact("research.json", "Research Studio", (), research.payload()),
        _artifact(
            "creative-direction.json",
            "Creative Director",
            ("research.json",),
            {
                "narrative_model": creative.narrative_model,
                "emotional_curve": list(creative.emotional_curve),
                "persuasion_principles": list(creative.persuasion_principles),
                "visual_direction": creative.visual_direction,
                "page_identity": page.visual_profile,
                "research_sha256": research.sha256,
                "selected_pattern_candidates": [candidate.id for candidate in research.pattern_candidates],
            },
        ),
        _artifact(
            "art-direction.json",
            "Art Director",
            ("creative-direction.json",),
            {
                "visual_dna": dict(dna.fingerprint_payload()),
                "global_motif": patterns.global_motif,
                "scroll_model": patterns.scroll_model,
                "section_motifs": [section.motif for section in patterns.sections],
                "research_constraints": sorted({constraint for candidate in research.pattern_candidates for constraint in candidate.constraints}),
            },
        ),
        _artifact(
            "ux-plan.json",
            "UX Lead",
            ("research.json", "creative-direction.json"),
            {
                "narrative_arc": patterns.narrative_arc,
                "journey": page.metadata.get("journey", ""),
                "audience_hypotheses": list(research.audience_hypotheses),
                "sections": [
                    {"id": section.section_id, "chapter": section.chapter, "pacing": section.pacing, "transition": section.transition}
                    for section in patterns.sections
                ],
            },
        ),
        _artifact(
            "ui-plan.json",
            "UI Lead",
            ("art-direction.json", "ux-plan.json"),
            {
                "components": [
                    {
                        "id": component.id,
                        "section_id": component.section_id,
                        "family": component.family,
                        "variant": component.variant,
                        "density": component.density,
                        "emphasis": component.emphasis,
                        "capabilities": list(component.capabilities),
                    }
                    for component in components.components
                ]
            },
        ),
        _artifact(
            "motion-plan.json",
            "Motion Lead",
            ("ux-plan.json", "ui-plan.json"),
            {
                "strategy": motion.strategy,
                "reduced_motion_policy": motion.reduced_motion_policy,
                "cues": [
                    {
                        "section_id": cue.section_id,
                        "order": cue.order,
                        "trigger": cue.trigger,
                        "target": cue.target,
                        "effect": cue.effect,
                        "duration_ms": cue.duration_ms,
                        "delay_ms": cue.delay_ms,
                        "easing": cue.easing,
                    }
                    for cue in motion.cues
                ],
            },
        ),
        _artifact(
            "content-plan.json",
            "Content Director",
            ("research.json", "ux-plan.json"),
            {
                "language": content.language,
                "direction": content.direction,
                "primary_intent": content.primary_intent,
                "voice": {
                    **voice.payload(),
                    "sha256": voice.sha256,
                },
                "blocks": [
                    {
                        "section_id": block.section_id,
                        "role": block.role,
                        "heading_level": block.heading_level,
                        "intent": block.intent,
                        "title": block.title,
                        "body": block.body,
                        "cta_label": block.cta_label,
                        "cta_href": block.cta_href,
                        "entities": list(block.entities),
                        "attributes": dict(block.attributes),
                    }
                    for block in content.blocks
                ],
            },
        ),
        _artifact(
            "seo-plan.json",
            "SEO Lead",
            ("research.json", "content-plan.json"),
            {
                "title": page.title,
                "description": page.description,
                "primary_query": query.primary_query,
                "supporting_queries": list(query.supporting_queries),
                "schema_types": list(semantic.schema_types),
                "answer_targets": list(semantic.answer_targets),
                "ai_summary": semantic.ai_summary,
                "evidence_status": research.evidence_status,
                "limitations": list(research.limitations),
            },
        ),
        _artifact(
            "cro-plan.json",
            "CRO Lead",
            ("research.json", "content-plan.json", "ux-plan.json"),
            {
                "conversion_goal": sales.conversion_goal,
                "value_proposition": sales.value_proposition,
                "friction_policy": sales.friction_policy,
                "proof_requirements": list(sales.proof_requirements),
                "cta_sequence": list(sales.cta_sequence),
                "commercial_routes": list(page.metadata.get("commercial_routes", [])),
            },
        ),
        _artifact(
            "agency-review.json",
            "Virtual Studio Review Board",
            ("creative-direction.json", "art-direction.json", "ux-plan.json", "ui-plan.json", "motion-plan.json", "content-plan.json", "seo-plan.json", "cro-plan.json"),
            {
                **studio_review.payload(),
                "studio_review_sha256": studio_review.sha256,
                "agency_quality": {
                    "score": quality.total,
                    "grade": quality.grade,
                    "publishable": quality.publishable,
                },
                "research": {
                    "evidence_score": research.evidence_score,
                    "evidence_status": research.evidence_status,
                    "sha256": research.sha256,
                },
                "content_voice": {
                    "approved_voice_id": voice.approved_voice_id,
                    "approval_status": voice.approval_status,
                    "sha256": voice.sha256,
                },
            },
        ),
    )
    names = tuple(artifact.name for artifact in artifacts)
    if names != _REQUIRED_ORDER:
        raise StudioArtifactError("Studio artifact pipeline order is invalid")
    seen: set[str] = set()
    for artifact in artifacts:
        missing = [dependency for dependency in artifact.dependencies if dependency not in seen]
        if missing:
            raise StudioArtifactError(f"{artifact.name} has unresolved dependencies: {', '.join(missing)}")
        seen.add(artifact.name)
    return StudioArtifactBundle(page_slug=page.slug, artifacts=artifacts)

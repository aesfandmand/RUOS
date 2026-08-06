from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from typing import Mapping

from .art_director import direct_art
from .competitive_intelligence import build_competitive_intelligence
from .component_resolver import ComponentPlan
from .content_composer import ContentPlan
from .creative_intelligence import CreativeIntelligencePlan
from .creative_selection import select_creative_library
from .design_brief import compile_design_brief
from .design_critic import critique_design
from .inspiration_intelligence import analyze_inspiration
from .models import GateResult, PageSpec
from .motion_composer import MotionPlan
from .pattern_intelligence import select_patterns
from .pattern_resolver import PatternPlan
from .quality_score import AgencyQualityScore
from .query_intelligence import build_query_intelligence
from .research_studio import conduct_research
from .studio_knowledge import compose_studio_knowledge
from .ux_director import direct_ux
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
    "query-intelligence.json",
    "competitive-analysis.json",
    "pattern-selection.json",
    "knowledge-graph.json",
    "inspiration-intelligence.json",
    "component-selection.json",
    "design-brief.json",
    "creative-direction.json",
    "art-decision.json",
    "art-direction.json",
    "ux-decision.json",
    "ux-plan.json",
    "ui-plan.json",
    "motion-plan.json",
    "content-plan.json",
    "seo-plan.json",
    "cro-plan.json",
    "design-critique.json",
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
    query_intelligence = build_query_intelligence(page, research, intelligence)
    competition = build_competitive_intelligence(page, research)
    pattern_intelligence = select_patterns(page, research, query_intelligence, competition)
    knowledge_graph = compose_studio_knowledge(page, research, query_intelligence, pattern_intelligence)
    inspiration = analyze_inspiration(page)
    component_selection = select_creative_library(page, query_intelligence, components, pattern_intelligence, knowledge_graph)
    design_brief = compile_design_brief(page, research, query_intelligence, competition, pattern_intelligence, voice)
    art_decision = direct_art(page, dna, patterns, component_selection, inspiration)
    ux_decision = direct_ux(page, components, patterns, art_decision)
    design_critique = critique_design(page, gates, quality, component_selection)
    studio_review = conduct_virtual_studio_review(page, research, gates, quality)
    critique_publishable = design_critique.release_recommendation != "reject"
    final_publishable = studio_review.publishable and critique_publishable
    final_blockers = tuple(dict.fromkeys((*studio_review.blockers, *design_critique.blockers)))

    artifacts = (
        _artifact("research.json", "Research Studio", (), research.payload()),
        _artifact("query-intelligence.json", "SEO Strategist", ("research.json",), query_intelligence.payload()),
        _artifact("competitive-analysis.json", "Competitive Intelligence Lead", ("research.json", "query-intelligence.json"), competition.payload()),
        _artifact("pattern-selection.json", "Creative Research Lead", ("research.json", "query-intelligence.json", "competitive-analysis.json"), pattern_intelligence.payload()),
        _artifact("knowledge-graph.json", "Creative Knowledge Architect", ("research.json", "query-intelligence.json", "pattern-selection.json"), knowledge_graph.payload()),
        _artifact("inspiration-intelligence.json", "Inspiration Intelligence Lead", ("research.json", "knowledge-graph.json"), inspiration.payload()),
        _artifact("component-selection.json", "Creative Systems Lead", ("query-intelligence.json", "pattern-selection.json", "knowledge-graph.json", "inspiration-intelligence.json"), component_selection.payload()),
        _artifact("design-brief.json", "Creative Director", ("query-intelligence.json", "competitive-analysis.json", "pattern-selection.json", "knowledge-graph.json", "inspiration-intelligence.json", "component-selection.json"), design_brief.payload()),
        _artifact("creative-direction.json", "Creative Director", ("design-brief.json", "knowledge-graph.json", "inspiration-intelligence.json", "component-selection.json"), {
            "narrative_model": creative.narrative_model,
            "emotional_curve": list(creative.emotional_curve),
            "persuasion_principles": list(creative.persuasion_principles),
            "visual_direction": creative.visual_direction,
            "page_identity": page.visual_profile,
            "research_sha256": research.sha256,
            "design_brief_sha256": design_brief.sha256,
            "knowledge_graph_sha256": knowledge_graph.sha256,
            "inspiration_intelligence_sha256": inspiration.sha256,
            "component_selection_sha256": component_selection.sha256,
            "selected_pattern_candidates": [item.id for item in pattern_intelligence.selected],
            "selected_library_candidates": [decision.candidate_id for decision in component_selection.decisions],
        }),
        _artifact("art-decision.json", "Art Director", ("creative-direction.json", "inspiration-intelligence.json", "component-selection.json"), art_decision.payload()),
        _artifact("art-direction.json", "Art Director", ("art-decision.json", "pattern-selection.json", "component-selection.json"), {
            "art_decision_sha256": art_decision.sha256,
            "visual_dna": dict(dna.fingerprint_payload()),
            "concept": art_decision.concept,
            "composition": art_decision.composition,
            "hierarchy": list(art_decision.hierarchy),
            "grid_system": art_decision.grid_system,
            "whitespace_rhythm": art_decision.whitespace_rhythm,
            "typography_scale": list(art_decision.typography_scale),
            "color_logic": list(art_decision.color_logic),
            "image_direction": list(art_decision.image_direction),
            "scroll_composition": list(art_decision.scroll_composition),
            "responsive_translation": list(art_decision.responsive_translation),
            "constraints": list(art_decision.constraints),
            "global_motif": patterns.global_motif,
            "scroll_model": patterns.scroll_model,
            "section_motifs": [section.motif for section in patterns.sections],
        }),
        _artifact("ux-decision.json", "UX Director", ("design-brief.json", "creative-direction.json", "art-decision.json", "component-selection.json"), ux_decision.payload()),
        _artifact("ux-plan.json", "UX Lead", ("ux-decision.json", "art-direction.json"), {
            "ux_decision_sha256": ux_decision.sha256,
            "journey_model": ux_decision.journey_model,
            "narrative_arc": patterns.narrative_arc,
            "journey": page.metadata.get("journey", ""),
            "audience_hypotheses": list(research.audience_hypotheses),
            "reading_strategy": design_brief.reading_strategy,
            "interaction_strategy": design_brief.interaction_strategy,
            "reading_contract": list(ux_decision.reading_contract),
            "trust_sequence": list(ux_decision.trust_sequence),
            "conversion_sequence": list(ux_decision.conversion_sequence),
            "mobile_behavior": list(ux_decision.mobile_behavior),
            "accessibility_contract": list(ux_decision.accessibility_contract),
            "stages": [stage.payload() for stage in ux_decision.stages],
            "sections": [{"id": section.section_id, "chapter": section.chapter, "pacing": section.pacing, "transition": section.transition} for section in patterns.sections],
        }),
        _artifact("ui-plan.json", "UI Lead", ("art-direction.json", "ux-plan.json", "component-selection.json"), {
            "selection_sha256": component_selection.sha256,
            "art_decision_sha256": art_decision.sha256,
            "ux_decision_sha256": ux_decision.sha256,
            "components": [{"id": component.id, "section_id": component.section_id, "family": component.family, "variant": component.variant, "density": component.density, "emphasis": component.emphasis, "capabilities": list(component.capabilities)} for component in components.components],
        }),
        _artifact("motion-plan.json", "Motion Lead", ("ux-plan.json", "ui-plan.json", "art-decision.json", "ux-decision.json", "component-selection.json"), {
            "strategy": motion.strategy,
            "reduced_motion_policy": motion.reduced_motion_policy,
            "art_scroll_composition": list(art_decision.scroll_composition),
            "ux_journey_sha256": ux_decision.sha256,
            "cues": [{"section_id": cue.section_id, "order": cue.order, "trigger": cue.trigger, "target": cue.target, "effect": cue.effect, "duration_ms": cue.duration_ms, "delay_ms": cue.delay_ms, "easing": cue.easing} for cue in motion.cues],
        }),
        _artifact("content-plan.json", "Content Director", ("design-brief.json", "ux-decision.json", "ux-plan.json"), {
            "language": content.language,
            "direction": content.direction,
            "primary_intent": content.primary_intent,
            "ux_decision_sha256": ux_decision.sha256,
            "voice": {**voice.payload(), "sha256": voice.sha256},
            "blocks": [{"section_id": block.section_id, "role": block.role, "heading_level": block.heading_level, "intent": block.intent, "title": block.title, "body": block.body, "cta_label": block.cta_label, "cta_href": block.cta_href, "entities": list(block.entities), "attributes": dict(block.attributes)} for block in content.blocks],
        }),
        _artifact("seo-plan.json", "SEO Lead", ("query-intelligence.json", "content-plan.json"), {
            "title": page.title,
            "description": page.description,
            "primary_query": query.primary_query,
            "supporting_queries": list(query.supporting_queries),
            "clusters": [cluster.payload() for cluster in query_intelligence.clusters],
            "schema_types": list(semantic.schema_types),
            "answer_targets": list(semantic.answer_targets),
            "ai_summary": semantic.ai_summary,
            "evidence_status": research.evidence_status,
            "limitations": list(research.limitations),
        }),
        _artifact("cro-plan.json", "CRO Lead", ("design-brief.json", "content-plan.json", "ux-decision.json", "ux-plan.json"), {
            "conversion_goal": sales.conversion_goal,
            "value_proposition": sales.value_proposition,
            "friction_policy": sales.friction_policy,
            "proof_requirements": list(sales.proof_requirements),
            "cta_sequence": list(sales.cta_sequence),
            "ux_conversion_sequence": list(ux_decision.conversion_sequence),
            "commercial_routes": list(page.metadata.get("commercial_routes", [])),
            "opportunity_gaps": list(competition.opportunity_gaps),
        }),
        _artifact("design-critique.json", "Design Critic", ("component-selection.json", "creative-direction.json", "art-decision.json", "art-direction.json", "ux-decision.json", "ux-plan.json", "ui-plan.json", "motion-plan.json", "content-plan.json", "seo-plan.json", "cro-plan.json"), design_critique.payload()),
        _artifact("agency-review.json", "Virtual Studio Review Board", ("knowledge-graph.json", "inspiration-intelligence.json", "component-selection.json", "design-brief.json", "creative-direction.json", "art-decision.json", "art-direction.json", "ux-decision.json", "ux-plan.json", "ui-plan.json", "motion-plan.json", "content-plan.json", "seo-plan.json", "cro-plan.json", "design-critique.json"), {
            **studio_review.payload(),
            "publishable": final_publishable,
            "blockers": list(final_blockers),
            "studio_review_sha256": studio_review.sha256,
            "design_critique_sha256": design_critique.sha256,
            "design_critique_recommendation": design_critique.release_recommendation,
            "design_critique_publishable": critique_publishable,
            "agency_quality": {"score": quality.total, "grade": quality.grade, "publishable": quality.publishable},
            "research": {
                "evidence_score": research.evidence_score,
                "evidence_status": research.evidence_status,
                "sha256": research.sha256,
                "query_intelligence_sha256": query_intelligence.sha256,
                "competitive_intelligence_sha256": competition.sha256,
                "pattern_intelligence_sha256": pattern_intelligence.sha256,
                "knowledge_graph_sha256": knowledge_graph.sha256,
                "inspiration_intelligence_sha256": inspiration.sha256,
                "component_selection_sha256": component_selection.sha256,
                "design_brief_sha256": design_brief.sha256,
                "art_decision_sha256": art_decision.sha256,
                "ux_decision_sha256": ux_decision.sha256,
            },
            "content_voice": {"approved_voice_id": voice.approved_voice_id, "approval_status": voice.approval_status, "sha256": voice.sha256},
        }),
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

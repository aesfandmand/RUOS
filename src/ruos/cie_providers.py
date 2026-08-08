from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping, Protocol, Sequence

from .content_composer import ContentPlan
from .creative_intelligence import CreativeIntelligencePlan
from .models import PageSpec
from .motion_composer import MotionPlan
from .pattern_resolver import PatternPlan


CONFLICT_PRIORITY: tuple[str, ...] = (
    "locked_project_rules",
    "user_and_business_goal",
    "evidence_and_truth",
    "accessibility_and_mobile",
    "brand_distinctiveness",
    "approved_reference_direction",
    "novelty",
)

STRUCTURE_PAGE_TYPES = {"structure", "product", "catalog", "industrial-service", "investment-asset", "outdoor-structure", "indoor-structure"}


@dataclass(frozen=True)
class ProviderFinding:
    provider_id: str
    domain: str
    recommendation: str
    rationale: str
    confidence: float
    priority_basis: str
    evidence: tuple[str, ...] = ()
    risks: tuple[str, ...] = ()
    mobile: str | None = None
    fallback: str | None = None

    def payload(self) -> dict[str, Any]:
        provenance = [
            {"id": f"{self.provider_id}-{index}", "source": source, "source_type": "repo-artifact" if source.startswith(("intent:", "query:", "entity:", "visual-profile:", "scroll-model:", "motion-cues:")) else "approved-reference"}
            for index, source in enumerate(self.evidence, start=1)
        ]
        if not provenance:
            provenance = [{"id": f"{self.provider_id}-context", "source": "RUOS PageSpec and deterministic runtime context", "source_type": "repo-artifact"}]
        return {
            "provider_id": self.provider_id,
            "status": "success",
            "domain": self.domain,
            "findings": [{"observation": self.rationale, "principle": self.recommendation, "evidence_id": provenance[0]["id"]}],
            "page_specific_recommendations": [{"recommendation": self.recommendation, "reason": self.rationale, "priority": "high", "desktop": self.recommendation, "mobile": self.mobile, "fallback": self.fallback}],
            "anti_copy_constraints": ["Do not copy source layout, geometry, copy, branded assets, or signature interaction sequences verbatim."],
            "provenance": provenance,
            "risks": [{"risk": risk, "severity": "medium", "mitigation": self.fallback} for risk in self.risks],
            "unknowns": [],
            "confidence": self.confidence,
            "priority_basis": self.priority_basis,
        }


@dataclass(frozen=True)
class ProviderContext:
    page: PageSpec
    content: ContentPlan
    intelligence: CreativeIntelligencePlan
    patterns: PatternPlan
    motion: MotionPlan
    references: Sequence[Mapping[str, str]]


class IntelligenceProvider(Protocol):
    provider_id: str
    domain: str
    required: bool
    def applies(self, context: ProviderContext) -> bool: ...
    def analyze(self, context: ProviderContext) -> ProviderFinding: ...


class BaseProvider:
    required = True
    def applies(self, context: ProviderContext) -> bool:
        return True


class ReferenceVisualAnalyst(BaseProvider):
    provider_id = "reference_visual_analyst"; domain = "visual_direction"
    def analyze(self, context: ProviderContext) -> ProviderFinding:
        names = tuple(str(item.get("name", "")) for item in context.references if item.get("name")); evidence = tuple(str(item.get("url", "")) for item in context.references if item.get("url"))
        return ProviderFinding(self.provider_id, self.domain, "Translate approved visual principles into a page-specific composition without copying source geometry or signature sequences.", f"Visual profile is {context.page.visual_profile}; approved references: {', '.join(names)}.", 1.0 if evidence else 0.7, "approved_reference_direction", evidence, ("reference similarity can become imitation",), "Preserve hierarchy and information parity in a touch-first vertical composition.", "Use static DOM/SVG composition when advanced spatial effects are too costly.")


class MotionInteractionAnalyst(BaseProvider):
    provider_id = "motion_interaction_analyst"; domain = "motion_interaction"
    def analyze(self, context: ProviderContext) -> ProviderFinding:
        cue_count = len(context.motion.cues)
        return ProviderFinding(self.provider_id, self.domain, "Use motion only to reveal information, relationships, progress, state or depth; preserve touch, keyboard and reduced-motion equivalents.", f"Resolved motion plan contains {cue_count} cues.", 0.96, "accessibility_and_mobile", (f"motion-cues:{cue_count}",), ("motion can obscure the journey or increase loading cost",), "Replace hover/pinned dependencies with tap/focus and vertical/snap equivalents.", "Render the same information in static visible states under reduced motion or constrained devices.")


class UXJourneyAnalyst(BaseProvider):
    provider_id = "ux_journey_analyst"; domain = "ux_storytelling"
    def analyze(self, context: ProviderContext) -> ProviderFinding:
        roles = tuple(block.role for block in context.content.blocks if block.role)
        return ProviderFinding(self.provider_id, self.domain, "Make each section answer the next user question and advance one decision state toward the conversion goal.", f"Journey has {len(context.content.blocks)} blocks and roles {roles or ('unassigned',)}.", 0.94, "user_and_business_goal", (f"intent:{context.content.primary_intent or context.intelligence.query.search_intent}",), ("excessive spectacle can increase decision friction",), "Keep CTA availability and narrative order identical on mobile.", "Prefer a linear semantic reading order when advanced choreography is unavailable.")


class IndustrialProductAnalyst(BaseProvider):
    provider_id = "industrial_product_analyst"; domain = "industrial_product"
    def applies(self, context: ProviderContext) -> bool:
        page_type = str(context.page.metadata.get("page_type", context.page.metadata.get("type", ""))).strip().lower()
        return page_type in STRUCTURE_PAGE_TYPES
    def analyze(self, context: ProviderContext) -> ProviderFinding:
        return ProviderFinding(self.provider_id, self.domain, "Expose structure anatomy, technical layers, options, scale and evidence progressively; prefer NRG-like staged construction logic for structure/catalog pages.", "Industrial pages require comprehension of physical relationships before purchase, investment or specification decisions.", 0.98, "evidence_and_truth", tuple(str(item.get("url", "")) for item in context.references if "NRG" in str(item.get("name", ""))), ("unsupported technical values can become false claims",), "Convert hotspots and horizontal assemblies into tap-accessible vertical anatomy stages.", "Show labeled static diagrams and evidence-bound specifications when 3D or virtual-tour interactions are unavailable.")


class BrandEditorialAnalyst(BaseProvider):
    provider_id = "brand_editorial_analyst"; domain = "brand_editorial"
    def analyze(self, context: ProviderContext) -> ProviderFinding:
        return ProviderFinding(self.provider_id, self.domain, "Keep the customer as the decision-making hero; use brand voice to clarify responsibility, proof and the next action rather than to self-celebrate.", f"Conversion goal is {context.intelligence.sales.conversion_goal}; page title is {context.page.title}.", 0.93, "brand_distinctiveness", (f"intent:{context.content.primary_intent or context.intelligence.query.search_intent}",), ("generic agency language can weaken specificity",), "Retain concise decision copy and proof near mobile actions.", "If rich media is absent, copy and evidence must still carry the complete persuasion sequence.")


class PerformanceAccessibilityAnalyst(BaseProvider):
    provider_id = "performance_accessibility_analyst"; domain = "performance_accessibility"
    def analyze(self, context: ProviderContext) -> ProviderFinding:
        return ProviderFinding(self.provider_id, self.domain, "Advanced motion, 3D and media must progressively enhance a fully usable semantic page with keyboard, touch, reduced-motion and low-power fallbacks.", "The approved quality bar is cinematic, but comprehension and conversion cannot depend on expensive rendering.", 0.99, "accessibility_and_mobile", (f"scroll-model:{context.patterns.scroll_model}",), ("high-cost effects can harm loading, battery and accessibility",), "Use touch-first controls, minimum tap targets and no hover-only states.", "Fall back to semantic HTML, CSS, SVG or pre-rendered states while preserving content and CTA parity.")


class CompetitiveDifferentiationAnalyst(BaseProvider):
    provider_id = "competitive_differentiation_analyst"; domain = "competitive_differentiation"; required = False
    def analyze(self, context: ProviderContext) -> ProviderFinding:
        return ProviderFinding(self.provider_id, self.domain, "Reject generic card-grid-only composition and common category clichés; differentiate through page-specific information choreography rather than novelty for its own sake.", f"Scroll model is {context.patterns.scroll_model} and visual profile is {context.page.visual_profile}.", 0.88, "novelty", (f"visual-profile:{context.page.visual_profile}",), ("novelty can conflict with usability",), "Preserve differentiation through hierarchy and interaction pacing rather than desktop-only spectacle.", "Use distinctive typography, structure and evidence sequencing when advanced effects are disabled.")


class SEOAIKnowledgeGraphAnalyst(BaseProvider):
    provider_id = "seo_ai_knowledge_graph_analyst"; domain = "seo_ai_knowledge_graph"
    def analyze(self, context: ProviderContext) -> ProviderFinding:
        query = context.intelligence.query.primary_query; entities = tuple(context.intelligence.semantic.entities)
        return ProviderFinding(self.provider_id, self.domain, "Keep query intent, named entities, schema relationships and conversion content semantically aligned so search and AI systems can extract the page accurately.", f"Primary query is '{query}' and the intelligence plan exposes {len(entities)} entities.", 0.97, "evidence_and_truth", (f"query:{query}", *(f"entity:{item}" for item in entities[:8])), ("visual abstraction can hide extractable meaning",), "Maintain semantic parity, headings and entity labels independent of visual ordering.", "All critical meaning remains in crawlable semantic HTML and structured data.")


DEFAULT_PROVIDERS: tuple[IntelligenceProvider, ...] = (
    ReferenceVisualAnalyst(), MotionInteractionAnalyst(), UXJourneyAnalyst(), IndustrialProductAnalyst(), BrandEditorialAnalyst(), PerformanceAccessibilityAnalyst(), CompetitiveDifferentiationAnalyst(), SEOAIKnowledgeGraphAnalyst(),
)


def _priority_rank(basis: str) -> int:
    try:
        return CONFLICT_PRIORITY.index(basis)
    except ValueError:
        return len(CONFLICT_PRIORITY)


def _resolve_conflicts(findings: Sequence[ProviderFinding]) -> tuple[list[dict[str, Any]], list[str]]:
    resolutions: list[dict[str, Any]] = []
    unresolved: list[str] = []
    by_domain: dict[str, list[ProviderFinding]] = {}
    for finding in findings:
        by_domain.setdefault(finding.domain, []).append(finding)
    for domain, candidates in by_domain.items():
        distinct = {item.recommendation for item in candidates}
        if len(distinct) <= 1:
            continue
        ordered = sorted(candidates, key=lambda item: (_priority_rank(item.priority_basis), -item.confidence, item.provider_id))
        winner = ordered[0]
        if len(ordered) > 1 and _priority_rank(ordered[0].priority_basis) == _priority_rank(ordered[1].priority_basis) and ordered[0].confidence == ordered[1].confidence:
            unresolved.append(f"Unresolved equal-priority conflict in {domain}")
            continue
        resolutions.append({"domain": domain, "winner": winner.provider_id, "priority_basis": winner.priority_basis, "recommendation": winner.recommendation, "superseded": [item.provider_id for item in ordered[1:]]})
    return resolutions, unresolved


def run_provider_pipeline(context: ProviderContext, providers: Sequence[IntelligenceProvider] = DEFAULT_PROVIDERS) -> dict[str, Any]:
    active = tuple(provider for provider in providers if provider.applies(context))
    findings = tuple(provider.analyze(context) for provider in active)
    required = tuple(provider.provider_id for provider in active if provider.required)
    successful = {item.provider_id for item in findings}
    missing_required = [provider_id for provider_id in required if provider_id not in successful]
    resolutions, unresolved = _resolve_conflicts(findings)
    confidence = round(sum(item.confidence for item in findings) / len(findings), 3) if findings else 0.0
    coverage = list(dict.fromkeys(item.domain for item in findings))
    provenance_ok = all(item.evidence or item.provider_id in {"brand_editorial_analyst", "performance_accessibility_analyst"} for item in findings)
    minimum_success = 5
    blockers = list(unresolved)
    if missing_required:
        blockers.append("Missing required providers: " + ", ".join(missing_required))
    if len(findings) < minimum_success:
        blockers.append(f"Provider quorum not met: {len(findings)}/{minimum_success}")
    if not provenance_ok:
        blockers.append("Provider provenance requirement failed")
    status = "ready" if not blockers else "needs_resolution"
    ordered_recommendations = sorted(findings, key=lambda item: (_priority_rank(item.priority_basis), -item.confidence, item.provider_id))
    return {
        "version": "2.0",
        "providers": [item.payload() for item in findings],
        "required_providers": list(required),
        "coverage": coverage,
        "confidence": confidence,
        "conflicts": unresolved,
        "conflict_resolutions": resolutions,
        "conflict_priority": list(CONFLICT_PRIORITY),
        "quorum": {"minimum_successful_providers": minimum_success, "successful": len(findings), "passed": len(findings) >= minimum_success},
        "provenance_required": True,
        "provenance_passed": provenance_ok,
        "synthesis": {"status": status, "blockers": blockers, "recommendations": [item.recommendation for item in ordered_recommendations]},
    }

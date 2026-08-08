from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping, Protocol, Sequence

from .content_composer import ContentPlan
from .creative_intelligence import CreativeIntelligencePlan
from .models import PageSpec
from .motion_composer import MotionPlan
from .pattern_resolver import PatternPlan


@dataclass(frozen=True)
class ProviderFinding:
    provider: str
    domain: str
    recommendation: str
    rationale: str
    confidence: float
    evidence: tuple[str, ...] = ()

    def payload(self) -> dict[str, Any]:
        return {"provider": self.provider, "domain": self.domain, "recommendation": self.recommendation, "rationale": self.rationale, "confidence": self.confidence, "evidence": list(self.evidence)}


@dataclass(frozen=True)
class ProviderContext:
    page: PageSpec
    content: ContentPlan
    intelligence: CreativeIntelligencePlan
    patterns: PatternPlan
    motion: MotionPlan
    references: Sequence[Mapping[str, str]]


class IntelligenceProvider(Protocol):
    name: str
    domain: str
    def analyze(self, context: ProviderContext) -> ProviderFinding: ...


class ResearchReferenceProvider:
    name = "research-reference-analyzer"; domain = "research_reference"
    def analyze(self, context: ProviderContext) -> ProviderFinding:
        names = tuple(str(item.get("name", "")) for item in context.references if item.get("name")); evidence = tuple(str(item.get("url", "")) for item in context.references if item.get("url"))
        return ProviderFinding(self.name, self.domain, "Translate approved reference principles into page-specific behavior; never copy source composition or signature interaction sequences.", f"{len(names)} approved references are available for principle-level translation: {', '.join(names)}.", 1.0 if evidence else 0.6, evidence)


class UXStorytellingProvider:
    name = "ux-storytelling-intelligence"; domain = "ux_storytelling"
    def analyze(self, context: ProviderContext) -> ProviderFinding:
        roles = tuple(block.role for block in context.content.blocks if block.role)
        return ProviderFinding(self.name, self.domain, "Make each section answer the next user question and advance one decision state toward the conversion goal.", f"The composed journey exposes {len(context.content.blocks)} content blocks and roles {roles or ('unassigned',)}.", 0.9, (f"intent:{context.content.primary_intent or context.intelligence.query.search_intent}",))


class VisualDirectionProvider:
    name = "visual-direction-intelligence"; domain = "visual_direction"
    def analyze(self, context: ProviderContext) -> ProviderFinding:
        return ProviderFinding(self.name, self.domain, "Use a page-specific visual system that exposes hierarchy, anatomy and evidence instead of relying on a generic card grid.", f"Visual profile is {context.page.visual_profile}; scroll model is {context.patterns.scroll_model}.", 0.9, (f"visual-profile:{context.page.visual_profile}", f"scroll-model:{context.patterns.scroll_model}"))


class MotionInteractionProvider:
    name = "motion-interaction-intelligence"; domain = "motion_interaction"
    def analyze(self, context: ProviderContext) -> ProviderFinding:
        cue_count = len(context.motion.cues)
        return ProviderFinding(self.name, self.domain, "Use motion only to reveal information, relationships, progress, state or depth; preserve touch, keyboard and reduced-motion equivalents.", f"The resolved motion plan contains {cue_count} cues and must remain semantic across desktop and mobile.", 0.95, (f"motion-cues:{cue_count}",))


class SEOAIKnowledgeGraphProvider:
    name = "seo-ai-knowledge-graph-intelligence"; domain = "seo_ai_knowledge_graph"
    def analyze(self, context: ProviderContext) -> ProviderFinding:
        query = context.intelligence.query.primary_query; entities = tuple(context.intelligence.semantic.entities)
        return ProviderFinding(self.name, self.domain, "Keep query intent, named entities, schema relationships and conversion content semantically aligned so search and AI systems can extract the page accurately.", f"Primary query is '{query}' and the intelligence plan exposes {len(entities)} entities.", 0.95, (f"query:{query}", *(f"entity:{item}" for item in entities[:8])))


DEFAULT_PROVIDERS: tuple[IntelligenceProvider, ...] = (ResearchReferenceProvider(), UXStorytellingProvider(), VisualDirectionProvider(), MotionInteractionProvider(), SEOAIKnowledgeGraphProvider())


def run_provider_pipeline(context: ProviderContext, providers: Sequence[IntelligenceProvider] = DEFAULT_PROVIDERS) -> dict[str, Any]:
    findings = tuple(provider.analyze(context) for provider in providers); domains = tuple(dict.fromkeys(item.domain for item in findings)); confidence = round(sum(item.confidence for item in findings) / len(findings), 3) if findings else 0.0
    conflicts: list[str] = []; by_domain: dict[str, set[str]] = {}
    for item in findings: by_domain.setdefault(item.domain, set()).add(item.recommendation)
    for domain, recommendations in by_domain.items():
        if len(recommendations) > 1: conflicts.append(f"Conflicting recommendations in {domain}")
    return {"version": "1.0", "providers": [item.payload() for item in findings], "coverage": list(domains), "confidence": confidence, "conflicts": conflicts, "synthesis": {"status": "ready" if findings and not conflicts else "needs_resolution", "recommendations": [item.recommendation for item in findings]}}

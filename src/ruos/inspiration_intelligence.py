from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass

from .models import PageSpec


class InspirationIntelligenceError(ValueError):
    """Raised when the approved inspiration corpus cannot support a design decision."""


@dataclass(frozen=True)
class InspirationReference:
    id: str
    title: str
    url: str
    source: str
    roles: tuple[str, ...]
    principles: tuple[str, ...]
    suitable_page_kinds: tuple[str, ...]
    evidence: tuple[str, ...]
    confidence: int

    def payload(self) -> dict[str, object]:
        return {
            "id": self.id,
            "title": self.title,
            "url": self.url,
            "source": self.source,
            "roles": list(self.roles),
            "principles": list(self.principles),
            "suitable_page_kinds": list(self.suitable_page_kinds),
            "evidence": list(self.evidence),
            "confidence": self.confidence,
        }


@dataclass(frozen=True)
class InspirationDecision:
    reference_id: str
    score: int
    reasons: tuple[str, ...]
    adopted_principles: tuple[str, ...]
    prohibited_actions: tuple[str, ...]

    def payload(self) -> dict[str, object]:
        return {
            "reference_id": self.reference_id,
            "score": self.score,
            "reasons": list(self.reasons),
            "adopted_principles": list(self.adopted_principles),
            "prohibited_actions": list(self.prohibited_actions),
        }


@dataclass(frozen=True)
class InspirationIntelligence:
    page_slug: str
    references: tuple[InspirationReference, ...]
    decisions: tuple[InspirationDecision, ...]
    synthesis: tuple[str, ...]
    visual_language: tuple[str, ...]
    scroll_language: tuple[str, ...]
    motion_language: tuple[str, ...]
    presentation_language: tuple[str, ...]
    evidence_status: str

    def payload(self) -> dict[str, object]:
        return {
            "page_slug": self.page_slug,
            "references": [item.payload() for item in self.references],
            "decisions": [item.payload() for item in self.decisions],
            "synthesis": list(self.synthesis),
            "visual_language": list(self.visual_language),
            "scroll_language": list(self.scroll_language),
            "motion_language": list(self.motion_language),
            "presentation_language": list(self.presentation_language),
            "evidence_status": self.evidence_status,
        }

    @property
    def sha256(self) -> str:
        canonical = json.dumps(self.payload(), ensure_ascii=False, sort_keys=True, separators=(",", ":"))
        return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


_APPROVED_REFERENCES = (
    InspirationReference(
        "fort-vega-scroll",
        "Fort Vega Website Scroll",
        "https://www.awwwards.com/inspiration/website-scroll-fort-vega",
        "Awwwards",
        ("scroll", "3d", "interactive", "animation"),
        ("continuous-scroll-narrative", "spatial-transition", "interactive-discovery"),
        ("hero", "story", "knowledge"),
        ("Awwwards classifies the element as scroll, 3d, interactive and animation.",),
        96,
    ),
    InspirationReference(
        "sky-clinics",
        "Sky Clinics",
        "https://www.awwwards.com/sites/sky-clinics",
        "Awwwards",
        ("motion", "healthcare", "presentation"),
        ("controlled-motion", "trust-led-presentation", "calm-visual-rhythm"),
        ("hero", "story", "conversion"),
        ("User-approved reference; source page retained for visual review.",),
        82,
    ),
    InspirationReference(
        "bucks-sauce",
        "Bucks Sauce",
        "https://www.awwwards.com/sites/bucks-sauce",
        "Awwwards",
        ("brand-personality", "product", "interaction"),
        ("distinct-brand-character", "product-slider", "stop-motion", "interactive-3d"),
        ("hero", "knowledge", "interaction"),
        (
            "Awwwards highlights a vertical menu, product slider, product-grid animation, stop-motion and interactive 3D.",
            "Awwwards records a deliberately restricted two-colour palette.",
        ),
        96,
    ),
    InspirationReference(
        "nrg-data-center",
        "NRG Build Your Data Center",
        "https://www.awwwards.com/sites/nrg-build-your-data-center",
        "Awwwards",
        ("industrial", "infrastructure", "scale", "structures"),
        ("industrial-monumentality", "system-construction", "large-scale-story", "spatial-composition"),
        ("hero", "story", "knowledge", "interaction", "conversion"),
        ("User explicitly approved this reference as the primary fit for the structures page.",),
        100,
    ),
    InspirationReference(
        "oryzo-ai",
        "Oryzo AI",
        "https://www.awwwards.com/sites/oryzo-ai",
        "Awwwards",
        ("presentation", "ai", "narrative", "motion"),
        ("presentation-as-experience", "coherent-visual-story", "motion-supports-meaning"),
        ("hero", "story", "knowledge", "conversion"),
        ("User explicitly approved the presentation quality as exceptional.",),
        100,
    ),
    InspirationReference(
        "xurya-manufacture",
        "Xurya Manufacture Landing Page",
        "https://dribbble.com/shots/24874505-Xurya-Manufacture-Landing-Page",
        "Dribbble",
        ("manufacturing", "landing-page", "ui"),
        ("manufacturing-hierarchy", "clean-grid", "structured-information"),
        ("hero", "knowledge", "conversion"),
        ("User-approved manufacturing UI reference.",),
        90,
    ),
    InspirationReference(
        "construction-insurtech",
        "Construction Insurtech B2B Landing Page",
        "https://dribbble.com/shots/27435782-Construction-Insurtech-B2B-Web-Design-SaaS-Landing-Page-UI",
        "Dribbble",
        ("construction", "b2b", "saas", "conversion"),
        ("b2b-clarity", "proof-led-layout", "commercial-hierarchy"),
        ("knowledge", "interaction", "conversion"),
        ("User-approved B2B construction UI reference.",),
        90,
    ),
)


def analyze_inspiration(page: PageSpec) -> InspirationIntelligence:
    if not page.sections:
        raise InspirationIntelligenceError("Inspiration analysis requires a page with sections")
    page_kinds = {section.kind for section in page.sections}
    ranked: list[tuple[int, InspirationDecision]] = []
    for reference in _APPROVED_REFERENCES:
        overlap = page_kinds & set(reference.suitable_page_kinds)
        raw_score = reference.confidence + min(6, len(overlap) * 2)
        priority = 0
        reasons = [f"evidence-confidence:{reference.confidence}"]
        if overlap:
            reasons.append("page-kind-fit:" + ",".join(sorted(overlap)))
        if page.slug == "structures" and reference.id == "nrg-data-center":
            raw_score += 8
            priority = 1
            reasons.append("user-declared-primary-structures-reference")
        ranked.append(
            (
                priority,
                InspirationDecision(
                    reference_id=reference.id,
                    score=min(100, raw_score),
                    reasons=tuple(reasons),
                    adopted_principles=reference.principles,
                    prohibited_actions=("copy-layout", "copy-code", "copy-brand-assets", "imitate-signature-composition"),
                ),
            )
        )
    ranked.sort(key=lambda item: (-item[0], -item[1].score, item[1].reference_id))
    decisions = tuple(item[1] for item in ranked)
    if len(decisions) < 5 or decisions[0].score < 90:
        raise InspirationIntelligenceError("Approved inspiration evidence is insufficient for production")
    return InspirationIntelligence(
        page_slug=page.slug,
        references=_APPROVED_REFERENCES,
        decisions=decisions,
        synthesis=(
            "Build one continuous visual argument instead of a stack of interchangeable cards.",
            "Use industrial scale and spatial depth for structures while preserving B2B clarity.",
            "Make presentation, interaction and motion reinforce one narrative idea.",
            "Adopt principles only; never reproduce a reference layout, code or branded asset.",
        ),
        visual_language=("industrial-monumentality", "editorial-clarity", "asymmetric-composition", "controlled-contrast"),
        scroll_language=("continuous-chapters", "pinned-reveal", "spatial-transition", "decision-led-progression"),
        motion_language=("narrative-cues", "camera-like-depth", "purposeful-state-feedback", "reduced-motion-equivalence"),
        presentation_language=("large-scale-opening", "proof-through-structure", "guided-comparison", "decisive-closing-stage"),
        evidence_status="ready",
    )

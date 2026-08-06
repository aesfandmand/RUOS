from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass

from .models import GateResult, PageSpec
from .quality_score import AgencyQualityScore
from .research_studio import ResearchBrief


class VirtualStudioError(ValueError):
    """Raised when the specialist review panel cannot reach a valid verdict."""


@dataclass(frozen=True)
class SpecialistVerdict:
    role: str
    discipline: str
    score: int
    passed: bool
    evidence: tuple[str, ...]
    blockers: tuple[str, ...]

    def payload(self) -> dict[str, object]:
        return {
            "role": self.role,
            "discipline": self.discipline,
            "score": self.score,
            "passed": self.passed,
            "evidence": list(self.evidence),
            "blockers": list(self.blockers),
        }


@dataclass(frozen=True)
class StudioReview:
    page_slug: str
    verdicts: tuple[SpecialistVerdict, ...]
    total_score: int
    unanimous: bool
    publishable: bool
    blockers: tuple[str, ...]

    def payload(self) -> dict[str, object]:
        return {
            "page_slug": self.page_slug,
            "verdicts": [verdict.payload() for verdict in self.verdicts],
            "total_score": self.total_score,
            "unanimous": self.unanimous,
            "publishable": self.publishable,
            "blockers": list(self.blockers),
        }

    @property
    def sha256(self) -> str:
        canonical = json.dumps(self.payload(), ensure_ascii=False, sort_keys=True, separators=(",", ":"))
        return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


_ROLE_GATES: tuple[tuple[str, str, tuple[str, ...]], ...] = (
    ("Creative Director", "creative-direction", ("creative-direction", "storytelling")),
    ("Art Director", "art-direction", ("creative-direction", "visual-rhythm")),
    ("UX Lead", "experience-design", ("reading-experience", "visual-rhythm", "interaction-accessibility")),
    ("UI Lead", "interface-design", ("creative-direction", "interaction-accessibility")),
    ("Motion Lead", "motion-design", ("motion", "storytelling")),
    ("Content Director", "content-design", ("reading-experience", "storytelling")),
    ("SEO Lead", "search-and-ai", ("seo-query-alignment", "ai-readiness")),
    ("CRO Lead", "conversion-design", ("conversion", "reading-experience")),
    ("Accessibility Lead", "inclusive-design", ("interaction-accessibility", "motion")),
    ("Front-end Lead", "engineering", ("performance", "interaction-accessibility")),
)


def _gate_map(gates: tuple[GateResult, ...]) -> dict[str, GateResult]:
    mapping = {gate.gate: gate for gate in gates}
    missing = sorted({name for _, _, names in _ROLE_GATES for name in names} - set(mapping))
    if missing:
        raise VirtualStudioError("Specialist review is missing QA gates: " + ", ".join(missing))
    return mapping


def conduct_virtual_studio_review(
    page: PageSpec,
    research: ResearchBrief,
    gates: tuple[GateResult, ...],
    quality: AgencyQualityScore,
) -> StudioReview:
    if research.page_slug != page.slug:
        raise VirtualStudioError("Research brief does not belong to the reviewed page")
    if research.evidence_status != "ready" or research.evidence_score < 75:
        raise VirtualStudioError("Virtual Studio requires production-ready research evidence")

    mapped = _gate_map(gates)
    verdicts: list[SpecialistVerdict] = []
    for role, discipline, gate_names in _ROLE_GATES:
        selected = tuple(mapped[name] for name in gate_names)
        score = round(sum(gate.score for gate in selected) / len(selected))
        blockers = tuple(
            f"{gate.gate}: {failure}"
            for gate in selected
            for failure in gate.failures
        )
        evidence = tuple(
            item
            for gate in selected
            for item in gate.evidence
        ) + (f"research_evidence_score={research.evidence_score}",)
        passed = score >= 85 and not blockers
        verdicts.append(
            SpecialistVerdict(
                role=role,
                discipline=discipline,
                score=score,
                passed=passed,
                evidence=evidence,
                blockers=blockers,
            )
        )

    total_score = round(sum(verdict.score for verdict in verdicts) / len(verdicts))
    all_blockers = tuple(
        f"{verdict.role}: {blocker}"
        for verdict in verdicts
        for blocker in verdict.blockers
    )
    unanimous = all(verdict.passed for verdict in verdicts)
    publishable = unanimous and total_score >= 88 and quality.publishable
    if not quality.publishable:
        all_blockers += tuple(f"Agency Quality: {blocker}" for blocker in quality.blockers)
    if total_score < 88:
        all_blockers += (f"Virtual Studio score {total_score} is below threshold 88",)

    return StudioReview(
        page_slug=page.slug,
        verdicts=tuple(verdicts),
        total_score=total_score,
        unanimous=unanimous,
        publishable=publishable,
        blockers=all_blockers,
    )

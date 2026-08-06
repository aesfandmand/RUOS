from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass

from .creative_selection import CreativeSelectionPlan
from .models import GateResult, PageSpec
from .quality_score import AgencyQualityScore


class DesignCriticError(ValueError):
    """Raised when a critique cannot be produced from a complete quality contract."""


@dataclass(frozen=True)
class CritiqueFinding:
    discipline: str
    severity: str
    score: int
    observation: str
    action: str
    evidence: tuple[str, ...]

    def payload(self) -> dict[str, object]:
        return {
            "discipline": self.discipline,
            "severity": self.severity,
            "score": self.score,
            "observation": self.observation,
            "action": self.action,
            "evidence": list(self.evidence),
        }


@dataclass(frozen=True)
class DesignCritique:
    page_slug: str
    findings: tuple[CritiqueFinding, ...]
    blockers: tuple[str, ...]
    improvement_backlog: tuple[str, ...]
    release_recommendation: str
    quality_score: int
    selection_sha256: str

    def payload(self) -> dict[str, object]:
        return {
            "page_slug": self.page_slug,
            "findings": [finding.payload() for finding in self.findings],
            "blockers": list(self.blockers),
            "improvement_backlog": list(self.improvement_backlog),
            "release_recommendation": self.release_recommendation,
            "quality_score": self.quality_score,
            "selection_sha256": self.selection_sha256,
        }

    @property
    def sha256(self) -> str:
        canonical = json.dumps(self.payload(), ensure_ascii=False, sort_keys=True, separators=(",", ":"))
        return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


_DISCIPLINE_ACTIONS = {
    "creative-direction": "Strengthen the singular creative idea and remove any generic visual treatment.",
    "reading-experience": "Improve paragraph rhythm, heading transitions and deliberate reading pauses.",
    "visual-rhythm": "Rebalance density, whitespace and section-to-section contrast across viewports.",
    "storytelling": "Clarify the causal arc from user problem to informed decision.",
    "interaction-accessibility": "Make every state operable, perceivable and announced to assistive technology.",
    "motion": "Tie every animation cue to narrative meaning and preserve reduced-motion parity.",
    "conversion": "Reduce decision friction and strengthen proof immediately before each CTA.",
    "seo-query-alignment": "Tighten query coverage, intent alignment and semantic answer structure.",
    "ai-readiness": "Increase entity clarity, extractable answers and schema consistency.",
    "performance": "Reduce rendering cost without weakening the approved visual direction.",
}


def _severity(gate: GateResult) -> str:
    if not gate.passed or gate.score < 70:
        return "blocker"
    if gate.score < 88:
        return "major"
    if gate.score < 95:
        return "refinement"
    return "strength"


def critique_design(
    page: PageSpec,
    gates: tuple[GateResult, ...],
    quality: AgencyQualityScore,
    selection: CreativeSelectionPlan,
) -> DesignCritique:
    if selection.page_slug != page.slug:
        raise DesignCriticError("Creative selection does not belong to the reviewed page")
    expected = set(_DISCIPLINE_ACTIONS)
    by_name = {gate.gate: gate for gate in gates}
    missing = sorted(expected - set(by_name))
    if missing:
        raise DesignCriticError("Design critique is missing QA gates: " + ", ".join(missing))

    findings: list[CritiqueFinding] = []
    blockers: list[str] = []
    backlog: list[str] = []
    for name in _DISCIPLINE_ACTIONS:
        gate = by_name[name]
        severity = _severity(gate)
        observation = (
            "; ".join(gate.failures)
            if gate.failures
            else f"{name} scored {gate.score}/100 against the production quality contract."
        )
        action = _DISCIPLINE_ACTIONS[name]
        findings.append(
            CritiqueFinding(
                discipline=name,
                severity=severity,
                score=gate.score,
                observation=observation,
                action=action,
                evidence=gate.evidence,
            )
        )
        if severity == "blocker":
            blockers.append(f"{name}: {observation}")
        elif severity in {"major", "refinement"}:
            backlog.append(f"{name}: {action}")

    for decision in selection.decisions:
        if decision.score < 95:
            backlog.append(
                f"library-{decision.category}: Re-evaluate {decision.candidate_id}; selection score is {decision.score}."
            )

    release = "reject" if blockers or not quality.publishable else "publish-with-backlog" if backlog else "publish"
    return DesignCritique(
        page_slug=page.slug,
        findings=tuple(findings),
        blockers=tuple(blockers),
        improvement_backlog=tuple(dict.fromkeys(backlog)),
        release_recommendation=release,
        quality_score=quality.total,
        selection_sha256=selection.sha256,
    )

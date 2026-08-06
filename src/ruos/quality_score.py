from __future__ import annotations

from dataclasses import dataclass

from .models import GateResult


class QualityScoreError(ValueError):
    pass


@dataclass(frozen=True)
class QualityDimension:
    name: str
    score: int
    weight: int


@dataclass(frozen=True)
class AgencyQualityScore:
    total: int
    grade: str
    publishable: bool
    dimensions: tuple[QualityDimension, ...]
    blockers: tuple[str, ...]

    def fingerprint_payload(self) -> tuple[tuple[str, object], ...]:
        return (
            ("total", self.total),
            ("grade", self.grade),
            ("publishable", self.publishable),
            ("dimensions", tuple((item.name, item.score, item.weight) for item in self.dimensions)),
            ("blockers", self.blockers),
        )


_WEIGHTS = {
    "creative-direction": 14,
    "reading-experience": 10,
    "visual-rhythm": 10,
    "storytelling": 10,
    "interaction-accessibility": 10,
    "motion": 8,
    "conversion": 14,
    "seo-query-alignment": 10,
    "ai-readiness": 8,
    "performance": 6,
}


def _grade(total: int) -> str:
    if total >= 95:
        return "A+"
    if total >= 90:
        return "A"
    if total >= 85:
        return "B+"
    if total >= 80:
        return "B"
    if total >= 70:
        return "C"
    return "F"


def calculate_agency_quality(gates: tuple[GateResult, ...], threshold: int = 88) -> AgencyQualityScore:
    by_name = {gate.gate: gate for gate in gates}
    missing = sorted(set(_WEIGHTS) - by_name.keys())
    unknown = sorted(by_name.keys() - set(_WEIGHTS))
    if missing:
        raise QualityScoreError(f"Missing quality gates: {', '.join(missing)}")
    if unknown:
        raise QualityScoreError(f"Unknown quality gates: {', '.join(unknown)}")
    if sum(_WEIGHTS.values()) != 100:
        raise QualityScoreError("Quality dimension weights must total 100")

    dimensions = tuple(
        QualityDimension(name=name, score=by_name[name].score, weight=weight)
        for name, weight in _WEIGHTS.items()
    )
    total = round(sum(item.score * item.weight for item in dimensions) / 100)
    blockers = tuple(
        f"{gate.gate}: {failure}"
        for gate in gates
        if not gate.passed
        for failure in gate.failures
    )
    publishable = not blockers and total >= threshold
    return AgencyQualityScore(
        total=total,
        grade=_grade(total),
        publishable=publishable,
        dimensions=dimensions,
        blockers=blockers,
    )

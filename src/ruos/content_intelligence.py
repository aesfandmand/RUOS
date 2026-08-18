"""Core scoring utilities for RUOS Content Intelligence Engine.

This module is intentionally dependency-free so the first usable version can run
inside the existing RUOS test suite without paid services or external APIs.
"""

from __future__ import annotations

from dataclasses import dataclass
from statistics import median
from typing import Iterable, Mapping


DEFAULT_WEIGHTS = {
    "demand": 0.20,
    "viral_potential": 0.20,
    "audience_pain": 0.15,
    "commercial_intent": 0.15,
    "brand_authority_fit": 0.10,
    "differentiation": 0.10,
    "production_feasibility": 0.05,
    "freshness": 0.05,
}


@dataclass(frozen=True)
class OpportunitySignals:
    """Normalized 0..100 signals for one content opportunity."""

    demand: float
    viral_potential: float
    audience_pain: float
    commercial_intent: float
    brand_authority_fit: float
    differentiation: float
    production_feasibility: float
    freshness: float

    def as_dict(self) -> dict[str, float]:
        return {
            "demand": self.demand,
            "viral_potential": self.viral_potential,
            "audience_pain": self.audience_pain,
            "commercial_intent": self.commercial_intent,
            "brand_authority_fit": self.brand_authority_fit,
            "differentiation": self.differentiation,
            "production_feasibility": self.production_feasibility,
            "freshness": self.freshness,
        }


def _validate_0_100(value: float, label: str) -> None:
    if not 0 <= value <= 100:
        raise ValueError(f"{label} must be between 0 and 100; got {value}")


def score_opportunity(
    signals: OpportunitySignals,
    weights: Mapping[str, float] | None = None,
) -> float:
    """Return weighted content opportunity score on a 0..100 scale."""

    values = signals.as_dict()
    for label, value in values.items():
        _validate_0_100(value, label)

    selected = dict(DEFAULT_WEIGHTS if weights is None else weights)
    missing = set(values) - set(selected)
    extra = set(selected) - set(values)
    if missing or extra:
        raise ValueError(
            f"weights must match signal keys; missing={sorted(missing)}, extra={sorted(extra)}"
        )

    total_weight = sum(selected.values())
    if abs(total_weight - 1.0) > 1e-9:
        raise ValueError(f"weights must sum to 1.0; got {total_weight}")
    if any(weight < 0 for weight in selected.values()):
        raise ValueError("weights cannot be negative")

    return round(sum(values[key] * selected[key] for key in values), 2)


def classify_opportunity(score: float) -> str:
    """Map score to the v0.1 planning buckets."""

    _validate_0_100(score, "score")
    if score >= 85:
        return "produce_now"
    if score >= 70:
        return "backlog"
    return "watch_or_reject"


def outlier_ratio(current_value: float, baseline_values: Iterable[float]) -> float:
    """Compare a content metric to the median of a baseline window.

    Median is preferred over mean because a single viral post should not inflate the
    normal baseline of an account.
    """

    if current_value < 0:
        raise ValueError("current_value cannot be negative")

    baseline = [float(value) for value in baseline_values]
    if not baseline:
        raise ValueError("baseline_values cannot be empty")
    if any(value < 0 for value in baseline):
        raise ValueError("baseline_values cannot contain negative numbers")

    baseline_median = median(baseline)
    if baseline_median == 0:
        return float("inf") if current_value > 0 else 0.0
    return round(current_value / baseline_median, 2)


def classify_outlier(ratio: float) -> str:
    """Classify an outlier ratio using the engine contract thresholds."""

    if ratio < 0:
        raise ValueError("ratio cannot be negative")
    if ratio >= 5:
        return "breakout"
    if ratio >= 3:
        return "strong_outlier"
    if ratio >= 2:
        return "outlier"
    return "normal"


def review_checkpoint(day: int) -> str | None:
    """Return the formal review checkpoint for a day in the 45-day cycle."""

    if day < 1:
        raise ValueError("day must be >= 1")
    return {
        15: "mini_review",
        30: "performance_review",
        45: "strategic_review",
    }.get(day)

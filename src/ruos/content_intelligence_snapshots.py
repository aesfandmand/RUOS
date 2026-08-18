"""Snapshot scheduling and derived metrics for Content Intelligence."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Iterable, Mapping


SNAPSHOT_TARGET_HOURS = (1, 6, 24, 72, 168, 720)


def media_age_hours(published_at: datetime, captured_at: datetime | None = None) -> float:
    """Return non-negative media age in hours."""

    captured_at = captured_at or datetime.now(timezone.utc)
    if published_at.tzinfo is None or captured_at.tzinfo is None:
        raise ValueError("published_at and captured_at must be timezone-aware")
    age = (captured_at - published_at).total_seconds() / 3600
    if age < 0:
        raise ValueError("captured_at cannot be before published_at")
    return age


def due_snapshot_target(
    age_hours: float,
    completed_targets: Iterable[int],
    *,
    tolerance_hours: float = 1.0,
) -> int | None:
    """Return the earliest snapshot target that is due and not completed.

    A target becomes due when content age reaches ``target - tolerance``. The caller
    records the returned target as completed after a successful snapshot.
    """

    if age_hours < 0:
        raise ValueError("age_hours cannot be negative")
    if tolerance_hours < 0:
        raise ValueError("tolerance_hours cannot be negative")
    completed = set(completed_targets)
    for target in SNAPSHOT_TARGET_HOURS:
        if target not in completed and age_hours >= max(0, target - tolerance_hours):
            return target
    return None


def metric_rate(numerator: float | int | None, denominator: float | int | None) -> float | None:
    """Return a percentage rate, or None when the denominator is unavailable/zero."""

    if numerator is None or denominator is None:
        return None
    if numerator < 0 or denominator < 0:
        raise ValueError("metrics cannot be negative")
    if denominator == 0:
        return None
    return round((float(numerator) / float(denominator)) * 100, 4)


def derive_instagram_rates(metrics: Mapping[str, float | int]) -> dict[str, float]:
    """Derive comparable rates from one Instagram owned snapshot.

    Reach is the preferred denominator because it answers "of people reached, how
    many acted?". Missing denominators simply omit the derived rate.
    """

    reach = metrics.get("reach")
    candidates = {
        "save_rate": metric_rate(metrics.get("saved"), reach),
        "share_rate": metric_rate(metrics.get("shares"), reach),
        "interaction_rate": metric_rate(metrics.get("total_interactions"), reach),
        "comment_rate": metric_rate(metrics.get("comments"), reach),
        "like_rate": metric_rate(metrics.get("likes"), reach),
    }
    return {key: value for key, value in candidates.items() if value is not None}


def view_velocity(
    current_views: float | int,
    current_age_hours: float,
    previous_views: float | int | None = None,
    previous_age_hours: float | None = None,
) -> float:
    """Return average views/hour, optionally between two snapshots."""

    if current_views < 0 or current_age_hours <= 0:
        raise ValueError("current_views must be >= 0 and current_age_hours > 0")

    if previous_views is None and previous_age_hours is None:
        return round(float(current_views) / current_age_hours, 4)
    if previous_views is None or previous_age_hours is None:
        raise ValueError("previous_views and previous_age_hours must be provided together")
    if previous_views < 0 or previous_age_hours < 0:
        raise ValueError("previous metrics cannot be negative")
    if current_age_hours <= previous_age_hours:
        raise ValueError("current_age_hours must be greater than previous_age_hours")
    delta_views = float(current_views) - float(previous_views)
    if delta_views < 0:
        # Platform corrections can reduce a metric; do not report negative velocity.
        delta_views = 0.0
    return round(delta_views / (current_age_hours - previous_age_hours), 4)

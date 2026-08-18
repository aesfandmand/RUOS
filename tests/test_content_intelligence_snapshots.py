from datetime import datetime, timezone

import pytest

from ruos.content_intelligence_snapshots import (
    derive_instagram_rates,
    due_snapshot_target,
    media_age_hours,
    metric_rate,
    view_velocity,
)


def test_due_snapshot_target_returns_current_checkpoint_only():
    assert due_snapshot_target(6.2, completed_targets=[1]) == 6
    assert due_snapshot_target(25, completed_targets=[1, 6, 24]) is None
    assert due_snapshot_target(73, completed_targets=[1, 6, 24]) == 72


def test_due_snapshot_target_does_not_fake_old_checkpoints():
    assert due_snapshot_target(100, completed_targets=[]) is None
    assert due_snapshot_target(8.9, completed_targets=[1]) == 6
    assert due_snapshot_target(9.1, completed_targets=[1]) is None


def test_instagram_rates_use_reach_denominator():
    metrics = {
        "reach": 1000,
        "saved": 50,
        "shares": 20,
        "total_interactions": 120,
        "comments": 10,
        "likes": 90,
    }
    assert derive_instagram_rates(metrics) == {
        "save_rate": 5.0,
        "share_rate": 2.0,
        "interaction_rate": 12.0,
        "comment_rate": 1.0,
        "like_rate": 9.0,
    }


def test_metric_rate_handles_missing_or_zero_denominator():
    assert metric_rate(5, None) is None
    assert metric_rate(5, 0) is None
    with pytest.raises(ValueError):
        metric_rate(-1, 100)


def test_view_velocity_can_use_full_age_or_snapshot_delta():
    assert view_velocity(1200, 6) == 200.0
    assert view_velocity(1800, 6, previous_views=600, previous_age_hours=2) == 300.0


def test_media_age_requires_timezone_aware_datetimes():
    published = datetime(2026, 8, 18, 0, tzinfo=timezone.utc)
    captured = datetime(2026, 8, 18, 6, tzinfo=timezone.utc)
    assert media_age_hours(published, captured) == 6.0
    with pytest.raises(ValueError):
        media_age_hours(datetime(2026, 8, 18, 0), captured)

import math

import pytest

from ruos.content_intelligence import (
    OpportunitySignals,
    classify_opportunity,
    classify_outlier,
    outlier_ratio,
    review_checkpoint,
    score_opportunity,
)


def test_score_opportunity_uses_locked_weights():
    signals = OpportunitySignals(
        demand=90,
        viral_potential=80,
        audience_pain=90,
        commercial_intent=100,
        brand_authority_fit=80,
        differentiation=70,
        production_feasibility=100,
        freshness=60,
    )
    assert score_opportunity(signals) == 85.5
    assert classify_opportunity(score_opportunity(signals)) == "produce_now"


def test_score_rejects_out_of_range_signal():
    signals = OpportunitySignals(101, 0, 0, 0, 0, 0, 0, 0)
    with pytest.raises(ValueError):
        score_opportunity(signals)


def test_outlier_ratio_uses_median_not_mean():
    baseline = [1000, 1100, 900, 1050, 50000]
    ratio = outlier_ratio(4200, baseline)
    assert ratio == 4.0
    assert classify_outlier(ratio) == "strong_outlier"


def test_zero_baseline_is_explicit():
    assert math.isinf(outlier_ratio(100, [0, 0, 0]))
    assert outlier_ratio(0, [0, 0, 0]) == 0.0


def test_review_checkpoints_match_30_45_model():
    assert review_checkpoint(15) == "mini_review"
    assert review_checkpoint(30) == "performance_review"
    assert review_checkpoint(45) == "strategic_review"
    assert review_checkpoint(22) is None

import pytest

from ruos.cie_lod_policy import build_lod_policy, validate_lod_metrics


def test_default_lod_policy_has_ordered_ratios():
    policy = build_lod_policy()
    assert policy["medium_ratio"] < policy["high_ratio"]
    assert policy["revalidate_glb_after_generation"] is True


def test_invalid_lod_ratios_are_blocked():
    with pytest.raises(ValueError):
        build_lod_policy({"medium_ratio": 0.8, "high_ratio": 0.7})


def test_lod_metrics_pass_meaningful_reduction():
    policy = build_lod_policy()
    report = validate_lod_metrics(100000, 75000, 45000, policy)
    assert report["status"] == "pass"


def test_lod_metrics_block_fake_or_insufficient_reduction():
    policy = build_lod_policy()
    report = validate_lod_metrics(100000, 95000, 90000, policy)
    assert report["status"] == "blocked"
    assert report["failures"]

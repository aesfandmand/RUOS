from __future__ import annotations

from dataclasses import replace
from datetime import datetime, timedelta, timezone

import pytest

from ruos.open_source_registry import OpenSourceAsset, OpenSourceRegistry, OpenSourceRegistryError
from ruos.open_source_registry_verifier import verify_open_source_registry


NOW = datetime(2026, 8, 6, 6, 0, tzinfo=timezone.utc)


def _asset(index: int, category: str, *, production: int = 90, observed_at: str = "2026-08-06T05:00:00Z") -> OpenSourceAsset:
    return OpenSourceAsset(
        id=f"asset-{index}", name=f"Asset {index}", category=category,
        repository_url=f"https://github.com/example/repo-{index}", homepage_url="",
        package_name=f"asset-{index}", license_spdx="MIT", version="v1",
        source_commit=(hex(index + 10)[2:] * 40)[:40], observed_at=observed_at,
        stars=100, open_issues=1, days_since_push=1,
        maintenance_score=90, documentation_score=90, accessibility_score=90,
        performance_score=90, rtl_score=90, ecosystem_score=90,
        production_score=production, capabilities=("production",), constraints=(),
    )


def _registry() -> OpenSourceRegistry:
    categories = ("accessibility", "animation", "component", "font", "icon", "qa", "scroll", "color")
    return OpenSourceRegistry.build(_asset(index, category) for index, category in enumerate(categories))


def test_verifier_accepts_fresh_complete_registry() -> None:
    verified = verify_open_source_registry(_registry(), now=NOW)

    assert verified.asset_count == 8
    assert verified.oldest_age_hours == 1
    assert verified.snapshot_sha256 == _registry().sha256
    assert "accessibility" in verified.categories


def test_verifier_rejects_stale_asset() -> None:
    registry = _registry()
    stale = replace(registry.assets[0], observed_at="2026-07-01T00:00:00Z")
    altered = OpenSourceRegistry.build((stale, *registry.assets[1:]))

    with pytest.raises(OpenSourceRegistryError, match="is stale"):
        verify_open_source_registry(altered, now=NOW, max_age=timedelta(days=14))


def test_verifier_rejects_missing_production_category() -> None:
    registry = _registry()
    weak_icon = replace(next(item for item in registry.assets if item.category == "icon"), production_score=20)
    altered = OpenSourceRegistry.build(
        weak_icon if item.category == "icon" else item for item in registry.assets
    )

    with pytest.raises(OpenSourceRegistryError, match="icon"):
        verify_open_source_registry(altered, now=NOW)


def test_verifier_rejects_insufficient_asset_count() -> None:
    with pytest.raises(OpenSourceRegistryError, match="minimum is 8"):
        verify_open_source_registry(OpenSourceRegistry.build(_registry().assets[:7]), now=NOW)

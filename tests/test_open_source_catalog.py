from __future__ import annotations

from datetime import datetime, timezone

import pytest

from ruos.open_source_catalog import RegistrySeed, refresh_open_source_registry
from ruos.open_source_registry import OpenSourceAsset, OpenSourceRegistryError


SEEDS = (
    RegistrySeed("one/repo", "one", "One", "icon", "one", (90, 90, 90, 90, 90, 90, 90), ("svg",)),
    RegistrySeed("two/repo", "two", "Two", "qa", "two", (80, 80, 80, 80, 80, 80, 80), ("ci",)),
)


class FakeBuilder:
    def __init__(self, failures: tuple[str, ...] = ()) -> None:
        self.failures = set(failures)
        self.calls: list[str] = []

    def build_asset(self, repository: str, **kwargs: object) -> OpenSourceAsset:
        self.calls.append(repository)
        if repository in self.failures:
            raise OpenSourceRegistryError("unavailable")
        return OpenSourceAsset(
            id=str(kwargs["asset_id"]),
            name=str(kwargs["name"]),
            category=str(kwargs["category"]),
            repository_url=f"https://github.com/{repository}",
            homepage_url="",
            package_name=str(kwargs["package_name"]),
            license_spdx="MIT",
            version="v1.0.0",
            source_commit="a" * 40,
            observed_at=datetime(2026, 8, 6, tzinfo=timezone.utc).isoformat().replace("+00:00", "Z"),
            stars=100,
            open_issues=2,
            days_since_push=1,
            maintenance_score=int(kwargs["maintenance_score"]),
            documentation_score=int(kwargs["documentation_score"]),
            accessibility_score=int(kwargs["accessibility_score"]),
            performance_score=int(kwargs["performance_score"]),
            rtl_score=int(kwargs["rtl_score"]),
            ecosystem_score=int(kwargs["ecosystem_score"]),
            production_score=int(kwargs["production_score"]),
            capabilities=tuple(kwargs["capabilities"]),
            constraints=tuple(kwargs["constraints"]),
        )


def test_refresh_builds_deterministic_registry_from_live_evidence() -> None:
    first, failures = refresh_open_source_registry(FakeBuilder(), seeds=SEEDS)
    second, _ = refresh_open_source_registry(FakeBuilder(), seeds=reversed(SEEDS))

    assert failures == ()
    assert tuple(asset.id for asset in first.assets) == ("one", "two")
    assert first.sha256 == second.sha256


def test_refresh_can_tolerate_explicitly_budgeted_failures() -> None:
    registry, failures = refresh_open_source_registry(
        FakeBuilder(("two/repo",)), seeds=SEEDS, minimum_success=1
    )

    assert tuple(asset.id for asset in registry.assets) == ("one",)
    assert failures == ("two/repo: unavailable",)


def test_refresh_rejects_when_success_threshold_is_not_met() -> None:
    with pytest.raises(OpenSourceRegistryError, match="accepted 1 assets; minimum is 2"):
        refresh_open_source_registry(FakeBuilder(("two/repo",)), seeds=SEEDS)


def test_refresh_rejects_invalid_threshold() -> None:
    with pytest.raises(OpenSourceRegistryError, match="minimum_success"):
        refresh_open_source_registry(FakeBuilder(), seeds=SEEDS, minimum_success=3)

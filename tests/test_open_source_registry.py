from __future__ import annotations

from dataclasses import replace

import pytest

from ruos.open_source_registry import (
    OpenSourceAsset,
    OpenSourceRegistry,
    OpenSourceRegistryError,
)


def _asset(asset_id: str = "lucide", **overrides) -> OpenSourceAsset:
    base = OpenSourceAsset(
        id=asset_id,
        name=asset_id.title(),
        category="icon",
        repository_url=f"https://github.com/example/{asset_id}",
        homepage_url=f"https://{asset_id}.example.com",
        package_name=f"@ruos/{asset_id}",
        license_spdx="ISC",
        version="1.0.0",
        source_commit="abcdef1234567890",
        observed_at="2026-08-06T06:30:00Z",
        stars=1000,
        open_issues=10,
        days_since_push=2,
        maintenance_score=90,
        documentation_score=88,
        accessibility_score=92,
        performance_score=94,
        rtl_score=96,
        ecosystem_score=89,
        production_score=93,
        capabilities=("svg", "tree-shaking", "rtl-safe"),
        constraints=("stroke-based",),
    )
    return replace(base, **overrides)


def test_registry_is_deterministic_independent_of_input_order() -> None:
    first = OpenSourceRegistry.build((_asset("phosphor"), _asset("lucide")))
    second = OpenSourceRegistry.build((_asset("lucide"), _asset("phosphor")))

    assert first.payload() == second.payload()
    assert first.sha256 == second.sha256
    assert [item.id for item in first.assets] == ["lucide", "phosphor"]


def test_registry_ranks_by_weighted_production_quality() -> None:
    stronger = _asset("lucide", production_score=99, accessibility_score=98)
    weaker = _asset("icons-basic", production_score=60, accessibility_score=55)
    registry = OpenSourceRegistry.build((weaker, stronger))

    ranked = registry.ranked("icon", minimum_score=70, required_capabilities=("svg", "rtl-safe"))

    assert [item.id for item in ranked] == ["lucide"]
    assert ranked[0].composite_score > weaker.composite_score


def test_registry_rejects_unapproved_license() -> None:
    with pytest.raises(OpenSourceRegistryError, match="License is not approved"):
        _asset(license_spdx="GPL-3.0")


def test_registry_rejects_duplicate_repositories() -> None:
    first = _asset("one")
    second = _asset("two", repository_url=first.repository_url)

    with pytest.raises(OpenSourceRegistryError, match="duplicate repositories"):
        OpenSourceRegistry.build((first, second))


def test_registry_rejects_untrusted_urls_and_invalid_scores() -> None:
    with pytest.raises(OpenSourceRegistryError, match="public HTTPS"):
        _asset(repository_url="http://localhost/repo")
    with pytest.raises(OpenSourceRegistryError, match="between 0 and 100"):
        _asset(performance_score=101)


def test_registry_payload_contains_traceable_source_and_license() -> None:
    asset = _asset()
    payload = OpenSourceRegistry.build((asset,)).payload()
    item = payload["assets"][0]

    assert item["repository_url"] == asset.repository_url
    assert item["source_commit"] == asset.source_commit
    assert item["license_spdx"] == "ISC"
    assert item["scores"]["composite"] == asset.composite_score

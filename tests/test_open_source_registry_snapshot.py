from __future__ import annotations

import json
from pathlib import Path

import pytest

from ruos.open_source_registry import OpenSourceAsset, OpenSourceRegistry, OpenSourceRegistryError
from ruos.open_source_registry_snapshot import load_registry, write_registry


def _registry() -> OpenSourceRegistry:
    return OpenSourceRegistry.build(
        (
            OpenSourceAsset(
                id="lucide",
                name="Lucide",
                category="icon",
                repository_url="https://github.com/lucide-icons/lucide",
                homepage_url="https://lucide.dev",
                package_name="lucide",
                license_spdx="ISC",
                version="v1.0.0",
                source_commit="a" * 40,
                observed_at="2026-08-06T00:00:00Z",
                stars=20000,
                open_issues=100,
                days_since_push=5,
                maintenance_score=95,
                documentation_score=92,
                accessibility_score=90,
                performance_score=94,
                rtl_score=95,
                ecosystem_score=93,
                production_score=95,
                capabilities=("svg", "rtl-safe", "tree-shakable"),
                constraints=(),
            ),
        )
    )


def test_registry_snapshot_round_trip(tmp_path: Path) -> None:
    path = tmp_path / "registry.json"
    expected = _registry()
    write_registry(expected, path)
    loaded = load_registry(path)

    assert loaded.payload() == expected.payload()
    assert loaded.sha256 == expected.sha256


def test_registry_snapshot_rejects_tampering(tmp_path: Path) -> None:
    path = tmp_path / "registry.json"
    write_registry(_registry(), path)
    raw = json.loads(path.read_text(encoding="utf-8"))
    raw["assets"][0]["metrics"]["stars"] = 999999
    path.write_text(json.dumps(raw), encoding="utf-8")

    with pytest.raises(OpenSourceRegistryError, match="checksum"):
        load_registry(path)


def test_registry_snapshot_rejects_wrong_asset_count(tmp_path: Path) -> None:
    path = tmp_path / "registry.json"
    write_registry(_registry(), path)
    raw = json.loads(path.read_text(encoding="utf-8"))
    raw["asset_count"] = 2
    path.write_text(json.dumps(raw), encoding="utf-8")

    with pytest.raises(OpenSourceRegistryError, match="asset count"):
        load_registry(path)

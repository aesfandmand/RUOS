from __future__ import annotations

from pathlib import Path

from ruos import cli
from ruos.open_source_registry import OpenSourceAsset, OpenSourceRegistry


def _registry() -> OpenSourceRegistry:
    return OpenSourceRegistry.build((
        OpenSourceAsset(
            id="lucide",
            name="Lucide",
            category="icon",
            repository_url="https://github.com/lucide-icons/lucide",
            homepage_url="https://lucide.dev",
            package_name="lucide",
            license_spdx="ISC",
            version="v1",
            source_commit="a" * 40,
            observed_at="2026-08-06T06:00:00Z",
            stars=100,
            open_issues=1,
            days_since_push=0,
            maintenance_score=90,
            documentation_score=90,
            accessibility_score=90,
            performance_score=90,
            rtl_score=90,
            ecosystem_score=90,
            production_score=90,
            capabilities=("svg",),
            constraints=(),
        ),
    ))


def test_registry_refresh_writes_snapshot_without_page_spec(monkeypatch, tmp_path: Path, capsys) -> None:
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(cli, "refresh_open_source_registry", lambda minimum_success: (_registry(), ()))

    code = cli.main(("registry", "refresh", "--minimum-success", "1"))

    assert code == 0
    output = tmp_path / ".ruos/registry/open-source.json"
    assert output.exists()
    captured = capsys.readouterr()
    assert "RUOS REGISTRY ASSETS: 1" in captured.out
    assert "RUOS REGISTRY SHA256:" in captured.out


def test_registry_refresh_reports_skipped_assets(monkeypatch, tmp_path: Path, capsys) -> None:
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(
        cli,
        "refresh_open_source_registry",
        lambda minimum_success: (_registry(), ("example/repo: unavailable",)),
    )

    assert cli.main(("registry", "refresh", "--minimum-success", "1")) == 0
    assert "RUOS REGISTRY SKIPPED: example/repo: unavailable" in capsys.readouterr().err

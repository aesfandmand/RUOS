from __future__ import annotations

from pathlib import Path

import yaml

from ruos import cli


def _write_registries(root: Path) -> None:
    root.mkdir(parents=True, exist_ok=True)
    (root / "architecture-entity-registry-v2.1.yaml").write_text(yaml.dump({
        "records": [{
            "id": "CORE-001",
            "commercial_status": "ACTIVE",
            "publication_status": "INDEX",
            "indexability": "index",
            "url_candidate": "/",
            "url_status": "KEEP",
            "page_level": "ROOT",
            "page_type": "HOME",
        }]
    }), encoding="utf-8")
    (root / "structure-page-registry-v2.1.yaml").write_text(
        yaml.dump({"records": []}), encoding="utf-8")


def test_next_reports_the_top_candidate(monkeypatch, tmp_path: Path, capsys) -> None:
    monkeypatch.chdir(tmp_path)
    registry_root = tmp_path / "registries"
    _write_registries(registry_root)

    code = cli.main(("next", "--registry-root", str(registry_root)))

    assert code == 0
    out = capsys.readouterr().out
    assert "RUOS NEXT: home" in out
    assert "RUOS NEXT SOURCE: entity CORE-001" in out


def test_next_fails_clearly_when_the_registry_is_missing(monkeypatch, tmp_path: Path, capsys) -> None:
    monkeypatch.chdir(tmp_path)

    code = cli.main(("next", "--registry-root", str(tmp_path / "does-not-exist")))

    assert code == 2
    assert "RUOS NEXT FAILED" in capsys.readouterr().err


def test_next_exits_nonzero_when_nothing_is_buildable(monkeypatch, tmp_path: Path, capsys) -> None:
    monkeypatch.chdir(tmp_path)
    registry_root = tmp_path / "registries"
    registry_root.mkdir()
    (registry_root / "architecture-entity-registry-v2.1.yaml").write_text(
        yaml.dump({"records": [{"id": "ENT-001", "commercial_status": "FUTURE"}]}), encoding="utf-8")
    (registry_root / "structure-page-registry-v2.1.yaml").write_text(
        yaml.dump({"records": []}), encoding="utf-8")

    code = cli.main(("next", "--registry-root", str(registry_root)))

    assert code == 2
    assert "no buildable page found" in capsys.readouterr().err

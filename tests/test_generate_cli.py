from __future__ import annotations

import json
from pathlib import Path

import yaml

from ruos import cli, generate as generate_module
from ruos.design_approach import MATCHED, DesignApproach, DesignApproachResult

REAL_SPEC = json.loads(Path("pages/blocks/urban-investment.json").read_text(encoding="utf-8"))


def _mini_composable_spec(slug: str) -> dict:
    spec = dict(REAL_SPEC)
    spec["slug"] = slug
    spec["blocks"] = [b for b in REAL_SPEC["blocks"] if b["block"] in ("hero-scroll-scene", "review-gate")]
    return spec


def test_generate_reports_a_blocked_queue_with_no_matched_design(monkeypatch, tmp_path: Path, capsys) -> None:
    monkeypatch.chdir(tmp_path)
    registry_root = tmp_path / "registry"
    registry_root.mkdir()
    (registry_root / "architecture-entity-registry-v2.1.yaml").write_text(yaml.dump({
        "records": [{
            "id": "CORE-001", "commercial_status": "ACTIVE", "publication_status": "INDEX",
            "indexability": "index", "url_candidate": "/", "url_status": "KEEP",
            "page_level": "ROOT", "page_type": "HOME",
        }]
    }), encoding="utf-8")
    (registry_root / "structure-page-registry-v2.1.yaml").write_text(yaml.dump({"records": []}), encoding="utf-8")

    code = cli.main(("generate", "--registry-root", str(registry_root)))

    assert code == 2
    captured = capsys.readouterr()
    assert "RUOS GENERATE ATTEMPT: CORE-001 home -> NO DESIGN APPROACH YET" in captured.out
    assert "RUOS GENERATE: no page in the current build queue is ready end-to-end" in captured.err


def test_generate_writes_a_composed_page_when_everything_is_ready(monkeypatch, tmp_path: Path, capsys) -> None:
    library_root = Path.cwd() / "blocks"  # the real, on-disk block library
    monkeypatch.chdir(tmp_path)

    registry_root = tmp_path / "registry"
    registry_root.mkdir()
    (registry_root / "architecture-entity-registry-v2.1.yaml").write_text(yaml.dump({
        "records": [{
            "id": "TEST-001", "commercial_status": "ACTIVE", "publication_status": "INDEX",
            "indexability": "index", "url_candidate": "/mini-test-page/", "url_status": "KEEP",
            "page_level": "LANDING", "page_type": "TEST_PAGE_TYPE",
        }]
    }), encoding="utf-8")
    (registry_root / "structure-page-registry-v2.1.yaml").write_text(yaml.dump({"records": []}), encoding="utf-8")

    spec_dir = tmp_path / "pages" / "blocks"
    spec_dir.mkdir(parents=True)
    (spec_dir / "mini-test-page.json").write_text(json.dumps(_mini_composable_spec("mini-test-page")), encoding="utf-8")

    small_approach = DesignApproach(
        id="mini-approach", name="mini", block_sequence=("hero-scroll-scene", "review-gate"),
        source_reference="test", note="test",
    )
    monkeypatch.setattr(generate_module, "select_design_approach",
                         lambda page_type: DesignApproachResult(page_type or "", MATCHED, small_approach, "matched"))

    code = cli.main((
        "generate",
        "--registry-root", str(registry_root),
        "--spec-root", str(spec_dir),
        "--library", str(library_root),
        "--output", "dist",
    ))

    assert code == 0
    captured = capsys.readouterr()
    assert "RUOS GENERATE PASSED" in captured.out
    output_dir = tmp_path / "dist" / "mini-test-page"
    assert (output_dir / "index.html").is_file()
    assert (output_dir / "compose-manifest.json").is_file()

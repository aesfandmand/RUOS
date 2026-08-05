import json
from pathlib import Path

from ruos.compiler import compile_page
from ruos.models import BuildContext
from ruos.spec_loader import load_page_spec


def _build(tmp_path: Path):
    page = load_page_spec(Path("pages/structures.json"))
    return compile_page(
        page,
        BuildContext(project_root=Path.cwd(), output_root=tmp_path, strict=True),
    )


def test_structures_build_passes(tmp_path: Path) -> None:
    result = _build(tmp_path)

    assert result.passed
    assert (result.output_dir / "index.html").exists()
    assert (result.output_dir / "assets/styles.css").exists()
    assert (result.output_dir / "assets/runtime.js").exists()
    assert (result.output_dir / "build-manifest.json").exists()
    assert (result.output_dir / "qa-report.json").exists()
    assert (result.output_dir / ".ruos-build").exists()
    assert len(result.gates) == 10


def test_build_id_and_artifact_hashes_are_reproducible(tmp_path: Path) -> None:
    first = _build(tmp_path)
    first_manifest = json.loads((first.output_dir / "build-manifest.json").read_text(encoding="utf-8"))
    first_html = (first.output_dir / "index.html").read_bytes()

    second = _build(tmp_path)
    second_manifest = json.loads((second.output_dir / "build-manifest.json").read_text(encoding="utf-8"))

    assert second_manifest["build_id"] == first_manifest["build_id"]
    assert second_manifest["sha256"] == first_manifest["sha256"]
    assert second_manifest["pattern_plan_sha256"] == first_manifest["pattern_plan_sha256"]
    assert (second.output_dir / "index.html").read_bytes() == first_html
    assert not list(tmp_path.glob(".ruos-structures-*"))
    assert not (tmp_path / ".structures.previous").exists()


def test_manifest_only_lists_public_artifacts(tmp_path: Path) -> None:
    result = _build(tmp_path)
    manifest = json.loads((result.output_dir / "build-manifest.json").read_text(encoding="utf-8"))

    assert manifest["files"] == [
        "index.html",
        "assets/styles.css",
        "assets/runtime.js",
    ]
    assert manifest["page"] == "structures"
    assert manifest["passed"] is True
    assert manifest["pattern_plan"]["narrative_arc"] == "discover-understand-decide-act"
    assert manifest["pattern_plan"]["global_motif"] == "red-umbrella-orbit"
    assert len(manifest["pattern_plan"]["sections"]) == 5
    assert len(manifest["pattern_plan_sha256"]) == 64
    assert all(len(value) == 64 for value in manifest["sha256"].values())

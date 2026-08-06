import json
from pathlib import Path

from ruos.compiler import compile_page
from ruos.models import BuildContext
from ruos.spec_loader import load_page_spec


STUDIO_ARTIFACTS = [
    "studio/manifest.json",
    "studio/research.json",
    "studio/query-intelligence.json",
    "studio/competitive-analysis.json",
    "studio/pattern-selection.json",
    "studio/knowledge-graph.json",
    "studio/component-selection.json",
    "studio/design-brief.json",
    "studio/creative-direction.json",
    "studio/art-direction.json",
    "studio/ux-plan.json",
    "studio/ui-plan.json",
    "studio/motion-plan.json",
    "studio/content-plan.json",
    "studio/seo-plan.json",
    "studio/cro-plan.json",
    "studio/design-critique.json",
    "studio/agency-review.json",
]


def _build(tmp_path: Path):
    page = load_page_spec(Path("pages/structures.json"))
    return compile_page(page, BuildContext(project_root=Path.cwd(), output_root=tmp_path, strict=True))


def test_structures_build_passes(tmp_path: Path) -> None:
    result = _build(tmp_path)
    assert result.passed
    assert (result.output_dir / "index.html").exists()
    assert (result.output_dir / "assets/styles.css").exists()
    assert (result.output_dir / "assets/runtime.js").exists()
    assert (result.output_dir / "assets/motion-manifest.json").exists()
    assert (result.output_dir / "assets/creative-intelligence.json").exists()
    assert (result.output_dir / "agency-quality-report.json").exists()
    assert (result.output_dir / "build-manifest.json").exists()
    assert (result.output_dir / "qa-report.json").exists()
    assert (result.output_dir / ".ruos-build").exists()
    for relative_path in STUDIO_ARTIFACTS:
        assert (result.output_dir / relative_path).exists()
    assert len(result.gates) == 10


def test_build_id_and_artifact_hashes_are_reproducible(tmp_path: Path) -> None:
    first = _build(tmp_path)
    first_manifest = json.loads((first.output_dir / "build-manifest.json").read_text(encoding="utf-8"))
    first_html = (first.output_dir / "index.html").read_bytes()
    first_motion = (first.output_dir / "assets/motion-manifest.json").read_bytes()
    first_intelligence = (first.output_dir / "assets/creative-intelligence.json").read_bytes()
    first_quality = (first.output_dir / "agency-quality-report.json").read_bytes()
    first_studio = {relative_path: (first.output_dir / relative_path).read_bytes() for relative_path in STUDIO_ARTIFACTS}

    second = _build(tmp_path)
    second_manifest = json.loads((second.output_dir / "build-manifest.json").read_text(encoding="utf-8"))

    assert second_manifest["build_id"] == first_manifest["build_id"]
    assert second_manifest["sha256"] == first_manifest["sha256"]
    assert second_manifest["pattern_plan_sha256"] == first_manifest["pattern_plan_sha256"]
    assert second_manifest["motion_plan_sha256"] == first_manifest["motion_plan_sha256"]
    assert second_manifest["creative_intelligence_sha256"] == first_manifest["creative_intelligence_sha256"]
    assert second_manifest["agency_quality_sha256"] == first_manifest["agency_quality_sha256"]
    assert (second.output_dir / "index.html").read_bytes() == first_html
    assert (second.output_dir / "assets/motion-manifest.json").read_bytes() == first_motion
    assert (second.output_dir / "assets/creative-intelligence.json").read_bytes() == first_intelligence
    assert (second.output_dir / "agency-quality-report.json").read_bytes() == first_quality
    for relative_path, first_bytes in first_studio.items():
        assert (second.output_dir / relative_path).read_bytes() == first_bytes
    assert not list(tmp_path.glob(".ruos-structures-*"))
    assert not (tmp_path / ".structures.previous").exists()


def test_manifest_lists_every_public_and_studio_artifact(tmp_path: Path) -> None:
    result = _build(tmp_path)
    manifest = json.loads((result.output_dir / "build-manifest.json").read_text(encoding="utf-8"))
    quality = json.loads((result.output_dir / "agency-quality-report.json").read_text(encoding="utf-8"))

    assert manifest["files"] == [
        "index.html",
        "assets/styles.css",
        "assets/runtime.js",
        "assets/motion-manifest.json",
        "assets/creative-intelligence.json",
        "agency-quality-report.json",
        *STUDIO_ARTIFACTS,
    ]
    assert manifest["page"] == "structures"
    assert manifest["passed"] is True
    assert manifest["pattern_plan"]["narrative_arc"] == "discover-understand-decide-act"
    assert len(manifest["pattern_plan_sha256"]) == 64
    assert manifest["motion_plan"]["strategy"] == "chapter-aware-progressive-motion"
    assert len(manifest["motion_plan_sha256"]) == 64
    assert manifest["creative_intelligence"]["query"]["search_intent"] == "commercial-investigation"
    assert manifest["creative_intelligence"]["sales"]["conversion_goal"] == "qualified-conversation"
    assert "FAQPage" in manifest["creative_intelligence"]["semantic"]["schema_types"]
    assert len(manifest["creative_intelligence_sha256"]) == 64
    assert quality["publishable"] is True
    assert quality["total"] >= quality["threshold"]
    assert quality["blockers"] == []
    assert len(manifest["agency_quality_sha256"]) == 64
    assert all(len(value) == 64 for value in manifest["sha256"].values())
    assert set(manifest["sha256"]) == set(manifest["files"])

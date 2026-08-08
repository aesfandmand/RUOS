import json
from pathlib import Path

from ruos.cie_build import compile_page_with_cie
from ruos.cie_lod_build import materialize_post_lod_artifacts
from ruos.cie_runtime_media import apply_runtime_media_delivery, build_runtime_media_delivery, bind_runtime_media_document, render_runtime_media_js
from ruos.models import BuildContext
from ruos.spec_loader import load_page_spec


def test_runtime_delivery_builds_picture_sources_and_artifact_map(tmp_path: Path):
    avif = tmp_path / "hero-768.avif"; avif.write_bytes(b"avif")
    webp = tmp_path / "hero-1200.webp"; webp.write_bytes(b"webp")
    report = {
        "assets": [{
            "asset_id": "hero-image",
            "media_type": "image",
            "status": "produced",
            "variants": [
                {"format": "avif", "width": 768, "uri": str(avif), "status": "produced"},
                {"format": "webp", "width": 1200, "uri": str(webp), "status": "produced"},
            ],
        }]
    }
    registry = {"entries": [{"asset_id": "hero-image", "media_type": "image", "semantics": {"alt": "نمای سازه", "decorative": False}}]}
    plan = {"sections": [{"section_id": "hero", "assets": [{"asset_id": "hero-image"}]}]}
    delivery, artifacts = build_runtime_media_delivery(report, registry, plan, tmp_path)
    assert delivery["status"] == "ready"
    assert delivery["bindings"][0]["section_id"] == "hero"
    assert "assets/media/hero-image/hero-768.avif" in artifacts
    document = '<main><section id="hero"><h1>Hero</h1></section></main>'
    bound = bind_runtime_media_document(document, delivery)
    assert "data-cie-responsive-picture" in bound
    assert "image/avif" in bound
    assert "1200w" in bound
    assert 'alt="نمای سازه"' in bound


def test_runtime_model_selects_lod_by_capability_and_network(tmp_path: Path):
    medium = tmp_path / "structure-medium.glb"; medium.write_bytes(b"medium")
    high = tmp_path / "structure-high.glb"; high.write_bytes(b"high")
    poster = tmp_path / "poster.webp"; poster.write_bytes(b"poster")
    report = {"assets": [{"asset_id": "structure-model", "section_id": "approved-technical", "media_type": "model-3d", "status": "produced", "variants": [
        {"format": "glb", "lod": "medium", "uri": str(medium), "status": "produced"},
        {"format": "glb", "lod": "high", "uri": str(high), "status": "produced"},
    ]}]}
    registry = {"entries": [{"asset_id": "structure-model", "media_type": "model-3d", "poster_uri": str(poster), "semantics": {"alt": "مدل سازه"}}]}
    plan = {"sections": [{"section_id": "knowledge", "assets": [{"asset_id": "structure-model"}]}]}
    delivery, artifacts = build_runtime_media_delivery(report, registry, plan, tmp_path)
    assert delivery["status"] == "ready"
    assert delivery["bindings"][0]["section_id"] == "approved-technical"
    assert "assets/media/approved-technical/structure-model/poster.webp" in artifacts
    bound = bind_runtime_media_document('<section id="knowledge"><h2>سازه</h2></section>', delivery)
    assert "data-cie-responsive-model" in bound
    assert "data-cie-model-medium" in bound
    runtime = render_runtime_media_js(delivery)
    assert "saveData" in runtime
    assert "effectiveType" in runtime
    assert "cieSelectedLod" in runtime


def test_runtime_manifest_hashes_post_lod_gate_evidence_and_approved_models(tmp_path: Path):
    page = load_page_spec(Path("pages/structures.json"))
    result = compile_page_with_cie(page, BuildContext(project_root=Path.cwd(), output_root=tmp_path / "dist", strict=False))
    medium = tmp_path / "approved/medium.glb"; high = tmp_path / "approved/high.glb"; poster = tmp_path / "approved/poster.webp"; evidence = tmp_path / "approved/compare.png"
    medium.parent.mkdir(parents=True); medium.write_bytes(b"medium"); high.write_bytes(b"high"); poster.write_bytes(b"poster"); evidence.write_bytes(b"comparison")
    gate = {"version": "1.0", "status": "pass", "reports": [{"status": "pass", "section_id": "knowledge", "geometry": {"medium": {"path": str(medium)}, "high": {"path": str(high)}}, "visual_qa": {"status": "approved", "reviewer": "qa", "evidence": str(evidence)}, "failures": []}], "failures": []}
    _, _, summary = materialize_post_lod_artifacts(gate, tmp_path, result.output_dir)
    report = {"assets": [{"asset_id": "structure-model", "section_id": "knowledge", "media_type": "model-3d", "status": "produced", "variants": [
        {"format": "glb", "lod": "medium", "uri": str(medium), "status": "produced"},
        {"format": "glb", "lod": "high", "uri": str(high), "status": "produced"},
    ]}]}
    registry = {"entries": [{"asset_id": "structure-model", "section_id": "knowledge", "media_type": "model-3d", "poster_uri": str(poster), "semantics": {"alt": "مدل سازه"}}]}
    delivery, artifacts = build_runtime_media_delivery(report, registry, {"sections": []}, tmp_path)
    implementation = json.loads((result.output_dir / "assets/cie-implementation-contract.json").read_text(encoding="utf-8"))
    apply_runtime_media_delivery(result.output_dir, page, delivery, artifacts, implementation, strict=False, post_lod_gate=summary)
    manifest = json.loads((result.output_dir / "build-manifest.json").read_text(encoding="utf-8"))
    assert manifest["cie_post_lod_qa"]["status"] == "pass"
    assert "assets/3d-qa/post-lod-gate.json" in manifest["sha256"]
    assert any(path.endswith("compare.png") for path in manifest["sha256"])
    assert any(path.endswith("medium.glb") for path in manifest["sha256"])

import json
from pathlib import Path

from ruos.cie_build import compile_page_with_cie
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
    assert "assets/media/hero/hero-image/hero-768.avif" in artifacts
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
    report = {"assets": [{"asset_id": "structure-model", "media_type": "model-3d", "status": "produced", "variants": [
        {"format": "glb", "lod": "medium", "uri": str(medium), "status": "produced"},
        {"format": "glb", "lod": "high", "uri": str(high), "status": "produced"},
    ]}]}
    registry = {"entries": [{"asset_id": "structure-model", "media_type": "model-3d", "poster_uri": str(poster), "semantics": {"alt": "مدل سازه"}}]}
    plan = {"sections": [{"section_id": "knowledge", "assets": [{"asset_id": "structure-model"}]}]}
    delivery, artifacts = build_runtime_media_delivery(report, registry, plan, tmp_path)
    assert delivery["status"] == "ready"
    assert "assets/media/knowledge/structure-model/poster.webp" in artifacts
    bound = bind_runtime_media_document('<section id="knowledge"><h2>سازه</h2></section>', delivery)
    assert "data-cie-responsive-model" in bound
    assert "data-cie-model-medium" in bound
    runtime = render_runtime_media_js(delivery)
    assert "saveData" in runtime
    assert "effectiveType" in runtime
    assert "cieSelectedLod" in runtime


def test_runtime_delivery_keeps_duplicate_asset_ids_scoped_by_section(tmp_path: Path):
    hero = tmp_path / "hero.webp"; hero.write_bytes(b"hero")
    technical = tmp_path / "technical.webp"; technical.write_bytes(b"technical")
    report = {"assets": [
        {"asset_id": "content", "section_id": "hero", "media_type": "image", "status": "produced", "variants": [{"format": "webp", "width": 480, "uri": str(hero), "status": "produced"}]},
        {"asset_id": "content", "section_id": "technical", "media_type": "image", "status": "produced", "variants": [{"format": "webp", "width": 480, "uri": str(technical), "status": "produced"}]},
    ]}
    registry = {"entries": [
        {"asset_id": "content", "section_id": "hero", "media_type": "image", "semantics": {"alt": "hero"}},
        {"asset_id": "content", "section_id": "technical", "media_type": "image", "semantics": {"alt": "technical"}},
    ]}
    delivery, artifacts = build_runtime_media_delivery(report, registry, {"sections": []}, tmp_path)
    assert [item["section_id"] for item in delivery["bindings"]] == ["hero", "technical"]
    assert set(artifacts) == {
        "assets/media/hero/content/hero.webp",
        "assets/media/technical/content/technical.webp",
    }


def test_runtime_manifest_hashes_retained_post_lod_evidence(tmp_path: Path):
    page = load_page_spec(Path("pages/structures.json"))
    result = compile_page_with_cie(page, BuildContext(project_root=Path.cwd(), output_root=tmp_path / "dist", strict=False))
    evidence = result.output_dir / "assets/3d-qa/technical/01-compare.png"
    evidence.parent.mkdir(parents=True); evidence.write_bytes(b"comparison")
    implementation = json.loads((result.output_dir / "assets/cie-implementation-contract.json").read_text(encoding="utf-8"))
    delivery = {"version": "1.4", "status": "ready", "selection_policy": {}, "bindings": []}
    summary = {"status": "pass", "runtime_delivery_blocking": True, "sections": ["technical"], "evidence_artifacts": ["assets/3d-qa/technical/01-compare.png"]}
    apply_runtime_media_delivery(result.output_dir, page, delivery, {}, implementation, strict=False, post_lod_gate=summary)
    manifest = json.loads((result.output_dir / "build-manifest.json").read_text(encoding="utf-8"))
    assert manifest["cie_post_lod_qa"]["status"] == "pass"
    assert "assets/3d-qa/technical/01-compare.png" in manifest["sha256"]

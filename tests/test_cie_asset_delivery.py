from pathlib import Path

from ruos.cie_asset_delivery import build_asset_production_manifest, validate_delivery_budget
from ruos.cie_build import compile_page_with_cie
from ruos.models import BuildContext
from ruos.spec_loader import load_page_spec


def test_manifest_plans_modern_image_video_and_3d_delivery(tmp_path: Path):
    registry = {
        "entries": [
            {"asset_id": "image-a", "media_type": "image", "uri": None, "preload_priority": "high"},
            {"asset_id": "video-a", "media_type": "video", "uri": None, "preload_priority": "auto"},
            {"asset_id": "model-a", "media_type": "model-3d", "uri": None, "preload_priority": "auto"},
        ]
    }
    manifest = build_asset_production_manifest(registry, tmp_path)
    assert manifest["status"] == "ready"
    assert manifest["generation_mode"] == "manifest-only"
    image = next(item for item in manifest["assets"] if item["asset_id"] == "image-a")
    assert {item["format"] for item in image["variants"]} == {"avif", "webp"}
    video = next(item for item in manifest["assets"] if item["asset_id"] == "video-a")
    assert video["mobile_strategy"] == "poster-first-lazy-video"
    model = next(item for item in manifest["assets"] if item["asset_id"] == "model-a")
    assert [item["lod"] for item in model["variants"]] == ["poster", "medium", "high"]


def test_delivery_budget_blocks_oversized_known_critical_media(tmp_path: Path):
    source = tmp_path / "hero.glb"
    source.write_bytes(b"x" * (500 * 1024))
    registry = {"entries": [{"asset_id": "hero", "media_type": "model-3d", "uri": "hero.glb", "preload_priority": "high", "checksum": "known"}]}
    manifest = build_asset_production_manifest(registry, tmp_path)
    report = validate_delivery_budget(manifest)
    assert report["status"] == "blocked"
    assert "mobile initial budget" in report["failures"][0]


def test_default_structures_build_emits_asset_production_manifest(tmp_path: Path):
    root = Path.cwd()
    page = load_page_spec(root / "pages" / "structures.json")
    result = compile_page_with_cie(page, BuildContext(project_root=root, output_root=tmp_path, strict=True))
    manifest = result.output_dir / "assets" / "asset-production-manifest.json"
    assert manifest in result.files
    assert manifest.is_file()
    assert "asset-production-manifest.json" in (result.output_dir / "creative-blueprint.json").read_text(encoding="utf-8")

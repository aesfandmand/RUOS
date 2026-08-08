from pathlib import Path

from PIL import Image

from ruos.cie_media_worker import produce_media_derivatives, validate_produced_media_budget


def test_worker_generates_real_webp_derivative_with_hash(tmp_path: Path):
    source = tmp_path / "hero.png"
    Image.new("RGB", (320, 180), (220, 20, 60)).save(source)
    registry = {"entries": [{"asset_id": "hero", "uri": source.name, "media_type": "image"}]}
    manifest = {
        "budgets": {"mobile": {"initial_media_kb": 450}, "desktop": {"deferred_media_kb": 4200}},
        "assets": [{"asset_id": "hero", "section_id": "hero", "media_type": "image", "priority": "high", "variants": [{"format": "webp", "width": 320, "descriptor": "320w"}]}],
    }
    report = produce_media_derivatives(manifest, registry, tmp_path, tmp_path / "dist-media")
    variant = report["assets"][0]["variants"][0]
    assert report["status"] == "produced"
    assert report["assets"][0]["section_id"] == "hero"
    assert variant["status"] == "produced"
    assert variant["sha256"]
    assert variant["bytes"] > 0
    assert (tmp_path / variant["uri"]).is_file()
    assert validate_produced_media_budget(report, manifest)["status"] == "pass"


def test_produced_budget_gate_uses_real_derivative_sizes():
    report = {"assets": [{"asset_id": "hero", "priority": "high", "status": "produced", "variants": [{"status": "produced", "kb": 501}]}]}
    manifest = {"budgets": {"mobile": {"initial_media_kb": 450}, "desktop": {"deferred_media_kb": 4200}}}
    gate = validate_produced_media_budget(report, manifest)
    assert gate["status"] == "blocked"
    assert any("produced critical media" in failure for failure in gate["failures"])


def test_worker_keeps_duplicate_asset_ids_scoped_by_section(tmp_path: Path):
    first = tmp_path / "first.png"; second = tmp_path / "second.png"
    Image.new("RGB", (20, 20), (255, 0, 0)).save(first)
    Image.new("RGB", (20, 20), (0, 0, 255)).save(second)
    registry = {"entries": [
        {"asset_id": "content", "section_id": "hero", "uri": first.name, "media_type": "image"},
        {"asset_id": "content", "section_id": "technical", "uri": second.name, "media_type": "image"},
    ]}
    variant = [{"format": "webp", "width": 20, "descriptor": "20w"}]
    manifest = {"assets": [
        {"asset_id": "content", "section_id": "hero", "media_type": "image", "variants": variant},
        {"asset_id": "content", "section_id": "technical", "media_type": "image", "variants": variant},
    ]}
    report = produce_media_derivatives(manifest, registry, tmp_path, tmp_path / "generated")
    uris = [item["variants"][0]["uri"] for item in report["assets"]]
    assert uris[0] != uris[1]
    assert "/hero/content/" in uris[0]
    assert "/technical/content/" in uris[1]

from pathlib import Path

from ruos.cie_build import generate_cie_blueprint
from ruos.spec_loader import load_page_spec


def test_asset_source_registry_contracts():
    page = load_page_spec(Path("pages/structures.json"))
    blueprint = generate_cie_blueprint(page)
    registry = blueprint["asset_source_registry"]
    assert registry["status"] == "ready"
    assert registry["entries"]
    assert registry["policy"]["provenance_required_before_publish"] is True
    assert registry["policy"]["license_required_before_publish"] is True
    for entry in registry["entries"]:
        assert "integrity" in entry
        assert "provenance" in entry
        assert "semantics" in entry
        assert "hotspots" in entry


def test_every_asset_uses_lightweight_source_reference():
    page = load_page_spec(Path("pages/structures.json"))
    blueprint = generate_cie_blueprint(page)
    plan = blueprint["asset_media_plan"]
    assets = [asset for section in plan["sections"] for asset in section["assets"]]
    assert assets
    assert all(asset.get("source_ref") == asset["asset_id"] for asset in assets)
    assert "source_registry" not in plan
    contract = blueprint["ui_implementation_contract"]
    assert contract["asset_source_registry_ref"]["status"] == "ready"
    assert contract["asset_source_registry_ref"]["artifact"].endswith("#asset_source_registry")

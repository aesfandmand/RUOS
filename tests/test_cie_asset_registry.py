from pathlib import Path

from ruos.cie_build import generate_cie_blueprint
from ruos.spec_loader import load_page_spec


def test_asset_source_registry_contracts():
    page = load_page_spec(Path("pages/structures.json"))
    plan = generate_cie_blueprint(page)["asset_media_plan"]
    registry = plan["source_registry"]
    assert registry["status"] == "ready"
    assert registry["entries"]
    assert registry["policy"]["provenance_required_before_publish"] is True
    assert registry["policy"]["license_required_before_publish"] is True
    for entry in registry["entries"]:
        assert "integrity" in entry
        assert "provenance" in entry
        assert "semantics" in entry
        assert "hotspots" in entry


def test_source_contract_is_bound_to_every_asset():
    page = load_page_spec(Path("pages/structures.json"))
    plan = generate_cie_blueprint(page)["asset_media_plan"]
    assets = [asset for section in plan["sections"] for asset in section["assets"]]
    assert assets
    assert all("source_contract" in asset for asset in assets)
    assert all(asset["source_contract"]["asset_id"] == asset["asset_id"] for asset in assets)

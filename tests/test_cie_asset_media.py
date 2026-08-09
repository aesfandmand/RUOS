from pathlib import Path

from ruos.cie_build import generate_cie_blueprint
from ruos.cie_native_renderer import render_runtime_from_contract
from ruos.spec_loader import load_page_spec


def test_structures_asset_media_plan_is_ready():
    page = load_page_spec(Path("pages/structures.json"))
    blueprint = generate_cie_blueprint(page)
    plan = blueprint["asset_media_plan"]
    assert plan["status"] == "ready"
    assert len(plan["sections"]) == len(page.sections)
    assets = [asset for section in plan["sections"] for asset in section["assets"]]
    assert assets
    assert any(asset["media_type"] == "model-3d" for asset in assets)
    assert all("mobile_fallback" in asset for asset in assets)
    assert all("performance_budget" in asset for asset in assets)
    assert plan["policy"]["webgl_is_progressive_enhancement"] is True


def test_asset_media_plan_reaches_contract_and_runtime():
    page = load_page_spec(Path("pages/structures.json"))
    blueprint = generate_cie_blueprint(page)
    contract = blueprint["ui_implementation_contract"]
    assert contract["asset_media_plan"]["status"] == "ready"
    assert contract["global_contract"]["asset_media_progressive_enhancement_required"] is True
    runtime = render_runtime_from_contract(contract)
    assert "RUOS_CIE_ASSET_MEDIA" in runtime
    assert "cieWebGLCapable" in runtime
    assert "data-cie-media" in runtime.lower()

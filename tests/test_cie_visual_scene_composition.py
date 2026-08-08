from pathlib import Path

from ruos.cie_build import generate_cie_blueprint
from ruos.cie_native_renderer import render_css_from_contract, render_runtime_from_contract
from ruos.spec_loader import load_page_spec
from ruos.visual_dna import resolve_visual_dna


def test_structures_visual_scene_composition_is_ready_and_complete():
    page = load_page_spec(Path("pages/structures.json"))
    blueprint = generate_cie_blueprint(page)
    composition = blueprint["visual_scene_composition"]
    assert composition["status"] == "ready"
    assert len(composition["sections"]) == len(page.sections)
    by_id = {item["section_id"]: item for item in composition["sections"]}
    hero = by_id["hero"]
    assert hero["pattern"] == "cinematic-scroll-stage"
    assert len(hero["scenes"]) == 4
    assert any(layer["id"] == "hero-depth" for scene in hero["scenes"] for layer in scene["layers"])
    assert hero["scenes"][1]["camera"]["z"] > 1


def test_visual_scene_composition_reaches_contract_and_native_runtime():
    page = load_page_spec(Path("pages/structures.json"))
    blueprint = generate_cie_blueprint(page)
    contract = blueprint["ui_implementation_contract"]
    assert contract["version"] == "1.2"
    assert all(item["visual_scene_composition"]["scenes"] for item in contract["sections"])
    runtime = render_runtime_from_contract(contract)
    css = render_css_from_contract(resolve_visual_dna(page.visual_profile), contract)
    assert "RUOS_CIE_VISUAL_SCENES" in runtime
    assert "data-cie-visual-layer" in runtime
    assert "data-cie-camera" in css
    assert "prefers-reduced-motion" in css

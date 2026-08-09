from pathlib import Path

from ruos.cie_3d_authoring_manifest import build_3d_authoring_manifest
from ruos.cie_build import generate_cie_blueprint
from ruos.spec_loader import load_page_spec


def test_structures_generate_actionable_3d_authoring_manifest():
    page = load_page_spec(Path("pages/structures.json"))
    blueprint = generate_cie_blueprint(page)
    manifest = build_3d_authoring_manifest(blueprint["scene_orchestration"], blueprint["asset_media_plan"])
    assert manifest["status"] == "ready"
    assert manifest["sections"]
    assert manifest["naming_convention"]["semantic_group"] == "cie-group-{state}"
    assert manifest["naming_convention"]["hotspot_anchor"] == "cie-hotspot-{semantic-id}"
    for section in manifest["sections"]:
        assert section["required_material_variants"]
        assert section["required_animation_names"]
        assert section["lod_contract"]["poster"]["required"] is True
        assert section["lod_contract"]["medium"]["required"] is True
        assert section["lod_contract"]["high"]["required"] is True
        assert section["qc"]["must_validate_before_publish"] is True


def test_manifest_matches_semantic_glb_validator_naming():
    page = load_page_spec(Path("pages/structures.json"))
    blueprint = generate_cie_blueprint(page)
    manifest = build_3d_authoring_manifest(blueprint["scene_orchestration"], blueprint["asset_media_plan"])
    for section in manifest["sections"]:
        for state in section["states"]:
            expected_animation = "cie-overview" if state == "overview" else f"cie-explode-{state}"
            assert expected_animation in section["required_animation_names"]
        for node in section["required_node_names"]:
            assert node.startswith("cie-group-")

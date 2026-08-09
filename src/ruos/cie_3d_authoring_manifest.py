from __future__ import annotations

from typing import Any, Mapping


def build_3d_authoring_manifest(scene_orchestration: Mapping[str, Any], asset_media_plan: Mapping[str, Any]) -> dict[str, Any]:
    model_sections = {
        str(section.get("section_id", ""))
        for section in asset_media_plan.get("sections", [])
        if isinstance(section, Mapping)
        and any(isinstance(asset, Mapping) and asset.get("media_type") == "model-3d" for asset in section.get("assets", []))
    }
    manifests: list[dict[str, Any]] = []
    for section in scene_orchestration.get("sections", []) if isinstance(scene_orchestration, Mapping) else []:
        if not isinstance(section, Mapping):
            continue
        section_id = str(section.get("section_id", ""))
        if section_id not in model_sections:
            continue
        states: list[str] = []
        for scene in section.get("scenes", []) if isinstance(section.get("scenes"), list) else []:
            if not isinstance(scene, Mapping):
                continue
            state = str(scene.get("state", scene.get("id", "overview")))
            if state and state not in states:
                states.append(state)
        focus_states = [state for state in states if state != "overview"]
        manifests.append({
            "section_id": section_id,
            "states": states,
            "required_node_names": [f"cie-group-{state}" for state in focus_states],
            "required_material_variants": states,
            "required_animation_names": ["cie-overview" if state == "overview" else f"cie-explode-{state}" for state in states],
            "hotspot_anchor_pattern": "cie-hotspot-{semantic-id}",
            "semantic_group_pattern": "cie-group-{state}",
            "lod_contract": {
                "poster": {"required": True, "purpose": "non-WebGL and reduced-motion fallback"},
                "medium": {"required": True, "purpose": "mobile/tablet and constrained network"},
                "high": {"required": True, "purpose": "desktop/high-capability WebGL"},
            },
            "export_contract": {
                "container": "GLB 2.0",
                "material_variants_extension": "KHR_materials_variants",
                "preserve_node_names": True,
                "preserve_animation_names": True,
                "bake_transform_animation": True,
                "draco_or_meshopt_allowed": True,
            },
            "qc": {
                "must_validate_before_publish": True,
                "validator": "cie_glb_validation.validate_glb_authoring",
                "fail_publish_on_missing_authored_capability": True,
            },
        })
    return {
        "version": "1.0",
        "status": "ready" if manifests else "not-applicable",
        "naming_convention": {
            "semantic_group": "cie-group-{state}",
            "hotspot_anchor": "cie-hotspot-{semantic-id}",
            "animation": "cie-explode-{state}",
            "overview_animation": "cie-overview",
            "material_variant": "{state}",
        },
        "sections": manifests,
    }

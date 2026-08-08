from __future__ import annotations

import json
from typing import Any, Mapping


def _state_contract(state: str) -> dict[str, Any]:
    normalized = state or "overview"
    presets: dict[str, dict[str, Any]] = {
        "overview": {"variant": "overview", "animation": "cie-overview", "mode": "assembled", "focus": []},
        "structure": {"variant": "structure", "animation": "cie-explode-structure", "mode": "isolate-highlight", "focus": ["structure"]},
        "foundation": {"variant": "foundation", "animation": "cie-explode-foundation", "mode": "isolate-highlight", "focus": ["foundation"]},
        "lighting": {"variant": "lighting", "animation": "cie-explode-lighting", "mode": "isolate-highlight", "focus": ["lighting"]},
        "placement": {"variant": "placement", "animation": "cie-explode-placement", "mode": "context-highlight", "focus": ["placement"]},
    }
    contract = dict(presets.get(normalized, {"variant": normalized, "animation": f"cie-{normalized}", "mode": "state-highlight", "focus": [normalized]}))
    contract["state"] = normalized
    contract["fallback"] = "camera-and-hotspot-only"
    return contract


def build_mesh_state_plan(scene_orchestration: Mapping[str, Any], runtime_delivery: Mapping[str, Any]) -> dict[str, Any]:
    model_sections = {
        str(item.get("section_id", ""))
        for item in runtime_delivery.get("bindings", [])
        if isinstance(item, Mapping) and item.get("media_type") == "model-3d" and item.get("status") in {"ready", "fallback-only"}
    }
    sections: list[dict[str, Any]] = []
    for section in scene_orchestration.get("sections", []) if isinstance(scene_orchestration, Mapping) else []:
        if not isinstance(section, Mapping):
            continue
        section_id = str(section.get("section_id", ""))
        if section_id not in model_sections:
            continue
        states: list[dict[str, Any]] = []
        seen: set[str] = set()
        for scene in section.get("scenes", []) if isinstance(section.get("scenes"), list) else []:
            if not isinstance(scene, Mapping):
                continue
            state = str(scene.get("state", scene.get("id", "overview")))
            if state in seen:
                continue
            seen.add(state)
            states.append(_state_contract(state))
        sections.append({
            "section_id": section_id,
            "driver": "scene-state-and-hotspot",
            "states": states,
            "model_authoring_contract": {
                "preferred_variant_names": [item["variant"] for item in states],
                "preferred_animation_names": [item["animation"] for item in states],
                "variant_or_animation_is_optional": True,
                "semantic_mesh_metadata_required_for_custom_adapter": True,
            },
            "mobile_policy": "state-snap-without-required-explode-animation",
            "reduced_motion_policy": "prefer-variant-or-static-state;do-not-autoplay-explode-animation",
        })
    return {
        "version": "1.0",
        "status": "ready" if sections else "not-applicable",
        "sections": sections,
        "policy": {
            "never_hide_semantic_content_with_3d_state": True,
            "exploded_view_requires_authored_glb_variant_or_animation": True,
            "fallback_is_camera_and_hotspot_only": True,
            "user_model_interaction_preserved": True,
        },
    }


def render_mesh_state_runtime(plan: Mapping[str, Any]) -> str:
    if plan.get("status") != "ready":
        return ""
    payload = json.dumps(plan, ensure_ascii=False, separators=(",", ":"))
    return f'''const RUOS_CIE_MESH_STATE={payload};
const cieMeshReduce=matchMedia('(prefers-reduced-motion: reduce)').matches;
function cieAvailableVariants(viewer){{return Array.isArray(viewer.availableVariants)?viewer.availableVariants:[];}}
function cieAvailableAnimations(viewer){{return Array.isArray(viewer.availableAnimations)?viewer.availableAnimations:[];}}
function cieApplyMeshState(viewer,contract){{if(!viewer||!contract)return;viewer.dataset.cieMeshState=contract.state||'';viewer.dataset.cieMeshMode=contract.mode||'';let applied='fallback';const variants=cieAvailableVariants(viewer);if(contract.variant&&variants.includes(contract.variant)){{viewer.variantName=contract.variant;applied='variant';}}const animations=cieAvailableAnimations(viewer);if(!cieMeshReduce&&contract.animation&&animations.includes(contract.animation)){{viewer.animationName=contract.animation;viewer.play({{repetitions:1}});applied=applied==='variant'?'variant+animation':'animation';}}viewer.dataset.cieMeshApplied=applied;viewer.dispatchEvent(new CustomEvent('cie:model-state',{{bubbles:true,detail:{{state:contract.state,mode:contract.mode,applied}}}}));}}
for(const meshSection of RUOS_CIE_MESH_STATE.sections){{const section=document.getElementById(meshSection.section_id);if(!section)continue;const viewer=section.querySelector('[data-cie-model-viewer]');if(!viewer)continue;const states=meshSection.states||[];const apply=()=>{{const state=section.dataset.cieState||states[0]?.state||'';const contract=states.find(item=>item.state===state)||states[0];if(contract)cieApplyMeshState(viewer,contract);}};viewer.addEventListener('load',apply);section.addEventListener('cie:hotspot-change',apply);new MutationObserver(apply).observe(section,{{attributes:true,attributeFilter:['data-cie-state']}});apply();}}
'''

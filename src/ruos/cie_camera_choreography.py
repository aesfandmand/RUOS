from __future__ import annotations

import json
from typing import Any, Mapping


def _pose_for(state: str, index: int, total: int) -> dict[str, Any]:
    presets = {
        "context": {"orbit": "30deg 70deg 125%", "target": "0m 0m 0m", "fov": "35deg"},
        "depth": {"orbit": "55deg 68deg 112%", "target": "0m .15m 0m", "fov": "32deg"},
        "focus": {"orbit": "78deg 64deg 96%", "target": "0m .3m 0m", "fov": "28deg"},
        "handoff": {"orbit": "105deg 66deg 108%", "target": "0m .1m 0m", "fov": "32deg"},
        "overview": {"orbit": "35deg 68deg 125%", "target": "0m 0m 0m", "fov": "36deg"},
        "structure": {"orbit": "60deg 63deg 98%", "target": "0m .35m 0m", "fov": "29deg"},
        "foundation": {"orbit": "18deg 78deg 92%", "target": "0m -.35m 0m", "fov": "27deg"},
        "placement": {"orbit": "120deg 72deg 118%", "target": "0m 0m 0m", "fov": "34deg"},
    }
    if state in presets:
        return presets[state]
    ratio = 0 if total <= 1 else index / (total - 1)
    return {"orbit": f"{round(25 + 70 * ratio)}deg 70deg {round(122 - 18 * ratio)}%", "target": "0m 0m 0m", "fov": "34deg"}


def build_camera_choreography_plan(scene_orchestration: Mapping[str, Any], runtime_delivery: Mapping[str, Any]) -> dict[str, Any]:
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
        scenes = [item for item in section.get("scenes", []) if isinstance(item, Mapping)]
        keyframes = []
        for index, scene in enumerate(scenes):
            state = str(scene.get("state", scene.get("id", "")))
            keyframes.append({
                "scene_id": str(scene.get("id", state)),
                "state": state,
                "range": list(scene.get("range", [0.0, 1.0])),
                "camera": _pose_for(state, index, len(scenes)),
                "focus_hotspot": state if state in {"structure", "foundation", "placement", "lighting"} else None,
            })
        sections.append({
            "section_id": section_id,
            "driver": "scroll-progress-and-state",
            "interpolation": "model-viewer-camera-orbit",
            "keyframes": keyframes,
            "mobile_policy": "step-keyframes-no-continuous-camera-under-900px",
            "reduced_motion_policy": "snap-to-scene-keyframe",
        })
    return {
        "version": "1.0",
        "status": "ready" if sections else "not-applicable",
        "sections": sections,
        "policy": {"user_camera_controls_preserved": True, "scroll_camera_pauses_after_user_interaction": True, "semantic_state_drives_hotspot_focus": True},
    }


def render_camera_choreography_runtime(plan: Mapping[str, Any]) -> str:
    if plan.get("status") != "ready":
        return ""
    payload = json.dumps(plan, ensure_ascii=False, separators=(",", ":"))
    return f'''const RUOS_CIE_CAMERA={payload};
const cieCameraReduce=matchMedia('(prefers-reduced-motion: reduce)').matches;
function cieCameraApply(viewer,keyframe){{if(!viewer||!keyframe)return;const camera=keyframe.camera||{{}};if(camera.orbit)viewer.cameraOrbit=camera.orbit;if(camera.target)viewer.cameraTarget=camera.target;if(camera.fov)viewer.fieldOfView=camera.fov;viewer.dataset.cieCameraScene=keyframe.scene_id||'';}}
for(const cameraSection of RUOS_CIE_CAMERA.sections){{const section=document.getElementById(cameraSection.section_id);if(!section)continue;const viewer=section.querySelector('[data-cie-model-viewer]');if(!viewer)continue;let userCamera=false;viewer.addEventListener('camera-change',event=>{{if(event.detail&&event.detail.source==='user-interaction')userCamera=true;}});const frames=cameraSection.keyframes||[];const update=()=>{{if(!frames.length||userCamera)return;const rect=section.getBoundingClientRect();const total=Math.max(1,rect.height+innerHeight);const progress=Math.max(0,Math.min(1,(innerHeight-rect.top)/total));let frame=frames.find(item=>progress>=Number(item.range?.[0]||0)&&progress<=Number(item.range?.[1]||1))||frames[frames.length-1];if(cieCameraReduce||innerWidth<900){{const state=section.dataset.cieState||'';frame=frames.find(item=>item.state===state)||frame;}}cieCameraApply(viewer,frame);}};update();addEventListener('scroll',update,{{passive:true}});section.addEventListener('cie:hotspot-change',event=>{{const state=event.detail?.state||'';const frame=frames.find(item=>item.state===state);if(frame){{userCamera=false;cieCameraApply(viewer,frame);}}}});new MutationObserver(()=>{{if(cieCameraReduce||innerWidth<900)update();}}).observe(section,{{attributes:true,attributeFilter:['data-cie-state']}});}}
'''

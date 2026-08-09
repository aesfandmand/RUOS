from __future__ import annotations

from typing import Any, Mapping

from .models import PageSpec


def _layer_profile(pattern: str, scene_id: str) -> list[dict[str, Any]]:
    base = [
        {"id": "content", "role": "semantic-content", "depth": 0, "opacity": 1.0, "scale": 1.0, "translate_y": 0, "priority": "primary"},
        {"id": "ambient", "role": "ambient-visual", "depth": -1, "opacity": 0.45, "scale": 1.02, "translate_y": 0, "priority": "decorative"},
    ]
    if pattern == "cinematic-scroll-stage":
        if scene_id == "establish":
            return base + [{"id": "hero-depth", "role": "depth-layer", "depth": 2, "opacity": 0.45, "scale": 1.06, "translate_y": 20, "priority": "support"}]
        if scene_id == "depth":
            return base + [{"id": "hero-depth", "role": "depth-layer", "depth": 2, "opacity": 0.8, "scale": 1.02, "translate_y": 4, "priority": "support"}]
        if scene_id == "focus":
            return base + [{"id": "hero-depth", "role": "depth-layer", "depth": 1, "opacity": 0.35, "scale": 0.99, "translate_y": -8, "priority": "support"}, {"id": "evidence", "role": "evidence-focus", "depth": 3, "opacity": 1.0, "scale": 1.0, "translate_y": 0, "priority": "primary"}]
        return base + [{"id": "cta", "role": "conversion-action", "depth": 3, "opacity": 1.0, "scale": 1.0, "translate_y": 0, "priority": "primary"}]
    if pattern == "structure-anatomy-explorer":
        state = "placement" if scene_id == "context" else scene_id
        return base + [
            {"id": "anatomy-base", "role": "technical-model", "depth": 1, "opacity": 0.35 if state != "overview" else 1.0, "scale": 1.0, "translate_y": 0, "priority": "support"},
            {"id": state, "role": "active-anatomy-layer", "depth": 3, "opacity": 1.0, "scale": 1.04, "translate_y": 0, "priority": "primary"},
        ]
    if pattern == "hotspot-decision-explorer":
        return base + [{"id": "decision-surface", "role": "interactive-surface", "depth": 2, "opacity": 1.0, "scale": 1.0 if scene_id != "resolve" else 0.98, "translate_y": 0, "priority": "primary"}, {"id": "recommendation", "role": "decision-result", "depth": 3, "opacity": 1.0 if scene_id == "resolve" else 0.0, "scale": 1.0, "translate_y": 0, "priority": "primary"}]
    return base


def _camera(pattern: str, scene_id: str) -> dict[str, Any]:
    if pattern == "cinematic-scroll-stage":
        presets = {
            "establish": {"x": 0, "y": 0, "z": 1.0, "rotate": 0, "focal": 1.0},
            "depth": {"x": 0, "y": -0.04, "z": 1.08, "rotate": 1.5, "focal": 1.06},
            "focus": {"x": 0.03, "y": -0.02, "z": 1.12, "rotate": 0.5, "focal": 1.12},
            "handoff": {"x": 0, "y": 0.03, "z": 1.02, "rotate": 0, "focal": 1.0},
        }
        return presets.get(scene_id, presets["establish"])
    return {"x": 0, "y": 0, "z": 1.0, "rotate": 0, "focal": 1.0}


def build_visual_scene_composition(page: PageSpec, scene_orchestration: Mapping[str, Any]) -> dict[str, Any]:
    raw = scene_orchestration.get("sections", []) if isinstance(scene_orchestration, Mapping) else []
    if scene_orchestration.get("status") != "ready" or not isinstance(raw, list):
        return {"version": "1.0", "status": "blocked", "page_id": page.slug, "sections": [], "blockers": ["scene orchestration is not ready"]}
    sections: list[dict[str, Any]] = []
    blockers: list[str] = []
    for section in raw:
        if not isinstance(section, Mapping):
            blockers.append("visual scene composition requires object section entries"); continue
        section_id = str(section.get("section_id", "")).strip(); pattern = str(section.get("pattern", "")).strip(); scenes = section.get("scenes", [])
        if not section_id or not pattern or not isinstance(scenes, list):
            blockers.append("visual scene composition requires section_id, pattern and scenes"); continue
        composed = []
        for scene in scenes:
            if not isinstance(scene, Mapping): continue
            scene_id = str(scene.get("id", "")).strip()
            composed.append({
                "scene_id": scene_id,
                "state": str(scene.get("state", scene_id)),
                "range": list(scene.get("range", [0, 1])),
                "camera": _camera(pattern, scene_id),
                "layers": _layer_profile(pattern, scene_id),
                "transition": {"duration_ms": 420, "easing": "cubic-bezier(.22,.61,.36,1)", "crossfade": True},
                "mobile": {"camera_enabled": False, "layer_order_preserved": True, "continuous_depth": False},
                "reduced_motion": {"continuous_transform": False, "state_visibility_only": True},
            })
        if not composed:
            blockers.append(f"{section_id} has no composed scenes")
        sections.append({"section_id": section_id, "pattern": pattern, "scenes": composed, "asset_policy": "progressive-enhancement-with-semantic-fallback", "semantic_parity_required": True})
    if len(sections) != len(page.sections): blockers.append("visual scene composition requires exactly one composition per page section")
    return {"version": "1.0", "status": "ready" if sections and not blockers else "blocked", "page_id": page.slug, "sections": sections, "blockers": blockers}

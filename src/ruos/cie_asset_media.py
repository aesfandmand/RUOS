from __future__ import annotations

from typing import Any, Mapping

from .cie_asset_registry import bind_asset_sources, build_asset_source_registry
from .models import PageSpec


def _asset_type(role: str) -> str:
    role = role.lower()
    if any(token in role for token in ("model", "anatomy", "structure", "depth")):
        return "model-3d"
    if any(token in role for token in ("ambient", "video", "cinematic")):
        return "video"
    if any(token in role for token in ("diagram", "technical", "foundation", "lighting")):
        return "svg"
    return "image"


def build_asset_media_plan(page: PageSpec, visual_scene_composition: Mapping[str, Any]) -> dict[str, Any]:
    sections = visual_scene_composition.get("sections", []) if isinstance(visual_scene_composition, Mapping) else []
    planned_sections: list[dict[str, Any]] = []
    for section in sections if isinstance(sections, list) else []:
        if not isinstance(section, Mapping):
            continue
        assets: dict[str, dict[str, Any]] = {}
        for scene in section.get("scenes", []) if isinstance(section.get("scenes"), list) else []:
            if not isinstance(scene, Mapping):
                continue
            for layer in scene.get("layers", []) if isinstance(scene.get("layers"), list) else []:
                if not isinstance(layer, Mapping):
                    continue
                asset_id = str(layer.get("id", "")).strip()
                if not asset_id or asset_id in assets:
                    continue
                role = str(layer.get("role", asset_id))
                media_type = _asset_type(role)
                assets[asset_id] = {
                    "asset_id": asset_id,
                    "role": role,
                    "media_type": media_type,
                    "source": None,
                    "required": str(layer.get("priority", "supporting")) != "decorative",
                    "loading": "eager" if section.get("section_id") == "hero" else "lazy",
                    "preload": section.get("section_id") == "hero" and media_type in {"image", "model-3d"},
                    "lod": ["poster", "medium", "high"] if media_type == "model-3d" else ["mobile", "desktop"],
                    "mobile_fallback": "poster-image" if media_type in {"model-3d", "video"} else "responsive-source",
                    "reduced_motion_fallback": "poster-image" if media_type in {"model-3d", "video"} else "static",
                    "webgl": {"eligible": media_type == "model-3d", "progressive_enhancement": True, "fallback_required": media_type == "model-3d"},
                    "performance_budget": {"max_initial_kb": 350 if media_type == "model-3d" else 220, "max_deferred_kb": 1800 if media_type == "model-3d" else 900},
                }
        planned_sections.append({"section_id": str(section.get("section_id", "")), "assets": list(assets.values())})
    plan = {
        "version": "1.1",
        "status": "ready" if len(planned_sections) == len(sections) else "blocked",
        "policy": {
            "webgl_is_progressive_enhancement": True,
            "semantic_content_must_not_depend_on_media": True,
            "mobile_poster_fallback_required": True,
            "reduced_motion_fallback_required": True,
            "asset_sources_may_remain_unresolved_until_content_production": True,
        },
        "sections": planned_sections,
        "page_slug": page.slug,
    }
    registry = build_asset_source_registry(plan)
    return bind_asset_sources(plan, registry)

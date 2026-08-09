from __future__ import annotations

from typing import Any, Mapping


def _default_source_contract(asset: Mapping[str, Any]) -> dict[str, Any]:
    media_type = str(asset.get("media_type", "image"))
    asset_id = str(asset.get("asset_id", ""))
    return {
        "asset_id": asset_id,
        "media_type": media_type,
        "uri": None,
        "poster_uri": None,
        "responsive_sources": [],
        "mime_type": None,
        "checksum": None,
        "integrity": {"algorithm": "sha256", "value": None},
        "provenance": {"provider": None, "source_url": None, "license": None, "credit": None},
        "semantics": {"alt": None, "caption": None, "decorative": not bool(asset.get("required", True))},
        "hotspots": [],
        "preload_priority": "high" if asset.get("preload") else "auto",
        "status": "unresolved",
    }


def build_asset_source_registry(asset_media_plan: Mapping[str, Any]) -> dict[str, Any]:
    entries: list[dict[str, Any]] = []
    sections = asset_media_plan.get("sections", []) if isinstance(asset_media_plan, Mapping) else []
    for section in sections if isinstance(sections, list) else []:
        if not isinstance(section, Mapping):
            continue
        section_id = str(section.get("section_id", ""))
        for asset in section.get("assets", []) if isinstance(section.get("assets"), list) else []:
            if not isinstance(asset, Mapping):
                continue
            entry = _default_source_contract(asset)
            entry["section_id"] = section_id
            entries.append(entry)
    return {
        "version": "1.0",
        "status": "ready" if entries else "blocked",
        "policy": {
            "content_addressable_integrity_supported": True,
            "provenance_required_before_publish": True,
            "license_required_before_publish": True,
            "semantic_alt_required_for_non_decorative_images": True,
            "model_and_video_poster_required_before_publish": True,
            "hotspots_are_semantic_annotations": True,
            "unresolved_sources_allowed_before_content_production": True,
        },
        "entries": entries,
    }


def bind_asset_sources(asset_media_plan: Mapping[str, Any], registry: Mapping[str, Any]) -> dict[str, Any]:
    known = {str(entry.get("asset_id")) for entry in registry.get("entries", []) if isinstance(entry, Mapping) and entry.get("asset_id")}
    sections: list[dict[str, Any]] = []
    for section in asset_media_plan.get("sections", []) if isinstance(asset_media_plan, Mapping) else []:
        if not isinstance(section, Mapping):
            continue
        bound_assets: list[dict[str, Any]] = []
        for asset in section.get("assets", []) if isinstance(section.get("assets"), list) else []:
            if not isinstance(asset, Mapping):
                continue
            bound = dict(asset)
            asset_id = str(asset.get("asset_id", ""))
            bound["source_ref"] = asset_id if asset_id in known else None
            bound_assets.append(bound)
        sections.append({"section_id": str(section.get("section_id", "")), "assets": bound_assets})
    result = dict(asset_media_plan)
    result["sections"] = sections
    result["source_registry_status"] = registry.get("status", "blocked")
    return result

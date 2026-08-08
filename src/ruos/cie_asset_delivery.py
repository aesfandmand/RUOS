from __future__ import annotations

from pathlib import Path
from typing import Any, Mapping

IMAGE_WIDTHS = (480, 768, 1200, 1600)
IMAGE_FORMATS = ("avif", "webp")


def _source_size_kb(project_root: Path, uri: object) -> int | None:
    if not uri:
        return None
    candidate = Path(str(uri))
    path = candidate if candidate.is_absolute() else project_root / candidate
    if not path.is_file():
        return None
    return max(1, (path.stat().st_size + 1023) // 1024)


def build_asset_production_manifest(registry: Mapping[str, Any], project_root: Path) -> dict[str, Any]:
    assets: list[dict[str, Any]] = []
    for raw in registry.get("entries", []) if isinstance(registry, Mapping) else []:
        if not isinstance(raw, Mapping):
            continue
        media_type = str(raw.get("media_type", "image"))
        asset_id = str(raw.get("asset_id", ""))
        source_kb = _source_size_kb(project_root, raw.get("uri"))
        delivery: dict[str, Any] = {
            "asset_id": asset_id,
            "media_type": media_type,
            "source_kb": source_kb,
            "priority": "high" if raw.get("preload_priority") == "high" else "auto",
            "cache_policy": "immutable-content-addressed" if raw.get("checksum") else "revalidate",
        }
        if media_type in {"image", "svg"}:
            delivery["variants"] = [
                {"format": fmt, "width": width, "descriptor": f"{width}w"}
                for fmt in IMAGE_FORMATS for width in IMAGE_WIDTHS
            ] if media_type == "image" else [{"format": "svg", "mode": "original-vector"}]
            delivery["mobile_strategy"] = "responsive-picture"
            delivery["desktop_strategy"] = "responsive-picture"
        elif media_type == "video":
            delivery["variants"] = [
                {"format": "webm", "profile": "mobile", "max_width": 720},
                {"format": "mp4", "profile": "desktop", "max_width": 1440},
            ]
            delivery["mobile_strategy"] = "poster-first-lazy-video"
            delivery["desktop_strategy"] = "poster-first-lazy-video"
        elif media_type == "model-3d":
            delivery["variants"] = [
                {"format": "glb", "lod": "poster"},
                {"format": "glb", "lod": "medium"},
                {"format": "glb", "lod": "high"},
            ]
            delivery["mobile_strategy"] = "poster-or-medium-lod-on-capability"
            delivery["desktop_strategy"] = "progressive-lod-webgl"
        else:
            delivery["variants"] = [{"format": "original"}]
            delivery["mobile_strategy"] = "lazy"
            delivery["desktop_strategy"] = "lazy"
        assets.append(delivery)

    budgets = {
        "mobile": {"initial_media_kb": 450, "deferred_media_kb": 1800},
        "desktop": {"initial_media_kb": 900, "deferred_media_kb": 4200},
        "hero": {"initial_media_kb": 600},
    }
    initial_known = sum(item["source_kb"] or 0 for item in assets if item["priority"] == "high")
    total_known = sum(item["source_kb"] or 0 for item in assets)
    return {
        "version": "1.0",
        "status": "ready" if assets else "blocked",
        "generation_mode": "manifest-only",
        "note": "Derivative encoding is planned here; actual AVIF/WebP/video/GLB transcoding is delegated to the media production worker.",
        "budgets": budgets,
        "observed": {"known_initial_source_kb": initial_known, "known_total_source_kb": total_known},
        "assets": assets,
        "delivery_policy": {
            "mobile_first": True,
            "poster_first_for_motion_media": True,
            "webgl_progressive_enhancement": True,
            "content_addressed_cache_when_integrity_known": True,
            "preload_only_critical_media": True,
        },
    }


def validate_delivery_budget(manifest: Mapping[str, Any]) -> dict[str, Any]:
    failures: list[str] = []
    observed = manifest.get("observed", {}) if isinstance(manifest.get("observed"), Mapping) else {}
    budgets = manifest.get("budgets", {}) if isinstance(manifest.get("budgets"), Mapping) else {}
    mobile = budgets.get("mobile", {}) if isinstance(budgets.get("mobile"), Mapping) else {}
    desktop = budgets.get("desktop", {}) if isinstance(budgets.get("desktop"), Mapping) else {}
    initial = int(observed.get("known_initial_source_kb", 0) or 0)
    total = int(observed.get("known_total_source_kb", 0) or 0)
    if initial > int(mobile.get("initial_media_kb", 0) or 0):
        failures.append(f"known critical media {initial}KB exceeds mobile initial budget")
    if total > int(desktop.get("deferred_media_kb", 0) or 0):
        failures.append(f"known total media {total}KB exceeds desktop deferred budget")
    return {"status": "pass" if not failures else "blocked", "failures": failures, "observed": dict(observed)}

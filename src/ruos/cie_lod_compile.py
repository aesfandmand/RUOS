from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any, Mapping

from .cie_3d_authoring_manifest import build_3d_authoring_manifest
from .cie_3d_worker import build_3d_production_jobs
from .cie_glb_validation import build_source_model_delivery
from .cie_lod_build import build_post_lod_gate, enforce_post_lod_build_gate, normalize_blender_plan
from .cie_mesh_state import build_mesh_state_plan


def load_json_mapping(project_root: Path, path: Path | None, label: str) -> dict[str, Any]:
    if path is None:
        raise ValueError(f"CIE {label} file is required")
    resolved = path if path.is_absolute() else project_root / path
    if not resolved.is_file():
        raise ValueError(f"CIE {label} file not found: {resolved}")
    payload = json.loads(resolved.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"CIE {label} must be a JSON object")
    return payload


def _asset_section_map(asset_media_plan: Mapping[str, Any]) -> dict[str, str]:
    result: dict[str, str] = {}
    for section in asset_media_plan.get("sections", []) if isinstance(asset_media_plan, Mapping) else []:
        if not isinstance(section, Mapping):
            continue
        section_id = str(section.get("section_id", ""))
        for asset in section.get("assets", []) if isinstance(section.get("assets"), list) else []:
            if isinstance(asset, Mapping) and asset.get("asset_id"):
                result[str(asset["asset_id"])] = section_id
    return result


def _hotspot_map(registry: Mapping[str, Any], asset_media_plan: Mapping[str, Any]) -> dict[str, set[str]]:
    sections = _asset_section_map(asset_media_plan)
    result: dict[str, set[str]] = {}
    for entry in registry.get("entries", []) if isinstance(registry, Mapping) else []:
        if not isinstance(entry, Mapping) or entry.get("media_type") != "model-3d":
            continue
        section_id = sections.get(str(entry.get("asset_id", "")), "")
        if not section_id:
            continue
        ids = {
            str(item.get("id") or item.get("entity"))
            for item in entry.get("hotspots", []) if isinstance(entry.get("hotspots"), list)
            if isinstance(item, Mapping) and (item.get("id") or item.get("entity"))
        }
        result.setdefault(section_id, set()).update(ids)
    return result


def build_compile_post_lod_gate(
    blueprint: Mapping[str, Any],
    project_root: Path,
    source_map: Mapping[str, Any],
    visual_approvals: Mapping[str, Any],
) -> dict[str, Any]:
    scene = blueprint.get("scene_orchestration", {})
    asset_media_plan = blueprint.get("asset_media_plan", {})
    registry = blueprint.get("asset_source_registry", {})
    authoring = build_3d_authoring_manifest(scene, asset_media_plan)
    if authoring.get("status") == "not-applicable":
        return {"version": "1.0", "status": "not-applicable", "authoring_manifest": authoring, "production_plan": {"jobs": []}, "blender_plan": {"jobs": []}, "gate": {"status": "not-applicable", "reports": [], "failures": []}}
    string_sources = {str(key): str(value) for key, value in source_map.items() if value}
    production_plan = build_3d_production_jobs(authoring, string_sources)
    blender_plan = normalize_blender_plan(production_plan)
    if blender_plan.get("status") != "ready":
        raise ValueError("CIE 3D LOD QA requires a bound source for every authored model section")
    source_delivery = build_source_model_delivery(registry, asset_media_plan)
    mesh_state_plan = build_mesh_state_plan(scene, source_delivery)
    approvals = {str(key): value for key, value in visual_approvals.items() if isinstance(value, Mapping)}
    gate = build_post_lod_gate(
        blender_plan=blender_plan,
        project_root=project_root,
        mesh_state_plan=mesh_state_plan,
        hotspot_map=_hotspot_map(registry, asset_media_plan),
        visual_approvals=approvals,
    )
    enforce_post_lod_build_gate(gate)
    return {"version": "1.0", "status": "pass", "authoring_manifest": authoring, "production_plan": production_plan, "blender_plan": blender_plan, "mesh_state_plan": mesh_state_plan, "gate": gate}


def _record(path: Path, project_root: Path) -> dict[str, Any]:
    digest = hashlib.sha256(path.read_bytes()).hexdigest()
    try:
        uri = path.relative_to(project_root).as_posix()
    except ValueError:
        uri = path.as_posix()
    size = path.stat().st_size
    return {"uri": uri, "bytes": size, "kb": max(1, (size + 1023) // 1024), "sha256": digest, "status": "produced", "format": "glb"}


def bind_validated_lods_to_media_report(
    production_report: Mapping[str, Any],
    gate_bundle: Mapping[str, Any],
    asset_media_plan: Mapping[str, Any],
    project_root: Path,
) -> dict[str, Any]:
    if gate_bundle.get("status") != "pass":
        raise ValueError("CIE validated LOD binding requires a passing post-LOD gate")
    section_by_asset = _asset_section_map(asset_media_plan)
    jobs = {
        str(job.get("section_id", "")): job
        for job in gate_bundle.get("blender_plan", {}).get("jobs", [])
        if isinstance(job, Mapping)
    }
    assets: list[dict[str, Any]] = []
    for item in production_report.get("assets", []) if isinstance(production_report, Mapping) else []:
        if not isinstance(item, Mapping):
            continue
        updated = dict(item)
        if item.get("media_type") == "model-3d":
            section_id = section_by_asset.get(str(item.get("asset_id", "")), "")
            job = jobs.get(section_id)
            if not job:
                raise ValueError(f"CIE validated LOD job missing for model section: {section_id or 'unknown'}")
            outputs = job.get("outputs", {}) if isinstance(job.get("outputs"), Mapping) else {}
            high = project_root / str(outputs.get("lod_high", ""))
            medium = project_root / str(outputs.get("lod_medium", ""))
            if not high.is_file() or not medium.is_file():
                raise ValueError(f"CIE validated LOD artifacts missing for model section: {section_id}")
            updated["variants"] = [
                {"lod": "high", **_record(high, project_root)},
                {"lod": "medium", **_record(medium, project_root)},
            ]
            updated["status"] = "produced"
            updated["source"] = "post-lod-qa-approved"
        assets.append(updated)
    observed = {
        "produced_bytes": sum(int(v.get("bytes", 0) or 0) for item in assets for v in item.get("variants", []) if isinstance(v, Mapping) and v.get("status") == "produced"),
        "produced_assets": sum(1 for item in assets if item.get("status") == "produced"),
        "partial_assets": sum(1 for item in assets if item.get("status") == "partial"),
        "blocked_assets": sum(1 for item in assets if item.get("status") == "blocked"),
    }
    result = dict(production_report)
    result["assets"] = assets
    result["observed"] = observed
    result["validated_3d_lod_binding"] = True
    return result

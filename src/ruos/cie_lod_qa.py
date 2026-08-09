from __future__ import annotations

import math
from pathlib import Path
from typing import Any, Mapping

from .cie_glb_validation import GLBValidationError, _read_glb_json, validate_glb_authoring


class LODQAGateError(ValueError):
    pass


def _position_accessors(gltf: Mapping[str, Any]) -> list[Mapping[str, Any]]:
    accessors = gltf.get("accessors", []) if isinstance(gltf.get("accessors"), list) else []
    results: list[Mapping[str, Any]] = []
    for mesh in gltf.get("meshes", []) if isinstance(gltf.get("meshes"), list) else []:
        if not isinstance(mesh, Mapping):
            continue
        for primitive in mesh.get("primitives", []) if isinstance(mesh.get("primitives"), list) else []:
            if not isinstance(primitive, Mapping):
                continue
            attrs = primitive.get("attributes", {}) if isinstance(primitive.get("attributes"), Mapping) else {}
            index = attrs.get("POSITION")
            if isinstance(index, int) and 0 <= index < len(accessors) and isinstance(accessors[index], Mapping):
                results.append(accessors[index])
    return results


def inspect_glb_geometry(path: Path) -> dict[str, Any]:
    gltf = _read_glb_json(path)
    positions = _position_accessors(gltf)
    vertex_count = sum(int(item.get("count", 0) or 0) for item in positions)
    mins = [item.get("min") for item in positions if isinstance(item.get("min"), list) and len(item.get("min")) >= 3]
    maxs = [item.get("max") for item in positions if isinstance(item.get("max"), list) and len(item.get("max")) >= 3]
    bounds = None
    if mins and maxs:
        lo = [min(float(item[i]) for item in mins) for i in range(3)]
        hi = [max(float(item[i]) for item in maxs) for i in range(3)]
        bounds = {"min": lo, "max": hi, "size": [hi[i] - lo[i] for i in range(3)]}
    return {"path": str(path), "vertex_count": vertex_count, "bounds": bounds, "mesh_count": len(gltf.get("meshes", []) if isinstance(gltf.get("meshes"), list) else [])}


def _bounds_drift(source: Mapping[str, Any], lod: Mapping[str, Any]) -> float | None:
    source_bounds = source.get("bounds"); lod_bounds = lod.get("bounds")
    if not isinstance(source_bounds, Mapping) or not isinstance(lod_bounds, Mapping):
        return None
    source_size = source_bounds.get("size"); lod_size = lod_bounds.get("size")
    if not isinstance(source_size, list) or not isinstance(lod_size, list) or len(source_size) < 3 or len(lod_size) < 3:
        return None
    denominator = math.sqrt(sum(float(v) ** 2 for v in source_size))
    if denominator <= 0:
        return 0.0
    source_min = source_bounds.get("min", [0, 0, 0]); source_max = source_bounds.get("max", [0, 0, 0])
    lod_min = lod_bounds.get("min", [0, 0, 0]); lod_max = lod_bounds.get("max", [0, 0, 0])
    delta = math.sqrt(sum((float(source_min[i]) - float(lod_min[i])) ** 2 + (float(source_max[i]) - float(lod_max[i])) ** 2 for i in range(3)))
    return delta / denominator


def validate_post_lod_outputs(*, source: Path, high: Path, medium: Path, mesh_state_plan: Mapping[str, Any], section_id: str, required_hotspots: set[str] | None = None, max_bounds_drift: float = 0.02, visual_approval: Mapping[str, Any] | None = None) -> dict[str, Any]:
    failures: list[str] = []
    semantic_reports: dict[str, Any] = {}
    geometry: dict[str, Any] = {}
    for label, path in (("source", source), ("high", high), ("medium", medium)):
        if not path.is_file():
            failures.append(f"{label} GLB missing: {path}")
            continue
        try:
            semantic_reports[label] = validate_glb_authoring(path, mesh_state_plan, section_id, strict=True, required_hotspots=set(required_hotspots or ()))
            geometry[label] = inspect_glb_geometry(path)
        except (OSError, GLBValidationError) as exc:
            failures.append(f"{label}: {exc}")
            continue
        failures.extend(f"{label}: {item}" for item in semantic_reports[label].get("failures", []))

    if all(key in geometry for key in ("source", "high", "medium")):
        source_vertices = int(geometry["source"].get("vertex_count", 0)); high_vertices = int(geometry["high"].get("vertex_count", 0)); medium_vertices = int(geometry["medium"].get("vertex_count", 0))
        if source_vertices > 0 and not (0 < medium_vertices < high_vertices < source_vertices):
            failures.append("LOD vertex hierarchy must satisfy medium < high < source")
        for label in ("high", "medium"):
            drift = _bounds_drift(geometry["source"], geometry[label]); geometry[label]["bounds_drift"] = drift
            if drift is None:
                failures.append(f"{label}: geometry bounds metadata unavailable")
            elif drift > max_bounds_drift:
                failures.append(f"{label}: bounds drift {drift:.4f} exceeds {max_bounds_drift:.4f}")

    visual = dict(visual_approval or {})
    visual_status = "approved" if visual.get("approved") is True and visual.get("reviewer") and visual.get("evidence") else "needs-review"
    if visual_status != "approved":
        failures.append("visual QA approval with reviewer and evidence is required")

    return {"version": "1.0", "status": "blocked" if failures else "pass", "section_id": section_id, "semantic": semantic_reports, "geometry": geometry, "visual_qa": {"status": visual_status, **visual}, "policy": {"max_bounds_drift": max_bounds_drift, "semantic_revalidation_required": True, "visual_review_required": True}, "failures": failures}


def enforce_post_lod_qa(report: Mapping[str, Any]) -> None:
    if report.get("status") != "pass":
        raise LODQAGateError("CIE post-LOD QA gate blocked: " + "; ".join(str(item) for item in report.get("failures", [])))

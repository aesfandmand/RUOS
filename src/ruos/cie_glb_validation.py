from __future__ import annotations

import json
import struct
from pathlib import Path
from typing import Any, Mapping


class GLBValidationError(ValueError):
    pass


def _read_glb_json(path: Path) -> dict[str, Any]:
    data = path.read_bytes()
    if len(data) < 20 or data[:4] != b"glTF":
        raise GLBValidationError(f"Invalid GLB header: {path}")
    version, length = struct.unpack_from("<II", data, 4)
    if version != 2 or length > len(data):
        raise GLBValidationError(f"Unsupported or truncated GLB: {path}")
    chunk_length, chunk_type = struct.unpack_from("<II", data, 12)
    if chunk_type != 0x4E4F534A:
        raise GLBValidationError(f"GLB JSON chunk missing: {path}")
    raw = data[20:20 + chunk_length].rstrip(b" \t\r\n\x00")
    try:
        payload = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise GLBValidationError(f"Invalid GLB JSON chunk: {path}") from exc
    if not isinstance(payload, dict):
        raise GLBValidationError(f"GLB JSON root must be an object: {path}")
    return payload


def inspect_glb_authoring(path: Path) -> dict[str, Any]:
    gltf = _read_glb_json(path)
    nodes = sorted({str(item.get("name")) for item in gltf.get("nodes", []) if isinstance(item, Mapping) and item.get("name")})
    animations = sorted({str(item.get("name")) for item in gltf.get("animations", []) if isinstance(item, Mapping) and item.get("name")})
    variants: set[str] = set()
    extensions = gltf.get("extensions", {}) if isinstance(gltf.get("extensions"), Mapping) else {}
    materials_variants = extensions.get("KHR_materials_variants", {}) if isinstance(extensions.get("KHR_materials_variants"), Mapping) else {}
    for item in materials_variants.get("variants", []) if isinstance(materials_variants.get("variants"), list) else []:
        if isinstance(item, Mapping) and item.get("name"):
            variants.add(str(item["name"]))
    semantic_groups: set[str] = set()
    hotspot_anchors: set[str] = set()
    for name in nodes:
        lowered = name.lower()
        if lowered.startswith("cie-group-"):
            semantic_groups.add(lowered.removeprefix("cie-group-"))
        if lowered.startswith("cie-hotspot-"):
            hotspot_anchors.add(lowered.removeprefix("cie-hotspot-"))
    return {"path": str(path), "nodes": nodes, "animations": animations, "variants": sorted(variants), "semantic_groups": sorted(semantic_groups), "hotspot_anchors": sorted(hotspot_anchors)}


def validate_glb_authoring(path: Path, mesh_state_plan: Mapping[str, Any], section_id: str, *, strict: bool = True) -> dict[str, Any]:
    observed = inspect_glb_authoring(path)
    section = next((item for item in mesh_state_plan.get("sections", []) if isinstance(item, Mapping) and str(item.get("section_id", "")) == section_id), None)
    if section is None:
        return {"status": "not-applicable", "section_id": section_id, "failures": [], "observed": observed}
    contract = section.get("model_authoring_contract", {}) if isinstance(section.get("model_authoring_contract"), Mapping) else {}
    required_variants = {str(item) for item in contract.get("preferred_variant_names", [])}
    required_animations = {str(item) for item in contract.get("preferred_animation_names", [])}
    required_groups = {str(item.get("state")) for item in section.get("states", []) if isinstance(item, Mapping) and item.get("focus")}
    failures: list[str] = []
    missing_variants = sorted(required_variants - set(observed["variants"]))
    missing_animations = sorted(required_animations - set(observed["animations"]))
    missing_groups = sorted(required_groups - set(observed["semantic_groups"]))
    if strict:
        if missing_variants: failures.append("missing material variants: " + ", ".join(missing_variants))
        if missing_animations: failures.append("missing animations: " + ", ".join(missing_animations))
        if missing_groups: failures.append("missing semantic groups: " + ", ".join(missing_groups))
    return {"version": "1.0", "status": "blocked" if failures else "pass", "section_id": section_id, "strict": strict, "requirements": {"variants": sorted(required_variants), "animations": sorted(required_animations), "semantic_groups": sorted(required_groups), "hotspot_anchor_prefix": "cie-hotspot-", "semantic_group_prefix": "cie-group-"}, "missing": {"variants": missing_variants, "animations": missing_animations, "semantic_groups": missing_groups}, "failures": failures, "observed": observed}


def enforce_glb_authoring(report: Mapping[str, Any]) -> None:
    if report.get("status") == "blocked":
        raise GLBValidationError("CIE semantic GLB authoring gate blocked: " + "; ".join(str(item) for item in report.get("failures", [])))

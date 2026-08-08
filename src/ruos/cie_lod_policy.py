from __future__ import annotations

from typing import Any, Mapping


DEFAULT_LOD_POLICY = {
    "algorithm": "BLENDER_DECIMATE_COLLAPSE",
    "high_ratio": 0.75,
    "medium_ratio": 0.45,
    "min_medium_reduction": 0.35,
    "min_high_reduction": 0.15,
    "preserve_semantic_contract": True,
    "revalidate_glb_after_generation": True,
}


def build_lod_policy(overrides: Mapping[str, Any] | None = None) -> dict[str, Any]:
    policy = dict(DEFAULT_LOD_POLICY)
    if overrides:
        policy.update({key: value for key, value in overrides.items() if key in policy})
    high = float(policy["high_ratio"])
    medium = float(policy["medium_ratio"])
    if not 0.05 <= medium < high <= 1.0:
        raise ValueError("LOD ratios must satisfy 0.05 <= medium < high <= 1.0")
    return policy


def validate_lod_metrics(source_triangles: int, high_triangles: int, medium_triangles: int, policy: Mapping[str, Any]) -> dict[str, Any]:
    failures: list[str] = []
    if source_triangles <= 0:
        failures.append("source triangle count must be positive")
    else:
        high_reduction = 1 - (high_triangles / source_triangles)
        medium_reduction = 1 - (medium_triangles / source_triangles)
        if high_reduction < float(policy.get("min_high_reduction", 0.15)):
            failures.append("high LOD reduction below policy")
        if medium_reduction < float(policy.get("min_medium_reduction", 0.35)):
            failures.append("medium LOD reduction below policy")
        if medium_triangles >= high_triangles:
            failures.append("medium LOD must be lighter than high LOD")
    return {"version": "1.0", "status": "blocked" if failures else "pass", "source_triangles": source_triangles, "high_triangles": high_triangles, "medium_triangles": medium_triangles, "failures": failures}

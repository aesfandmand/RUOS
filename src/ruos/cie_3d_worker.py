from __future__ import annotations

import json
import shutil
from pathlib import Path
from typing import Any, Mapping


class ThreeDProductionError(ValueError):
    pass


def build_3d_production_jobs(authoring_manifest: Mapping[str, Any], source_map: Mapping[str, str] | None = None) -> dict[str, Any]:
    source_map = source_map or {}
    jobs: list[dict[str, Any]] = []
    for section in authoring_manifest.get("sections", []) if isinstance(authoring_manifest, Mapping) else []:
        if not isinstance(section, Mapping):
            continue
        section_id = str(section.get("section_id", ""))
        jobs.append({
            "job_id": f"3d-author-{section_id}",
            "section_id": section_id,
            "source": source_map.get(section_id),
            "output": f"assets/models/{section_id}/model.glb",
            "poster_output": f"assets/models/{section_id}/poster.webp",
            "required_nodes": list(section.get("required_node_names", [])),
            "required_variants": list(section.get("required_material_variants", [])),
            "required_animations": list(section.get("required_animation_names", [])),
            "lod_outputs": {
                "medium": f"assets/models/{section_id}/model-medium.glb",
                "high": f"assets/models/{section_id}/model-high.glb",
            },
            "worker": {
                "preferred": "blender",
                "fallback": "external-dcc",
                "non_destructive": True,
                "execution_requires_explicit_source": True,
            },
            "status": "ready-for-source" if source_map.get(section_id) else "awaiting-source",
        })
    return {
        "version": "1.0",
        "status": "ready" if jobs else "not-applicable",
        "blender_available": bool(shutil.which("blender")),
        "jobs": jobs,
    }


def write_3d_production_jobs(plan: Mapping[str, Any], output: Path) -> Path:
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(plan, ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")
    return output


def enforce_3d_production_sources(plan: Mapping[str, Any]) -> None:
    missing = [str(job.get("section_id")) for job in plan.get("jobs", []) if isinstance(job, Mapping) and job.get("status") != "ready-for-source"]
    if missing:
        raise ThreeDProductionError("CIE 3D production sources missing for sections: " + ", ".join(missing))

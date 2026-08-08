from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Mapping

from .cie_lod_policy import build_lod_policy
from .cie_lod_qa import enforce_post_lod_qa, validate_post_lod_outputs


def normalize_blender_job(job: Mapping[str, Any]) -> dict[str, Any]:
    lods = job.get("lod_outputs", {}) if isinstance(job.get("lod_outputs"), Mapping) else {}
    section_id = str(job.get("section_id", ""))
    normalized = dict(job)
    normalized["status"] = "ready" if job.get("status") in {"ready", "ready-for-source"} and job.get("source") else "blocked"
    normalized["outputs"] = {
        "glb": str(job.get("output", "")),
        "poster": str(job.get("poster_output", "")),
        "lod_medium": str(lods.get("medium", "")),
        "lod_high": str(lods.get("high", "")),
        "lod_report": f"assets/models/{section_id}/lod-report.json",
    }
    normalized["lod_policy"] = build_lod_policy()
    return normalized


def normalize_blender_plan(plan: Mapping[str, Any]) -> dict[str, Any]:
    jobs = [normalize_blender_job(job) for job in plan.get("jobs", []) if isinstance(job, Mapping)]
    return {"version": "1.0", "status": "ready" if jobs and all(job["status"] == "ready" for job in jobs) else "blocked", "jobs": jobs}


def build_post_lod_gate(*, blender_plan: Mapping[str, Any], project_root: Path, mesh_state_plan: Mapping[str, Any], hotspot_map: Mapping[str, set[str]] | None = None, visual_approvals: Mapping[str, Mapping[str, Any]] | None = None) -> dict[str, Any]:
    hotspot_map = hotspot_map or {}
    visual_approvals = visual_approvals or {}
    reports: list[dict[str, Any]] = []
    failures: list[str] = []
    for job in blender_plan.get("jobs", []) if isinstance(blender_plan, Mapping) else []:
        if not isinstance(job, Mapping):
            continue
        section_id = str(job.get("section_id", ""))
        outputs = job.get("outputs", {}) if isinstance(job.get("outputs"), Mapping) else {}
        source = project_root / str(outputs.get("glb", ""))
        high = project_root / str(outputs.get("lod_high", ""))
        medium = project_root / str(outputs.get("lod_medium", ""))
        report = validate_post_lod_outputs(source=source, high=high, medium=medium, mesh_state_plan=mesh_state_plan, section_id=section_id, required_hotspots=set(hotspot_map.get(section_id, set())), visual_approval=visual_approvals.get(section_id))
        reports.append(report)
        failures.extend(f"{section_id}: {failure}" for failure in report.get("failures", []))
    return {"version": "1.0", "status": "blocked" if failures else "pass", "reports": reports, "failures": failures}


def enforce_post_lod_build_gate(report: Mapping[str, Any]) -> None:
    if report.get("status") != "pass":
        raise ValueError("CIE post-LOD build gate blocked: " + "; ".join(str(item) for item in report.get("failures", [])))
    for item in report.get("reports", []):
        if isinstance(item, Mapping):
            enforce_post_lod_qa(item)


def write_post_lod_gate(report: Mapping[str, Any], output: Path) -> Path:
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")
    return output

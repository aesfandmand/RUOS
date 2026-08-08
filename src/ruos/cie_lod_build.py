from __future__ import annotations

import hashlib
import json
import shutil
from pathlib import Path
from typing import Any, Mapping

from .cie_lod_policy import build_lod_policy
from .cie_lod_qa import enforce_post_lod_qa, validate_post_lod_outputs


def _resolve_path(project_root: Path, value: object) -> Path:
    candidate = Path(str(value))
    return candidate if candidate.is_absolute() else project_root / candidate


def _file_record(path: Path, project_root: Path, *, lod: str) -> dict[str, Any]:
    digest = hashlib.sha256(path.read_bytes()).hexdigest()
    try:
        uri = path.relative_to(project_root).as_posix()
    except ValueError:
        uri = path.as_posix()
    return {
        "format": "glb",
        "lod": lod,
        "uri": uri,
        "bytes": path.stat().st_size,
        "kb": max(1, (path.stat().st_size + 1023) // 1024),
        "sha256": digest,
        "status": "produced",
        "approval": "post-lod-gate",
    }


def load_post_lod_gate(path: Path) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError(f"CIE post-LOD gate artifact could not be read: {path}: {exc}") from exc
    if not isinstance(payload, dict):
        raise ValueError("CIE post-LOD gate artifact must be a JSON object")
    return payload


def approved_lod_outputs(report: Mapping[str, Any], project_root: Path) -> dict[str, dict[str, Any]]:
    enforce_post_lod_build_gate(report)
    approved: dict[str, dict[str, Any]] = {}
    for item in report.get("reports", []) if isinstance(report.get("reports"), list) else []:
        if not isinstance(item, Mapping):
            continue
        section_id = str(item.get("section_id", "")).strip()
        if not section_id:
            raise ValueError("CIE post-LOD gate report is missing section_id")
        if section_id in approved:
            raise ValueError(f"CIE post-LOD gate contains duplicate section report: {section_id}")
        geometry = item.get("geometry", {}) if isinstance(item.get("geometry"), Mapping) else {}
        variants: list[dict[str, Any]] = []
        for lod in ("medium", "high"):
            observed = geometry.get(lod, {}) if isinstance(geometry.get(lod), Mapping) else {}
            path = _resolve_path(project_root, observed.get("path", ""))
            if not path.is_file():
                raise ValueError(f"CIE post-LOD approved {lod} GLB is missing for {section_id}: {path}")
            variants.append(_file_record(path, project_root, lod=lod))
        visual = item.get("visual_qa", {}) if isinstance(item.get("visual_qa"), Mapping) else {}
        raw_evidence = visual.get("evidence")
        evidence_values = list(raw_evidence) if isinstance(raw_evidence, list) else [raw_evidence] if raw_evidence else []
        evidence_paths: list[Path] = []
        for value in evidence_values:
            evidence = _resolve_path(project_root, value)
            if not evidence.is_file():
                raise ValueError(f"CIE post-LOD visual evidence is missing for {section_id}: {evidence}")
            evidence_paths.append(evidence)
        if not evidence_paths:
            raise ValueError(f"CIE post-LOD visual evidence is required for {section_id}")
        approved[section_id] = {
            "section_id": section_id,
            "variants": variants,
            "evidence": evidence_paths,
            "reviewer": str(visual.get("reviewer", "")),
        }
    if not approved:
        raise ValueError("CIE post-LOD gate artifact contains no approved section reports")
    return approved


def bind_approved_lod_outputs(production_report: Mapping[str, Any], gate_report: Mapping[str, Any], project_root: Path) -> dict[str, Any]:
    approved = approved_lod_outputs(gate_report, project_root)
    assets: list[dict[str, Any]] = []
    model_sections: set[str] = set()
    for raw in production_report.get("assets", []) if isinstance(production_report.get("assets"), list) else []:
        if not isinstance(raw, Mapping):
            continue
        item = dict(raw)
        if item.get("media_type") == "model-3d":
            section_id = str(item.get("section_id", "")).strip()
            if not section_id:
                raise ValueError(f"CIE model production result is missing section_id: {item.get('asset_id', 'unknown')}")
            if section_id not in approved:
                raise ValueError(f"CIE post-LOD gate does not cover runtime model section: {section_id}")
            model_sections.add(section_id)
            item["variants"] = [dict(variant) for variant in approved[section_id]["variants"]]
            item["status"] = "produced"
            item.pop("reason", None)
            item["post_lod_qa"] = {"status": "approved", "reviewer": approved[section_id]["reviewer"]}
        assets.append(item)
    if not model_sections:
        raise ValueError("CIE post-LOD gate was supplied but runtime media has no model-3d assets")
    extra_sections = sorted(set(approved) - model_sections)
    if extra_sections:
        raise ValueError("CIE post-LOD gate contains sections not present in runtime model delivery: " + ", ".join(extra_sections))
    observed = {
        "produced_bytes": sum(int(variant.get("bytes", 0) or 0) for item in assets for variant in item.get("variants", []) if isinstance(variant, Mapping) and variant.get("status") == "produced"),
        "produced_assets": sum(1 for item in assets if item.get("status") == "produced"),
        "partial_assets": sum(1 for item in assets if item.get("status") == "partial"),
        "blocked_assets": sum(1 for item in assets if item.get("status") == "blocked"),
    }
    return {**dict(production_report), "status": "produced" if assets and observed["blocked_assets"] == 0 else "partial" if assets else "blocked", "assets": assets, "observed": observed, "post_lod_qa": {"status": "approved", "sections": sorted(model_sections)}}


def materialize_post_lod_artifacts(report: Mapping[str, Any], project_root: Path, output_root: Path) -> tuple[dict[str, Any], tuple[Path, ...], dict[str, Any]]:
    approved = approved_lod_outputs(report, project_root)
    root = output_root / "assets" / "3d-qa"
    evidence_artifacts: list[str] = []
    copied: list[Path] = []
    for section_id, item in approved.items():
        for index, source in enumerate(item["evidence"], start=1):
            target = root / section_id / f"{index:02d}-{source.name}"
            target.parent.mkdir(parents=True, exist_ok=True)
            if source.resolve() != target.resolve():
                shutil.copy2(source, target)
            copied.append(target)
            evidence_artifacts.append(target.relative_to(output_root).as_posix())
    summary = {
        "version": str(report.get("version", "1.0")),
        "status": "pass",
        "runtime_delivery_blocking": True,
        "section_count": len(approved),
        "sections": sorted(approved),
        "artifact": "assets/3d-qa/post-lod-gate.json",
        "evidence_artifacts": sorted(evidence_artifacts),
    }
    enriched = {**dict(report), "runtime_delivery": summary}
    gate_path = write_post_lod_gate(enriched, output_root / summary["artifact"])
    return enriched, (gate_path, *copied), summary


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

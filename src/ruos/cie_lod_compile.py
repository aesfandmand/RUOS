from __future__ import annotations

import copy
import hashlib
import json
import re
import shutil
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
        section_id = str(entry.get("section_id") or sections.get(str(entry.get("asset_id", "")), ""))
        if not section_id:
            continue
        ids = {
            str(item.get("id") or item.get("entity"))
            for item in entry.get("hotspots", []) if isinstance(entry.get("hotspots"), list)
            if isinstance(item, Mapping) and (item.get("id") or item.get("entity"))
        }
        result.setdefault(section_id, set()).update(ids)
    return result


def build_compile_3d_plan_bundle(
    blueprint: Mapping[str, Any],
    source_map: Mapping[str, Any],
) -> dict[str, Any]:
    scene = blueprint.get("scene_orchestration", {})
    asset_media_plan = blueprint.get("asset_media_plan", {})
    authoring = build_3d_authoring_manifest(scene, asset_media_plan)
    if authoring.get("status") == "not-applicable":
        return {"version": "1.0", "status": "not-applicable", "authoring_manifest": authoring, "production_plan": {"jobs": []}, "blender_plan": {"jobs": []}}
    string_sources = {str(key): str(value) for key, value in source_map.items() if value}
    production_plan = build_3d_production_jobs(authoring, string_sources)
    blender_plan = normalize_blender_plan(production_plan)
    if blender_plan.get("status") != "ready":
        raise ValueError("CIE 3D LOD QA requires a bound source for every authored model section")
    return {"version": "1.0", "status": "ready", "authoring_manifest": authoring, "production_plan": production_plan, "blender_plan": blender_plan}


def _evidence_values(value: object) -> list[str]:
    raw = value if isinstance(value, list) else [value] if value else []
    return [str(item).strip() for item in raw if str(item).strip()]


def _project_file(project_root: Path, value: object) -> Path:
    candidate = Path(str(value))
    return candidate if candidate.is_absolute() else project_root / candidate


def validate_visual_approval_evidence(project_root: Path, approvals: Mapping[str, Any]) -> dict[str, Any]:
    normalized: dict[str, Any] = {}
    for key, value in approvals.items():
        if not isinstance(value, Mapping):
            continue
        approval = dict(value)
        if approval.get("approved") is True:
            evidence = _evidence_values(approval.get("evidence"))
            if not evidence:
                raise ValueError(f"CIE 3D visual approval evidence is required for {key}")
            for item in evidence:
                path = _project_file(project_root, item)
                if not path.is_file():
                    raise ValueError(f"CIE 3D visual approval evidence is missing for {key}: {path}")
            approval["evidence"] = evidence
        normalized[str(key)] = approval
    return normalized


def build_compile_post_lod_gate(
    blueprint: Mapping[str, Any],
    project_root: Path,
    source_map: Mapping[str, Any],
    visual_approvals: Mapping[str, Any],
) -> dict[str, Any]:
    scene = blueprint.get("scene_orchestration", {})
    asset_media_plan = blueprint.get("asset_media_plan", {})
    registry = blueprint.get("asset_source_registry", {})
    plan_bundle = build_compile_3d_plan_bundle(blueprint, source_map)
    if plan_bundle.get("status") == "not-applicable":
        return {**plan_bundle, "gate": {"status": "not-applicable", "reports": [], "failures": []}}
    blender_plan = plan_bundle["blender_plan"]
    source_delivery = build_source_model_delivery(registry, asset_media_plan)
    mesh_state_plan = build_mesh_state_plan(scene, source_delivery)
    approvals = validate_visual_approval_evidence(project_root, visual_approvals)
    gate = build_post_lod_gate(
        blender_plan=blender_plan,
        project_root=project_root,
        mesh_state_plan=mesh_state_plan,
        hotspot_map=_hotspot_map(registry, asset_media_plan),
        visual_approvals=approvals,
    )
    enforce_post_lod_build_gate(gate)
    return {**plan_bundle, "status": "pass", "mesh_state_plan": mesh_state_plan, "gate": gate}


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
            section_id = str(item.get("section_id") or section_by_asset.get(str(item.get("asset_id", "")), ""))
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
            updated["section_id"] = section_id
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


def materialize_post_lod_evidence(
    gate_bundle: Mapping[str, Any],
    project_root: Path,
    output_dir: Path,
) -> tuple[dict[str, Any], tuple[Path, ...], dict[str, Any]]:
    if gate_bundle.get("status") != "pass":
        raise ValueError("CIE post-LOD evidence materialization requires a passing gate")
    payload = copy.deepcopy(dict(gate_bundle))
    gate = dict(payload.get("gate", {}))
    reports: list[dict[str, Any]] = []
    evidence_artifacts: list[str] = []
    sections: list[str] = []
    files: list[Path] = []
    for raw in gate.get("reports", []) if isinstance(gate.get("reports"), list) else []:
        if not isinstance(raw, Mapping):
            continue
        report = dict(raw)
        section_id = str(report.get("section_id", "")).strip()
        if not section_id:
            raise ValueError("CIE post-LOD gate report is missing section_id")
        safe_section = re.sub(r"[^A-Za-z0-9._-]+", "-", section_id).strip("-.") or "section"
        visual = dict(report.get("visual_qa", {}))
        evidence = _evidence_values(visual.get("evidence"))
        if not evidence:
            raise ValueError(f"CIE post-LOD visual evidence is required for {section_id}")
        retained: list[str] = []
        for index, value in enumerate(evidence, start=1):
            source = _project_file(project_root, value)
            if not source.is_file():
                raise ValueError(f"CIE post-LOD visual evidence is missing for {section_id}: {source}")
            safe_name = re.sub(r"[^A-Za-z0-9._-]+", "-", source.name).strip("-.") or f"evidence-{index}"
            relative = Path("assets/3d-qa") / safe_section / f"{index:02d}-{safe_name}"
            target = output_dir / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            if source.resolve() != target.resolve():
                shutil.copy2(source, target)
            uri = relative.as_posix()
            retained.append(uri); evidence_artifacts.append(uri); files.append(target)
        visual["evidence"] = retained
        report["visual_qa"] = visual
        reports.append(report); sections.append(section_id)
    if not reports:
        raise ValueError("CIE post-LOD gate contains no approved section reports")
    if len(set(sections)) != len(sections):
        raise ValueError("CIE post-LOD gate contains duplicate section reports")
    gate["reports"] = reports
    payload["gate"] = gate
    summary = {
        "version": str(payload.get("version", "1.0")),
        "status": "pass",
        "artifact": "assets/post-lod-gate.json",
        "runtime_delivery_blocking": True,
        "sections": sorted(sections),
        "evidence_artifacts": sorted(evidence_artifacts),
    }
    payload["runtime_delivery"] = summary
    gate_path = output_dir / summary["artifact"]
    gate_path.parent.mkdir(parents=True, exist_ok=True)
    gate_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")
    files.append(gate_path)
    return payload, tuple(files), summary


def validate_runtime_lod_delivery(
    runtime_delivery: Mapping[str, Any],
    gate_bundle: Mapping[str, Any],
    project_root: Path,
) -> dict[str, Any]:
    expected: dict[str, dict[str, str]] = {}
    for job in gate_bundle.get("blender_plan", {}).get("jobs", []) if isinstance(gate_bundle.get("blender_plan"), Mapping) else []:
        if not isinstance(job, Mapping):
            continue
        section_id = str(job.get("section_id", ""))
        outputs = job.get("outputs", {}) if isinstance(job.get("outputs"), Mapping) else {}
        hashes: dict[str, str] = {}
        for lod, key in (("high", "lod_high"), ("medium", "lod_medium")):
            path = _project_file(project_root, outputs.get(key, ""))
            if not path.is_file():
                raise ValueError(f"CIE approved {lod} LOD is missing for runtime section: {section_id}")
            hashes[lod] = hashlib.sha256(path.read_bytes()).hexdigest()
        expected[section_id] = hashes
    if not expected:
        raise ValueError("CIE post-LOD gate contains no approved runtime model sections")
    delivered: list[dict[str, Any]] = []
    for binding in runtime_delivery.get("bindings", []) if isinstance(runtime_delivery, Mapping) else []:
        if not isinstance(binding, Mapping) or binding.get("media_type") != "model-3d" or binding.get("status") != "ready":
            continue
        section_id = str(binding.get("section_id", ""))
        variants = {
            str(item.get("lod")): item
            for item in binding.get("variants", []) if isinstance(binding.get("variants"), list)
            if isinstance(item, Mapping) and item.get("lod") in {"high", "medium"}
        }
        if set(variants) != {"high", "medium"}:
            raise ValueError(f"CIE runtime model delivery must bind approved high and medium LODs for {section_id}")
        if section_id not in expected:
            raise ValueError(f"CIE runtime model delivery contains an unapproved section: {section_id}")
        for lod, item in variants.items():
            if str(item.get("sha256", "")) != expected[section_id][lod]:
                raise ValueError(f"CIE runtime {lod} LOD does not match the approved artifact for {section_id}")
        delivered.append({
            "asset_id": str(binding.get("asset_id", "")),
            "section_id": section_id,
            "lods": {lod: str(variants[lod].get("uri", "")) for lod in ("high", "medium")},
            "sha256": {lod: expected[section_id][lod] for lod in ("high", "medium")},
        })
    if {item["section_id"] for item in delivered} != set(expected):
        raise ValueError("CIE post-LOD approved sections do not match runtime model delivery")
    return {
        "version": str(gate_bundle.get("version", "1.0")),
        "status": "pass",
        "artifact": "assets/post-lod-gate.json",
        "runtime_delivery_blocking": True,
        "sections": sorted(expected),
        "delivered_models": delivered,
    }

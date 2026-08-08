from __future__ import annotations

import json
import shutil
import subprocess
from pathlib import Path
from typing import Any, Mapping

from PIL import Image, ImageChops, ImageStat

from .cie_lod_compile import build_compile_3d_plan_bundle


class VisualEvidenceError(ValueError):
    pass


DEFAULT_VIEWS = (
    {"id": "front", "azimuth": 0.0, "elevation": 10.0, "distance_factor": 2.8},
    {"id": "three-quarter", "azimuth": 38.0, "elevation": 18.0, "distance_factor": 2.9},
    {"id": "side", "azimuth": 90.0, "elevation": 10.0, "distance_factor": 2.8},
)


def build_visual_evidence_plan(blender_plan: Mapping[str, Any], views: tuple[Mapping[str, Any], ...] = DEFAULT_VIEWS) -> dict[str, Any]:
    jobs: list[dict[str, Any]] = []
    for job in blender_plan.get("jobs", []) if isinstance(blender_plan, Mapping) else []:
        if not isinstance(job, Mapping) or job.get("status") != "ready":
            continue
        section_id = str(job.get("section_id", ""))
        outputs = job.get("outputs", {}) if isinstance(job.get("outputs"), Mapping) else {}
        models = {"source": outputs.get("glb"), "high": outputs.get("lod_high"), "medium": outputs.get("lod_medium")}
        shots: list[dict[str, Any]] = []
        for view in views:
            view_id = str(view.get("id", "view"))
            for level, model_uri in models.items():
                if not model_uri:
                    continue
                shots.append({
                    "shot_id": f"{section_id}-{level}-{view_id}",
                    "section_id": section_id,
                    "level": level,
                    "view": dict(view),
                    "model_uri": str(model_uri),
                    "output_uri": f"assets/models/{section_id}/qa/{level}-{view_id}.png",
                })
        jobs.append({"section_id": section_id, "status": "ready" if shots else "blocked", "shots": shots})
    return {"version": "1.0", "status": "ready" if jobs and all(job["status"] == "ready" for job in jobs) else "blocked", "render_contract": {"same_camera_per_view": True, "same_lighting_per_view": True, "resolution": [768, 768], "format": "PNG", "human_approval_still_required": True}, "jobs": jobs}


def _normalized_mae(source: Path, candidate: Path) -> float:
    with Image.open(source) as source_image, Image.open(candidate) as candidate_image:
        a = source_image.convert("RGB")
        b = candidate_image.convert("RGB")
        if a.size != b.size:
            raise VisualEvidenceError(f"Visual evidence dimensions differ: {source} {a.size} vs {candidate} {b.size}")
        difference = ImageChops.difference(a, b)
        means = ImageStat.Stat(difference).mean
        return sum(float(value) for value in means) / (3.0 * 255.0)


def evaluate_visual_evidence(plan: Mapping[str, Any], project_root: Path, *, high_mae_limit: float = 0.08, medium_mae_limit: float = 0.14) -> dict[str, Any]:
    reports: list[dict[str, Any]] = []
    failures: list[str] = []
    for job in plan.get("jobs", []) if isinstance(plan, Mapping) else []:
        if not isinstance(job, Mapping):
            continue
        section_id = str(job.get("section_id", ""))
        by_view: dict[str, dict[str, Path]] = {}
        evidence: list[str] = []
        for shot in job.get("shots", []) if isinstance(job.get("shots"), list) else []:
            if not isinstance(shot, Mapping):
                continue
            output = project_root / str(shot.get("output_uri", ""))
            if not output.is_file():
                failures.append(f"{section_id}: missing visual evidence {output}")
                continue
            view_id = str(shot.get("view", {}).get("id", "view")) if isinstance(shot.get("view"), Mapping) else "view"
            by_view.setdefault(view_id, {})[str(shot.get("level", ""))] = output
            evidence.append(output.relative_to(project_root).as_posix() if output.is_relative_to(project_root) else output.as_posix())
        comparisons: list[dict[str, Any]] = []
        for view_id, levels in by_view.items():
            source = levels.get("source")
            if source is None:
                failures.append(f"{section_id}/{view_id}: source visual evidence missing")
                continue
            for level, limit in (("high", high_mae_limit), ("medium", medium_mae_limit)):
                candidate = levels.get(level)
                if candidate is None:
                    failures.append(f"{section_id}/{view_id}: {level} visual evidence missing")
                    continue
                mae = _normalized_mae(source, candidate)
                signal = "within-advisory-threshold" if mae <= limit else "investigate"
                if signal == "investigate":
                    failures.append(f"{section_id}/{view_id}/{level}: normalized MAE {mae:.4f} exceeds advisory {limit:.4f}")
                comparisons.append({"view": view_id, "level": level, "normalized_mae": round(mae, 6), "advisory_limit": limit, "signal": signal})
        reports.append({"section_id": section_id, "evidence": sorted(evidence), "comparisons": comparisons})
    return {"version": "1.0", "status": "evidence-ready" if not failures else "needs-review", "automated_signal_only": True, "human_approval_required": True, "reports": reports, "failures": failures}


def build_visual_approval_template(report: Mapping[str, Any]) -> dict[str, Any]:
    approvals: dict[str, Any] = {}
    for item in report.get("reports", []) if isinstance(report, Mapping) else []:
        if not isinstance(item, Mapping):
            continue
        approvals[str(item.get("section_id", ""))] = {"approved": False, "reviewer": None, "evidence": list(item.get("evidence", [])), "automated_signal": report.get("status"), "review_notes": None}
    return approvals


def execute_visual_evidence_plan(plan: Mapping[str, Any], project_root: Path, script_path: Path, *, executable: str = "blender", timeout: int = 300) -> dict[str, Any]:
    blender = shutil.which(executable)
    if blender is None:
        raise VisualEvidenceError(f"Blender executable not available: {executable}")
    completed_shots = 0
    failures: list[str] = []
    for job in plan.get("jobs", []) if isinstance(plan, Mapping) else []:
        if not isinstance(job, Mapping):
            continue
        for shot in job.get("shots", []) if isinstance(job.get("shots"), list) else []:
            if not isinstance(shot, Mapping):
                continue
            model = project_root / str(shot.get("model_uri", ""))
            output = project_root / str(shot.get("output_uri", ""))
            if not model.is_file():
                failures.append(f"{shot.get('shot_id')}: model missing: {model}")
                continue
            payload = {"model": str(model), "output": str(output), "view": dict(shot.get("view", {}))}
            command = [blender, "-b", "--python", str(script_path), "--", json.dumps(payload, separators=(",", ":"))]
            try:
                result = subprocess.run(command, cwd=project_root, capture_output=True, text=True, timeout=timeout, check=False)
            except subprocess.TimeoutExpired:
                failures.append(f"{shot.get('shot_id')}: Blender evidence render timed out after {timeout}s")
                continue
            if result.returncode != 0 or not output.is_file():
                failures.append(f"{shot.get('shot_id')}: Blender evidence render failed")
            else:
                completed_shots += 1
    return {"version": "1.0", "status": "rendered" if not failures else "blocked", "completed_shots": completed_shots, "failures": failures}


def _write_json(path: Path, payload: Mapping[str, Any]) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")
    return path


def capture_visual_evidence(
    *,
    page_slug: str,
    blueprint: Mapping[str, Any],
    project_root: Path,
    source_map: Mapping[str, Any],
    output_root: Path,
    script_path: Path,
    executable: str = "blender",
    timeout: int = 300,
) -> dict[str, Any]:
    if not script_path.is_file():
        raise VisualEvidenceError(f"CIE Blender visual evidence script not found: {script_path}")
    plan_bundle = build_compile_3d_plan_bundle(blueprint, source_map)
    if plan_bundle.get("status") != "ready":
        raise VisualEvidenceError("CIE visual evidence capture requires at least one ready 3D model section")
    visual_plan = build_visual_evidence_plan(plan_bundle["blender_plan"])
    if visual_plan.get("status") != "ready":
        raise VisualEvidenceError("CIE visual evidence plan is blocked")

    paths = {
        "compile_plan": output_root / f"{page_slug}.3d-compile-plan.json",
        "visual_plan": output_root / f"{page_slug}.visual-evidence-plan.json",
        "render_report": output_root / f"{page_slug}.visual-evidence-run.json",
        "evaluation": output_root / f"{page_slug}.visual-evidence-report.json",
        "approvals": output_root / f"{page_slug}.visual-approvals.json",
    }
    _write_json(paths["compile_plan"], plan_bundle)
    _write_json(paths["visual_plan"], visual_plan)
    render_report = execute_visual_evidence_plan(visual_plan, project_root, script_path, executable=executable, timeout=timeout)
    _write_json(paths["render_report"], render_report)
    if render_report.get("status") != "rendered":
        raise VisualEvidenceError("CIE visual evidence render blocked: " + "; ".join(str(item) for item in render_report.get("failures", [])))
    evaluation = evaluate_visual_evidence(visual_plan, project_root)
    approvals = build_visual_approval_template(evaluation)
    _write_json(paths["evaluation"], evaluation)
    _write_json(paths["approvals"], approvals)
    return {
        "version": "1.0",
        "status": evaluation.get("status", "needs-review"),
        "human_approval_required": True,
        "paths": {key: path.as_posix() for key, path in paths.items()},
        "completed_shots": render_report.get("completed_shots", 0),
    }

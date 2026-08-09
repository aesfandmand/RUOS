from __future__ import annotations

import json
import shutil
import subprocess
from pathlib import Path
from typing import Any, Mapping


class BlenderWorkerError(RuntimeError):
    pass


def discover_blender(executable: str = "blender") -> str | None:
    return shutil.which(executable)


def build_blender_command(job: Mapping[str, Any], project_root: Path, script_path: Path, *, executable: str = "blender") -> list[str]:
    source = project_root / str(job.get("source", ""))
    if not source.is_file():
        raise BlenderWorkerError(f"3D source file not found: {source}")
    blender = discover_blender(executable)
    if blender is None:
        raise BlenderWorkerError(f"Blender executable not available: {executable}")
    return [blender, "-b", str(source), "--python", str(script_path), "--", json.dumps(dict(job), ensure_ascii=False, separators=(",", ":"))]


def execute_blender_job(job: Mapping[str, Any], project_root: Path, script_path: Path, *, executable: str = "blender", timeout: int = 900) -> dict[str, Any]:
    command = build_blender_command(job, project_root, script_path, executable=executable)
    completed = subprocess.run(command, cwd=project_root, capture_output=True, text=True, timeout=timeout, check=False)
    outputs = job.get("outputs", {}) if isinstance(job.get("outputs"), Mapping) else {}
    observed = {name: (project_root / str(path)).is_file() for name, path in outputs.items()}
    status = "success" if completed.returncode == 0 and all(observed.values()) else "blocked"
    report = {"version": "1.0", "job_id": str(job.get("job_id", "")), "status": status, "returncode": completed.returncode, "outputs": observed, "stdout_tail": completed.stdout[-4000:], "stderr_tail": completed.stderr[-4000:]}
    if status != "success":
        raise BlenderWorkerError("Blender production job failed: " + json.dumps(report, ensure_ascii=False))
    return report


def execute_ready_jobs(plan: Mapping[str, Any], project_root: Path, script_path: Path, *, executable: str = "blender") -> dict[str, Any]:
    reports: list[dict[str, Any]] = []
    failures: list[str] = []
    for job in plan.get("jobs", []):
        if not isinstance(job, Mapping) or job.get("status") != "ready":
            continue
        try:
            reports.append(execute_blender_job(job, project_root, script_path, executable=executable))
        except BlenderWorkerError as exc:
            failures.append(str(exc))
    return {"version": "1.0", "status": "blocked" if failures else "success", "executed_jobs": len(reports), "reports": reports, "failures": failures}

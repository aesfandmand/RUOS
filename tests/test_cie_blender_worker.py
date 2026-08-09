from pathlib import Path

import pytest

from ruos.cie_blender_worker import BlenderWorkerError, build_blender_command, execute_ready_jobs


def _job():
    return {"job_id": "technical", "status": "ready", "source": "source/model.blend", "outputs": {"glb": "build/model.glb", "poster": "build/poster.png", "lod_medium": "build/model-medium.glb", "lod_high": "build/model-high.glb"}}


def test_command_blocks_missing_source(tmp_path):
    with pytest.raises(BlenderWorkerError, match="source file not found"):
        build_blender_command(_job(), tmp_path, tmp_path / "export.py")


def test_command_blocks_missing_blender(tmp_path, monkeypatch):
    source = tmp_path / "source/model.blend"; source.parent.mkdir(); source.write_bytes(b"BLENDER")
    monkeypatch.setattr("ruos.cie_blender_worker.discover_blender", lambda executable="blender": None)
    with pytest.raises(BlenderWorkerError, match="Blender executable not available"):
        build_blender_command(_job(), tmp_path, tmp_path / "export.py")


def test_ready_job_execution_reports_success_with_fake_blender(tmp_path, monkeypatch):
    source = tmp_path / "source/model.blend"; source.parent.mkdir(); source.write_bytes(b"BLENDER")
    fake = tmp_path / "blender"; fake.write_text("#!/bin/sh\nexit 0\n"); fake.chmod(0o755)
    monkeypatch.setattr("ruos.cie_blender_worker.discover_blender", lambda executable="blender": str(fake))

    class Result:
        returncode = 0; stdout = "ok"; stderr = ""
    def run(command, **kwargs):
        for path in _job()["outputs"].values():
            target = tmp_path / path; target.parent.mkdir(parents=True, exist_ok=True); target.write_bytes(b"artifact")
        return Result()
    monkeypatch.setattr("ruos.cie_blender_worker.subprocess.run", run)
    report = execute_ready_jobs({"jobs": [_job()]}, tmp_path, tmp_path / "export.py")
    assert report["status"] == "success"
    assert report["executed_jobs"] == 1

from pathlib import Path

import pytest

from ruos.cie_lod_build import (
    bind_approved_lod_outputs,
    enforce_post_lod_build_gate,
    materialize_post_lod_artifacts,
    normalize_blender_plan,
)


def test_normalize_blender_plan_bridges_3d_job_schema():
    plan = {"jobs": [{"job_id": "3d-author-technical", "section_id": "technical", "source": "source/model.blend", "output": "assets/models/technical/model.glb", "poster_output": "assets/models/technical/poster.webp", "lod_outputs": {"medium": "assets/models/technical/model-medium.glb", "high": "assets/models/technical/model-high.glb"}, "status": "ready-for-source"}]}
    normalized = normalize_blender_plan(plan)
    job = normalized["jobs"][0]
    assert normalized["status"] == "ready"
    assert job["status"] == "ready"
    assert job["outputs"]["glb"].endswith("model.glb")
    assert job["outputs"]["lod_medium"].endswith("model-medium.glb")
    assert job["outputs"]["lod_high"].endswith("model-high.glb")
    assert job["outputs"]["lod_report"].endswith("lod-report.json")
    assert job["lod_policy"]["medium_ratio"] < job["lod_policy"]["high_ratio"]


def test_normalize_blender_plan_blocks_missing_source():
    plan = {"jobs": [{"job_id": "3d-author-technical", "section_id": "technical", "source": None, "output": "assets/models/technical/model.glb", "lod_outputs": {}, "status": "awaiting-source"}]}
    assert normalize_blender_plan(plan)["status"] == "blocked"


def test_post_lod_build_gate_enforcement_blocks_failures():
    with pytest.raises(ValueError, match="post-LOD build gate blocked"):
        enforce_post_lod_build_gate({"status": "blocked", "reports": [], "failures": ["technical: visual approval required"]})


def _approved_gate(tmp_path: Path):
    high = tmp_path / "models/technical/high.glb"
    medium = tmp_path / "models/technical/medium.glb"
    evidence = tmp_path / "reviews/technical-comparison.png"
    high.parent.mkdir(parents=True)
    medium.write_bytes(b"medium-approved")
    high.write_bytes(b"high-approved")
    evidence.parent.mkdir(parents=True)
    evidence.write_bytes(b"comparison")
    item = {
        "status": "pass",
        "section_id": "technical",
        "semantic": {},
        "geometry": {"medium": {"path": str(medium)}, "high": {"path": str(high)}},
        "visual_qa": {"status": "approved", "approved": True, "reviewer": "qa-reviewer", "evidence": str(evidence)},
        "failures": [],
    }
    return {"version": "1.0", "status": "pass", "reports": [item], "failures": []}


def test_approved_lod_gate_replaces_runtime_model_variants_and_is_materialized(tmp_path: Path):
    gate = _approved_gate(tmp_path)
    report = {
        "version": "1.0",
        "status": "produced",
        "assets": [{"asset_id": "technical-model", "section_id": "technical", "media_type": "model-3d", "priority": "auto", "status": "partial", "variants": []}],
        "observed": {},
    }
    approved = bind_approved_lod_outputs(report, gate, tmp_path)
    model = approved["assets"][0]
    assert model["status"] == "produced"
    assert [item["lod"] for item in model["variants"]] == ["medium", "high"]
    assert all(item["sha256"] for item in model["variants"])
    enriched, files, summary = materialize_post_lod_artifacts(gate, tmp_path, tmp_path / "dist")
    assert enriched["runtime_delivery"]["status"] == "pass"
    assert summary["runtime_delivery_blocking"] is True
    assert all(path.is_file() for path in files)
    assert summary["evidence_artifacts"] == ["assets/3d-qa/technical/01-technical-comparison.png"]


def test_runtime_lod_binding_rejects_missing_visual_evidence(tmp_path: Path):
    gate = _approved_gate(tmp_path)
    Path(gate["reports"][0]["visual_qa"]["evidence"]).unlink()
    report = {"assets": [{"asset_id": "technical-model", "section_id": "technical", "media_type": "model-3d", "status": "produced", "variants": []}]}
    with pytest.raises(ValueError, match="visual evidence is missing"):
        bind_approved_lod_outputs(report, gate, tmp_path)

from pathlib import Path

import pytest

from ruos.cie_lod_build import enforce_post_lod_build_gate, normalize_blender_plan


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

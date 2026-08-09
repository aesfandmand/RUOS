from pathlib import Path

import pytest

from ruos.cie_3d_authoring_manifest import build_3d_authoring_manifest
from ruos.cie_3d_worker import ThreeDProductionError, build_3d_production_jobs, enforce_3d_production_sources, write_3d_production_jobs
from ruos.cie_build import generate_cie_blueprint
from ruos.spec_loader import load_page_spec


def _manifest():
    page = load_page_spec(Path("pages/structures.json"))
    blueprint = generate_cie_blueprint(page)
    return build_3d_authoring_manifest(blueprint["scene_orchestration"], blueprint["asset_media_plan"])


def test_worker_plan_preserves_authoring_requirements(tmp_path):
    manifest = _manifest()
    plan = build_3d_production_jobs(manifest)
    assert plan["status"] == "ready"
    assert plan["jobs"]
    assert all(job["required_variants"] for job in plan["jobs"])
    assert all(job["required_animations"] for job in plan["jobs"])
    path = write_3d_production_jobs(plan, tmp_path / "3d-production-jobs.json")
    assert path.is_file()


def test_worker_requires_explicit_sources_before_execution():
    plan = build_3d_production_jobs(_manifest())
    with pytest.raises(ThreeDProductionError):
        enforce_3d_production_sources(plan)


def test_worker_marks_bound_sources_ready():
    manifest = _manifest()
    sources = {section["section_id"]: f"source/{section['section_id']}.blend" for section in manifest["sections"]}
    plan = build_3d_production_jobs(manifest, sources)
    enforce_3d_production_sources(plan)
    assert all(job["status"] == "ready-for-source" for job in plan["jobs"])

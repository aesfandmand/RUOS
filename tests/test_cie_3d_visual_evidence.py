from pathlib import Path

from PIL import Image

from ruos.cie_3d_visual_evidence import build_visual_approval_template, build_visual_evidence_plan, evaluate_visual_evidence


def _blender_plan():
    return {"jobs": [{"section_id": "technical", "status": "ready", "outputs": {"glb": "assets/models/technical/model.glb", "lod_high": "assets/models/technical/model-high.glb", "lod_medium": "assets/models/technical/model-medium.glb"}}]}


def test_visual_evidence_plan_uses_same_views_for_all_lods():
    plan = build_visual_evidence_plan(_blender_plan())
    shots = plan["jobs"][0]["shots"]
    assert plan["status"] == "ready"
    assert len(shots) == 9
    assert {shot["level"] for shot in shots} == {"source", "high", "medium"}
    assert {shot["view"]["id"] for shot in shots} == {"front", "three-quarter", "side"}


def test_identical_visual_evidence_is_ready_but_not_human_approved(tmp_path: Path):
    plan = build_visual_evidence_plan(_blender_plan())
    for shot in plan["jobs"][0]["shots"]:
        output = tmp_path / shot["output_uri"]
        output.parent.mkdir(parents=True, exist_ok=True)
        Image.new("RGB", (64, 64), (90, 90, 90)).save(output)
    report = evaluate_visual_evidence(plan, tmp_path)
    assert report["status"] == "evidence-ready"
    assert report["automated_signal_only"] is True
    template = build_visual_approval_template(report)
    assert template["technical"]["approved"] is False
    assert template["technical"]["reviewer"] is None
    assert template["technical"]["evidence"]


def test_large_visual_difference_is_flagged_for_review(tmp_path: Path):
    plan = build_visual_evidence_plan(_blender_plan())
    for shot in plan["jobs"][0]["shots"]:
        output = tmp_path / shot["output_uri"]
        output.parent.mkdir(parents=True, exist_ok=True)
        value = 0 if shot["level"] == "source" else 255
        Image.new("RGB", (32, 32), (value, value, value)).save(output)
    report = evaluate_visual_evidence(plan, tmp_path)
    assert report["status"] == "needs-review"
    assert any("normalized MAE" in failure for failure in report["failures"])

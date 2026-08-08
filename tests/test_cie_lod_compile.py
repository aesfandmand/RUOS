import hashlib
from pathlib import Path

import pytest

from ruos.cie_lod_compile import bind_validated_lods_to_media_report, materialize_post_lod_evidence, validate_runtime_lod_delivery, validate_visual_approval_evidence


def _media_plan():
    return {"sections": [{"section_id": "technical", "assets": [{"asset_id": "model-a", "media_type": "model-3d"}]}]}


def _bundle():
    return {
        "status": "pass",
        "blender_plan": {
            "jobs": [{
                "section_id": "technical",
                "outputs": {
                    "lod_high": "assets/models/technical/model-high.glb",
                    "lod_medium": "assets/models/technical/model-medium.glb",
                },
            }]
        },
    }


def test_validated_lods_replace_generic_model_derivatives(tmp_path: Path):
    high = tmp_path / "assets/models/technical/model-high.glb"
    medium = tmp_path / "assets/models/technical/model-medium.glb"
    high.parent.mkdir(parents=True)
    high.write_bytes(b"HIGH-VALIDATED")
    medium.write_bytes(b"MEDIUM-VALIDATED")
    report = {"version": "1.0", "assets": [{"asset_id": "model-a", "media_type": "model-3d", "status": "partial", "variants": [{"lod": "high", "status": "produced", "uri": "generic.glb"}]}]}
    bound = bind_validated_lods_to_media_report(report, _bundle(), _media_plan(), tmp_path)
    model = bound["assets"][0]
    assert bound["validated_3d_lod_binding"] is True
    assert model["source"] == "post-lod-qa-approved"
    assert [item["lod"] for item in model["variants"]] == ["high", "medium"]
    assert all(item["sha256"] for item in model["variants"])
    assert all(item["status"] == "produced" for item in model["variants"])


def test_runtime_lod_binding_rejects_unapproved_gate(tmp_path: Path):
    with pytest.raises(ValueError, match="passing post-LOD gate"):
        bind_validated_lods_to_media_report({"assets": []}, {"status": "blocked"}, _media_plan(), tmp_path)


def test_visual_approval_requires_real_evidence_and_materializes_it(tmp_path: Path):
    evidence = tmp_path / "reviews/compare.png"
    evidence.parent.mkdir(parents=True)
    evidence.write_bytes(b"comparison")
    approvals = validate_visual_approval_evidence(tmp_path, {"technical": {"approved": True, "reviewer": "qa", "evidence": ["reviews/compare.png"]}})
    bundle = {"version": "1.0", "status": "pass", "gate": {"status": "pass", "reports": [{"section_id": "technical", "visual_qa": approvals["technical"]}], "failures": []}}
    materialized, files, summary = materialize_post_lod_evidence(bundle, tmp_path, tmp_path / "dist")
    assert summary["evidence_artifacts"] == ["assets/3d-qa/technical/01-compare.png"]
    assert all(path.is_file() for path in files)
    assert materialized["gate"]["reports"][0]["visual_qa"]["evidence"] == summary["evidence_artifacts"]


def test_visual_approval_rejects_missing_evidence(tmp_path: Path):
    with pytest.raises(ValueError, match="evidence is missing"):
        validate_visual_approval_evidence(tmp_path, {"technical": {"approved": True, "reviewer": "qa", "evidence": "missing.png"}})


def test_runtime_delivery_must_match_approved_lod_hashes(tmp_path: Path):
    high = tmp_path / "assets/models/technical/model-high.glb"
    medium = tmp_path / "assets/models/technical/model-medium.glb"
    high.parent.mkdir(parents=True)
    high.write_bytes(b"approved-high"); medium.write_bytes(b"approved-medium")
    bundle = {"version": "1.0", "blender_plan": {"jobs": [{"section_id": "technical", "outputs": {"lod_high": str(high.relative_to(tmp_path)), "lod_medium": str(medium.relative_to(tmp_path))}}]}}
    variants = [
        {"lod": "high", "uri": "assets/media/technical/model/high.glb", "sha256": hashlib.sha256(high.read_bytes()).hexdigest()},
        {"lod": "medium", "uri": "assets/media/technical/model/medium.glb", "sha256": hashlib.sha256(medium.read_bytes()).hexdigest()},
    ]
    delivery = {"bindings": [{"asset_id": "model", "section_id": "technical", "media_type": "model-3d", "status": "ready", "variants": variants}]}
    summary = validate_runtime_lod_delivery(delivery, bundle, tmp_path)
    assert summary["status"] == "pass"
    assert summary["sections"] == ["technical"]
    variants[0]["sha256"] = "0" * 64
    with pytest.raises(ValueError, match="does not match"):
        validate_runtime_lod_delivery(delivery, bundle, tmp_path)

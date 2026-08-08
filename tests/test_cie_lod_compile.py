from pathlib import Path

import pytest

from ruos.cie_lod_compile import bind_validated_lods_to_media_report


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

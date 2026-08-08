import json
import struct
from pathlib import Path

import pytest

from ruos.cie_glb_validation import GLBValidationError, build_source_model_delivery, enforce_glb_authoring, inspect_glb_authoring, validate_glb_authoring, validate_registry_glb_authoring


def _glb(path: Path, payload: dict) -> Path:
    raw = json.dumps(payload, separators=(",", ":")).encode(); raw += b" " * ((4 - len(raw) % 4) % 4); total = 12 + 8 + len(raw)
    path.write_bytes(b"glTF" + struct.pack("<II", 2, total) + struct.pack("<II", len(raw), 0x4E4F534A) + raw); return path


def _plan():
    return {"sections": [{"section_id": "technical", "states": [{"state": "structure", "focus": ["structure"]}, {"state": "foundation", "focus": ["foundation"]}], "model_authoring_contract": {"preferred_variant_names": ["structure", "foundation"], "preferred_animation_names": ["cie-explode-structure", "cie-explode-foundation"]}}]}


def _full_payload():
    return {"asset": {"version": "2.0"}, "nodes": [{"name": "cie-group-structure"}, {"name": "cie-group-foundation"}, {"name": "cie-hotspot-foundation"}], "animations": [{"name": "cie-explode-structure"}, {"name": "cie-explode-foundation"}], "extensions": {"KHR_materials_variants": {"variants": [{"name": "structure"}, {"name": "foundation"}]}}}


def test_inspects_semantic_glb_contract(tmp_path):
    path = _glb(tmp_path / "model.glb", {"asset": {"version": "2.0"}, "nodes": [{"name": "cie-group-structure"}, {"name": "cie-hotspot-foundation"}], "animations": [{"name": "cie-explode-structure"}], "extensions": {"KHR_materials_variants": {"variants": [{"name": "structure"}]}}})
    report = inspect_glb_authoring(path)
    assert report["semantic_groups"] == ["structure"]; assert report["hotspot_anchors"] == ["foundation"]; assert report["variants"] == ["structure"]


def test_strict_gate_blocks_missing_authored_states(tmp_path):
    path = _glb(tmp_path / "model.glb", {"asset": {"version": "2.0"}, "nodes": [{"name": "cie-group-structure"}], "animations": [{"name": "cie-explode-structure"}], "extensions": {"KHR_materials_variants": {"variants": [{"name": "structure"}]}}})
    report = validate_glb_authoring(path, _plan(), "technical", strict=True)
    assert report["status"] == "blocked"; assert "foundation" in report["missing"]["variants"]; assert "cie-explode-foundation" in report["missing"]["animations"]
    with pytest.raises(GLBValidationError): enforce_glb_authoring(report)


def test_strict_gate_passes_fully_authored_model(tmp_path):
    path = _glb(tmp_path / "model.glb", _full_payload())
    report = validate_glb_authoring(path, _plan(), "technical", strict=True, required_hotspots={"foundation"})
    assert report["status"] == "pass"; enforce_glb_authoring(report)


def test_publish_registry_derives_model_section_and_validates_hotspots(tmp_path):
    model = _glb(tmp_path / "model.glb", _full_payload())
    registry = {"entries": [{"asset_id": "structure-model", "media_type": "model-3d", "status": "resolved", "uri": str(model), "hotspots": [{"id": "foundation"}]}]}
    media_plan = {"sections": [{"section_id": "technical", "assets": [{"asset_id": "structure-model"}]}]}
    delivery = build_source_model_delivery(registry, media_plan)
    assert delivery["bindings"][0]["section_id"] == "technical"
    report = validate_registry_glb_authoring(registry, delivery, _plan(), tmp_path, strict=True)
    assert report["status"] == "pass"; assert report["checked_models"] == 1


def test_publish_registry_blocks_missing_hotspot_anchor(tmp_path):
    payload = _full_payload(); payload["nodes"] = [{"name": "cie-group-structure"}, {"name": "cie-group-foundation"}]
    model = _glb(tmp_path / "model.glb", payload)
    registry = {"entries": [{"asset_id": "structure-model", "media_type": "model-3d", "status": "resolved", "uri": str(model), "hotspots": [{"id": "foundation"}]}]}
    delivery = {"status": "ready", "bindings": [{"asset_id": "structure-model", "section_id": "technical", "media_type": "model-3d", "status": "ready"}]}
    report = validate_registry_glb_authoring(registry, delivery, _plan(), tmp_path, strict=True)
    assert report["status"] == "blocked"; assert any("hotspot anchors" in item for item in report["failures"])


def test_source_model_delivery_uses_registry_section_for_duplicate_ids():
    registry = {"entries": [
        {"asset_id": "model", "section_id": "hero", "media_type": "model-3d", "status": "resolved"},
        {"asset_id": "model", "section_id": "technical", "media_type": "model-3d", "status": "resolved"},
    ]}
    media_plan = {"sections": [
        {"section_id": "hero", "assets": [{"asset_id": "model"}]},
        {"section_id": "technical", "assets": [{"asset_id": "model"}]},
    ]}
    delivery = build_source_model_delivery(registry, media_plan)
    assert [item["section_id"] for item in delivery["bindings"]] == ["hero", "technical"]

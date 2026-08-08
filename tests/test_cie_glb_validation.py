import json
import struct
from pathlib import Path

import pytest

from ruos.cie_glb_validation import GLBValidationError, enforce_glb_authoring, inspect_glb_authoring, validate_glb_authoring


def _glb(path: Path, payload: dict) -> Path:
    raw = json.dumps(payload, separators=(",", ":")).encode()
    raw += b" " * ((4 - len(raw) % 4) % 4)
    total = 12 + 8 + len(raw)
    path.write_bytes(b"glTF" + struct.pack("<II", 2, total) + struct.pack("<II", len(raw), 0x4E4F534A) + raw)
    return path


def _plan():
    return {"sections": [{"section_id": "technical", "states": [{"state": "structure", "focus": ["structure"]}, {"state": "foundation", "focus": ["foundation"]}], "model_authoring_contract": {"preferred_variant_names": ["structure", "foundation"], "preferred_animation_names": ["cie-explode-structure", "cie-explode-foundation"]}}]}


def test_inspects_semantic_glb_contract(tmp_path):
    path = _glb(tmp_path / "model.glb", {"asset": {"version": "2.0"}, "nodes": [{"name": "cie-group-structure"}, {"name": "cie-hotspot-foundation"}], "animations": [{"name": "cie-explode-structure"}], "extensions": {"KHR_materials_variants": {"variants": [{"name": "structure"}]}}})
    report = inspect_glb_authoring(path)
    assert report["semantic_groups"] == ["structure"]
    assert report["hotspot_anchors"] == ["foundation"]
    assert report["variants"] == ["structure"]


def test_strict_gate_blocks_missing_authored_states(tmp_path):
    path = _glb(tmp_path / "model.glb", {"asset": {"version": "2.0"}, "nodes": [{"name": "cie-group-structure"}], "animations": [{"name": "cie-explode-structure"}], "extensions": {"KHR_materials_variants": {"variants": [{"name": "structure"}]}}})
    report = validate_glb_authoring(path, _plan(), "technical", strict=True)
    assert report["status"] == "blocked"
    assert "foundation" in report["missing"]["variants"]
    assert "cie-explode-foundation" in report["missing"]["animations"]
    with pytest.raises(GLBValidationError):
        enforce_glb_authoring(report)


def test_strict_gate_passes_fully_authored_model(tmp_path):
    path = _glb(tmp_path / "model.glb", {"asset": {"version": "2.0"}, "nodes": [{"name": "cie-group-structure"}, {"name": "cie-group-foundation"}, {"name": "cie-hotspot-foundation"}], "animations": [{"name": "cie-explode-structure"}, {"name": "cie-explode-foundation"}], "extensions": {"KHR_materials_variants": {"variants": [{"name": "structure"}, {"name": "foundation"}]}}})
    report = validate_glb_authoring(path, _plan(), "technical", strict=True)
    assert report["status"] == "pass"
    enforce_glb_authoring(report)

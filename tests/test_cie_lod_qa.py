import json
import struct
from pathlib import Path

import pytest

from ruos.cie_lod_qa import LODQAGateError, enforce_post_lod_qa, validate_post_lod_outputs


def _glb(path: Path, vertices: int, bounds=(-1.0, 1.0)) -> Path:
    lo, hi = bounds
    payload = {
        "asset": {"version": "2.0"},
        "nodes": [{"name": "cie-group-structure"}, {"name": "cie-hotspot-structure"}],
        "animations": [{"name": "cie-explode-structure"}],
        "extensions": {"KHR_materials_variants": {"variants": [{"name": "structure"}]}},
        "accessors": [{"count": vertices, "type": "VEC3", "min": [lo, lo, lo], "max": [hi, hi, hi]}],
        "meshes": [{"primitives": [{"attributes": {"POSITION": 0}}]}],
    }
    raw = json.dumps(payload, separators=(",", ":")).encode()
    raw += b" " * ((4 - len(raw) % 4) % 4)
    total = 12 + 8 + len(raw)
    path.write_bytes(b"glTF" + struct.pack("<II", 2, total) + struct.pack("<II", len(raw), 0x4E4F534A) + raw)
    return path


def _plan():
    return {"sections": [{"section_id": "technical", "states": [{"state": "structure", "focus": ["structure"]}], "model_authoring_contract": {"preferred_variant_names": ["structure"], "preferred_animation_names": ["cie-explode-structure"]}}]}


def test_post_lod_gate_passes_semantic_geometry_and_visual_approval(tmp_path):
    source = _glb(tmp_path / "source.glb", 1000)
    high = _glb(tmp_path / "high.glb", 750)
    medium = _glb(tmp_path / "medium.glb", 450)
    report = validate_post_lod_outputs(source=source, high=high, medium=medium, mesh_state_plan=_plan(), section_id="technical", required_hotspots={"structure"}, visual_approval={"approved": True, "reviewer": "qa", "evidence": "renders/compare.png"})
    assert report["status"] == "pass"
    assert report["geometry"]["medium"]["bounds_drift"] == 0.0
    enforce_post_lod_qa(report)


def test_post_lod_gate_blocks_semantic_loss_and_missing_visual_review(tmp_path):
    source = _glb(tmp_path / "source.glb", 1000)
    high = _glb(tmp_path / "high.glb", 750)
    medium = _glb(tmp_path / "medium.glb", 450)
    raw = json.loads((medium.read_bytes()[20:]).rstrip(b" \t\r\n\x00").decode())
    raw["nodes"] = []
    encoded = json.dumps(raw, separators=(",", ":")).encode(); encoded += b" " * ((4 - len(encoded) % 4) % 4)
    medium.write_bytes(b"glTF" + struct.pack("<II", 2, 12 + 8 + len(encoded)) + struct.pack("<II", len(encoded), 0x4E4F534A) + encoded)
    report = validate_post_lod_outputs(source=source, high=high, medium=medium, mesh_state_plan=_plan(), section_id="technical", required_hotspots={"structure"})
    assert report["status"] == "blocked"
    assert any("semantic groups" in item or "hotspot anchors" in item for item in report["failures"])
    assert any("visual QA approval" in item for item in report["failures"])
    with pytest.raises(LODQAGateError):
        enforce_post_lod_qa(report)


def test_post_lod_gate_blocks_bounds_drift_and_fake_hierarchy(tmp_path):
    source = _glb(tmp_path / "source.glb", 1000)
    high = _glb(tmp_path / "high.glb", 950, (-1.2, 1.2))
    medium = _glb(tmp_path / "medium.glb", 980)
    report = validate_post_lod_outputs(source=source, high=high, medium=medium, mesh_state_plan=_plan(), section_id="technical", required_hotspots={"structure"}, visual_approval={"approved": True, "reviewer": "qa", "evidence": "renders/compare.png"})
    assert report["status"] == "blocked"
    assert any("vertex hierarchy" in item for item in report["failures"])
    assert any("bounds drift" in item for item in report["failures"])

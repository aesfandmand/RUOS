from pathlib import Path


def test_blender_export_uses_real_decimation_not_glb_copy():
    script = Path("scripts/cie_blender_export.py").read_text(encoding="utf-8")
    assert 'type="DECIMATE"' in script
    assert 'decimate_type = "COLLAPSE"' in script
    assert "target_path.write_bytes(glb.read_bytes())" not in script
    assert "lod_report" in script

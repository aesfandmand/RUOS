from pathlib import Path


def test_blender_visual_evidence_script_uses_fixed_camera_and_png_render():
    script = Path("scripts/cie_blender_visual_evidence.py").read_text(encoding="utf-8")
    assert 'bpy.ops.import_scene.gltf' in script
    assert 'camera_data.lens = 55' in script
    assert 'scene.render.resolution_x = 768' in script
    assert 'scene.render.image_settings.file_format = "PNG"' in script
    assert 'bpy.ops.render.render(write_still=True)' in script

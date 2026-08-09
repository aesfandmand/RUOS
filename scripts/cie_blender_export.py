from __future__ import annotations

import json
import sys
from pathlib import Path

import bpy


def _job() -> dict:
    if "--" not in sys.argv:
        raise SystemExit("Missing CIE job payload")
    return json.loads(sys.argv[sys.argv.index("--") + 1])


def _ensure_parent(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)


def _mesh_objects():
    return [obj for obj in bpy.context.scene.objects if obj.type == "MESH"]


def _triangle_count() -> int:
    total = 0
    for obj in _mesh_objects():
        mesh = obj.data
        mesh.calc_loop_triangles()
        total += len(mesh.loop_triangles)
    return total


def _export(path: Path) -> None:
    _ensure_parent(path)
    bpy.ops.export_scene.gltf(filepath=str(path), export_format="GLB", export_apply=True, export_animations=True)


def _decimate_and_export(path: Path, ratio: float) -> dict:
    ratio = max(0.05, min(1.0, float(ratio)))
    before = _triangle_count()
    modifiers = []
    for obj in _mesh_objects():
        modifier = obj.modifiers.new(name="CIE_DETERMINISTIC_LOD", type="DECIMATE")
        modifier.decimate_type = "COLLAPSE"
        modifier.ratio = ratio
        modifiers.append((obj, modifier))
    depsgraph = bpy.context.evaluated_depsgraph_get()
    depsgraph.update()
    _export(path)
    for obj, modifier in modifiers:
        obj.modifiers.remove(modifier)
    return {"ratio": ratio, "source_triangles": before, "target_triangles_estimate": int(before * ratio)}


def main() -> None:
    job = _job()
    outputs = job.get("outputs", {})
    policy = job.get("lod_policy", {}) if isinstance(job.get("lod_policy"), dict) else {}
    glb = Path(outputs["glb"])
    _export(glb)

    poster = outputs.get("poster")
    if poster:
        poster_path = Path(poster); _ensure_parent(poster_path)
        scene = bpy.context.scene
        scene.render.filepath = str(poster_path)
        scene.render.image_settings.file_format = "PNG"
        bpy.ops.render.render(write_still=True)

    reports = {}
    high = outputs.get("lod_high")
    if high:
        reports["lod_high"] = _decimate_and_export(Path(high), policy.get("high_ratio", 0.75))
    medium = outputs.get("lod_medium")
    if medium:
        reports["lod_medium"] = _decimate_and_export(Path(medium), policy.get("medium_ratio", 0.45))

    report_path = outputs.get("lod_report")
    if report_path:
        target = Path(report_path); _ensure_parent(target)
        target.write_text(json.dumps({"version": "1.0", "algorithm": "BLENDER_DECIMATE_COLLAPSE", "reports": reports}, ensure_ascii=False, indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()

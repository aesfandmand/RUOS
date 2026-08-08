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


def main() -> None:
    job = _job()
    outputs = job.get("outputs", {})
    glb = Path(outputs["glb"])
    _ensure_parent(glb)
    bpy.ops.export_scene.gltf(filepath=str(glb), export_format="GLB", export_apply=True, export_animations=True)

    # Poster and LOD production remain explicit Blender operations. The worker
    # only emits them when the job contract requests paths and the scene can render.
    poster = outputs.get("poster")
    if poster:
        poster_path = Path(poster); _ensure_parent(poster_path)
        scene = bpy.context.scene
        scene.render.filepath = str(poster_path)
        scene.render.image_settings.file_format = "PNG"
        bpy.ops.render.render(write_still=True)

    # Until deterministic decimation rules are authored per asset, preserve truth:
    # copy the validated export as LOD placeholders rather than claiming decimation.
    for key in ("lod_medium", "lod_high"):
        target = outputs.get(key)
        if target:
            target_path = Path(target); _ensure_parent(target_path)
            target_path.write_bytes(glb.read_bytes())


if __name__ == "__main__":
    main()

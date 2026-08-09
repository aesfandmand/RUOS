from __future__ import annotations

import json
import math
import sys
from pathlib import Path

import bpy
from mathutils import Vector


def _payload() -> dict:
    if "--" not in sys.argv:
        raise SystemExit("Missing CIE visual evidence payload")
    return json.loads(sys.argv[sys.argv.index("--") + 1])


def _world_bounds() -> tuple[Vector, Vector]:
    corners: list[Vector] = []
    for obj in bpy.context.scene.objects:
        if obj.type != "MESH":
            continue
        corners.extend(obj.matrix_world @ Vector(corner) for corner in obj.bound_box)
    if not corners:
        raise SystemExit("No mesh geometry available for visual evidence render")
    minimum = Vector((min(v.x for v in corners), min(v.y for v in corners), min(v.z for v in corners)))
    maximum = Vector((max(v.x for v in corners), max(v.y for v in corners), max(v.z for v in corners)))
    return minimum, maximum


def _look_at(camera, target: Vector) -> None:
    direction = target - camera.location
    camera.rotation_euler = direction.to_track_quat("-Z", "Y").to_euler()


def _setup_scene(view: dict) -> None:
    minimum, maximum = _world_bounds()
    center = (minimum + maximum) * 0.5
    diagonal = max((maximum - minimum).length, 0.01)
    azimuth = math.radians(float(view.get("azimuth", 0.0)))
    elevation = math.radians(float(view.get("elevation", 12.0)))
    distance = diagonal * float(view.get("distance_factor", 2.8))
    direction = Vector((math.cos(elevation) * math.cos(azimuth), math.cos(elevation) * math.sin(azimuth), math.sin(elevation)))

    camera_data = bpy.data.cameras.new("CIE_QA_CAMERA")
    camera = bpy.data.objects.new("CIE_QA_CAMERA", camera_data)
    bpy.context.scene.collection.objects.link(camera)
    camera.location = center + direction * distance
    camera_data.lens = 55
    _look_at(camera, center)
    bpy.context.scene.camera = camera

    key_data = bpy.data.lights.new("CIE_QA_KEY", type="AREA")
    key_data.energy = 900
    key_data.shape = "DISK"
    key_data.size = diagonal * 1.5
    key = bpy.data.objects.new("CIE_QA_KEY", key_data)
    bpy.context.scene.collection.objects.link(key)
    key.location = center + Vector((diagonal, -diagonal, diagonal * 1.6))
    _look_at(key, center)

    fill_data = bpy.data.lights.new("CIE_QA_FILL", type="AREA")
    fill_data.energy = 350
    fill_data.size = diagonal
    fill = bpy.data.objects.new("CIE_QA_FILL", fill_data)
    bpy.context.scene.collection.objects.link(fill)
    fill.location = center + Vector((-diagonal, diagonal * 0.7, diagonal * 0.8))
    _look_at(fill, center)

    world = bpy.context.scene.world or bpy.data.worlds.new("CIE_QA_WORLD")
    bpy.context.scene.world = world
    world.color = (0.035, 0.035, 0.035)


def main() -> None:
    payload = _payload()
    model = Path(payload["model"])
    output = Path(payload["output"])
    output.parent.mkdir(parents=True, exist_ok=True)

    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.gltf(filepath=str(model))
    _setup_scene(dict(payload.get("view", {})))

    scene = bpy.context.scene
    scene.render.resolution_x = 768
    scene.render.resolution_y = 768
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = "PNG"
    scene.render.film_transparent = False
    scene.render.filepath = str(output)
    bpy.ops.render.render(write_still=True)


if __name__ == "__main__":
    main()

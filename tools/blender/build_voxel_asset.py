"""Build an optimized voxel mesh, GLB export, review renders, and metrics.

Run with Blender:
  blender --background --python tools/blender/build_voxel_asset.py -- \
    --asset assets/environment/rock_demo
"""

from __future__ import annotations

import argparse
import json
import math
import sys
from pathlib import Path

import bpy
from mathutils import Vector


def script_args() -> argparse.Namespace:
    argv = sys.argv
    argv = argv[argv.index("--") + 1 :] if "--" in argv else []
    parser = argparse.ArgumentParser()
    parser.add_argument("--asset", required=True, type=Path)
    return parser.parse_args(argv)


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def clear_scene() -> None:
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete(use_global=False)
    for datablocks in (bpy.data.meshes, bpy.data.curves, bpy.data.materials, bpy.data.cameras, bpy.data.lights):
        # Materials are recreated below; removing unused datablocks keeps headless builds deterministic.
        for block in list(datablocks):
            if block.users == 0:
                datablocks.remove(block)


def parse_voxels(data: dict) -> tuple[dict[tuple[int, int, int], str], int, int, int]:
    layers = sorted(data["layers"], key=lambda item: item["y"])
    depth = len(layers[0]["rows"])
    width = len(layers[0]["rows"][0])
    height = max(layer["y"] for layer in layers) + 1

    occupied: dict[tuple[int, int, int], str] = {}
    for layer in layers:
        sy = int(layer["y"])
        for sz, row in enumerate(layer["rows"]):
            if len(row) != width:
                raise ValueError("Inconsistent row width")
            for sx, token in enumerate(row):
                if token != ".":
                    occupied[(sx, sy, sz)] = token
    return occupied, width, height, depth


def create_material(token: str, spec: dict) -> bpy.types.Material:
    mat = bpy.data.materials.new(name=spec.get("name", f"mat_{token}"))
    mat.use_nodes = True
    principled = mat.node_tree.nodes.get("Principled BSDF")
    color = spec.get("base_color", [0.5, 0.5, 0.5, 1.0])
    principled.inputs["Base Color"].default_value = tuple(float(v) for v in color)
    principled.inputs["Roughness"].default_value = float(spec.get("roughness", 0.9))
    principled.inputs["Metallic"].default_value = float(spec.get("metallic", 0.0))
    return mat


def face_vertices(cx: float, cy: float, cz: float, h: float, face: str):
    xm, xp = cx - h, cx + h
    ym, yp = cy - h, cy + h
    zm, zp = cz - h, cz + h
    return {
        "+X": [(xp, ym, zm), (xp, yp, zm), (xp, yp, zp), (xp, ym, zp)],
        "-X": [(xm, yp, zm), (xm, ym, zm), (xm, ym, zp), (xm, yp, zp)],
        "+Y": [(xp, yp, zm), (xm, yp, zm), (xm, yp, zp), (xp, yp, zp)],
        "-Y": [(xm, ym, zm), (xp, ym, zm), (xp, ym, zp), (xm, ym, zp)],
        "+Z": [(xm, ym, zp), (xp, ym, zp), (xp, yp, zp), (xm, yp, zp)],
        "-Z": [(xm, yp, zm), (xp, yp, zm), (xp, ym, zm), (xm, ym, zm)],
    }[face]


# source-neighbor -> Blender outward face.
NEIGHBORS = [
    ((1, 0, 0), "+X"),
    ((-1, 0, 0), "-X"),
    ((0, 1, 0), "+Z"),
    ((0, -1, 0), "-Z"),
    ((0, 0, 1), "-Y"),
    ((0, 0, -1), "+Y"),
]


def source_to_blender(
    sx: int, sy: int, sz: int, width: int, depth: int, voxel_size: float
) -> tuple[float, float, float]:
    # Source format is Y-up. Blender is Z-up.
    x = (sx - (width - 1) / 2.0) * voxel_size
    y = ((depth - 1) / 2.0 - sz) * voxel_size
    z = (sy + 0.5) * voxel_size
    return x, y, z


def resolve_eevee_engine() -> str:
    engine_items = {
        item.identifier
        for item in bpy.types.RenderSettings.bl_rna.properties["engine"].enum_items
    }
    if "BLENDER_EEVEE" in engine_items:
        return "BLENDER_EEVEE"
    elif "BLENDER_EEVEE_NEXT" in engine_items:
        return "BLENDER_EEVEE_NEXT"
    else:
        raise RuntimeError(
            f"No supported EEVEE engine found. Available: {sorted(engine_items)}"
        )


def build_objects(data: dict):
    occupied, width, height, depth = parse_voxels(data)
    voxel_size = float(data["voxel_size"])
    h = voxel_size / 2.0

    materials = {
        token: create_material(token, spec)
        for token, spec in data["materials"].items()
    }

    geometry = {
        token: {"verts": [], "faces": [], "visible_faces": 0}
        for token in materials
    }

    for (sx, sy, sz), token in occupied.items():
        cx, cy, cz = source_to_blender(sx, sy, sz, width, depth, voxel_size)
        target = geometry[token]

        for (dx, dy, dz), face_name in NEIGHBORS:
            neighbor = (sx + dx, sy + dy, sz + dz)
            if neighbor in occupied:
                continue

            quad = face_vertices(cx, cy, cz, h, face_name)
            base = len(target["verts"])
            target["verts"].extend(quad)
            target["faces"].append((base, base + 1, base + 2, base + 3))
            target["visible_faces"] += 1

    objects = []
    for token, geo in geometry.items():
        if not geo["faces"]:
            continue
        mesh = bpy.data.meshes.new(f"{data['name']}_{token}_mesh")
        mesh.from_pydata(geo["verts"], [], geo["faces"])
        mesh.update()
        obj = bpy.data.objects.new(f"{data['name']}_{token}", mesh)
        bpy.context.collection.objects.link(obj)
        obj.data.materials.append(materials[token])
        objects.append(obj)

    metrics = {
        "occupied_voxels": len(occupied),
        "visible_faces": sum(g["visible_faces"] for g in geometry.values()),
        "triangles": sum(g["visible_faces"] * 2 for g in geometry.values()),
        "mesh_objects": len(objects),
        "materials": len(objects),
        "grid": {"x": width, "y": height, "z": depth},
        "voxel_size": voxel_size,
        "world_size": {
            "x": width * voxel_size,
            "y": height * voxel_size,
            "z": depth * voxel_size,
        },
        "blender_version": bpy.app.version_string,
        "render_engine": resolve_eevee_engine(),
    }
    return objects, metrics


def bounds(objects):
    points = []
    for obj in objects:
        for corner in obj.bound_box:
            points.append(obj.matrix_world @ Vector(corner))
    low = Vector((min(p.x for p in points), min(p.y for p in points), min(p.z for p in points)))
    high = Vector((max(p.x for p in points), max(p.y for p in points), max(p.z for p in points)))
    return low, high


def look_at(obj: bpy.types.Object, target: Vector) -> None:
    direction = target - obj.location
    obj.rotation_euler = direction.to_track_quat("-Z", "Y").to_euler()


def setup_review_scene(objects):
    low, high = bounds(objects)
    center = (low + high) / 2.0
    extent = high - low
    max_dim = max(extent.x, extent.y, extent.z)

    world = bpy.context.scene.world
    world.color = (0.045, 0.050, 0.060)

    cam_data = bpy.data.cameras.new("ReviewCamera")
    cam = bpy.data.objects.new("ReviewCamera", cam_data)
    bpy.context.collection.objects.link(cam)
    bpy.context.scene.camera = cam
    cam.data.type = "ORTHO"
    cam.data.ortho_scale = max_dim * 1.6

    key_data = bpy.data.lights.new("Key", type="AREA")
    key_data.energy = 850.0
    key_data.shape = "DISK"
    key_data.size = max_dim * 3.0
    key_data.color = (1.0, 0.98, 0.94)
    key = bpy.data.objects.new("Key", key_data)
    bpy.context.collection.objects.link(key)
    key.location = center + Vector((-max_dim * 2.2, -max_dim * 2.2, max_dim * 3.2))
    look_at(key, center)

    fill_data = bpy.data.lights.new("Fill", type="AREA")
    fill_data.energy = 380.0
    fill_data.shape = "DISK"
    fill_data.size = max_dim * 2.5
    fill_data.color = (0.85, 0.90, 1.0)
    fill = bpy.data.objects.new("Fill", fill_data)
    bpy.context.collection.objects.link(fill)
    fill.location = center + Vector((max_dim * 2.2, max_dim * 1.8, max_dim * 1.8))
    look_at(fill, center)

    rim_data = bpy.data.lights.new("Rim", type="AREA")
    rim_data.energy = 220.0
    rim_data.shape = "DISK"
    rim_data.size = max_dim * 2.0
    rim_data.color = (0.95, 0.95, 1.0)
    rim = bpy.data.objects.new("Rim", rim_data)
    bpy.context.collection.objects.link(rim)
    rim.location = center + Vector((max_dim * 1.0, max_dim * 3.0, max_dim * 2.5))
    look_at(rim, center)

    scene = bpy.context.scene
    scene.render.engine = resolve_eevee_engine()
    scene.render.resolution_x = 640
    scene.render.resolution_y = 640
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = "PNG"
    scene.render.film_transparent = False

    return cam, center, max_dim


def render_views(review_dir: Path, objects) -> None:
    review_dir.mkdir(parents=True, exist_ok=True)
    cam, center, d = setup_review_scene(objects)

    views = {
        "front": center + Vector((0.0, -d * 3.0, d * 0.15)),
        "side": center + Vector((d * 3.0, 0.0, d * 0.15)),
        "top": center + Vector((0.0, 0.0, d * 4.0)),
        "iso": center + Vector((d * 2.6, -d * 2.6, d * 2.2)),
    }

    for name, position in views.items():
        cam.location = position
        look_at(cam, center)
        bpy.context.scene.render.filepath = str((review_dir / f"{name}.png").resolve())
        bpy.ops.render.render(write_still=True)


def export_glb(output_path: Path, objects) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    bpy.ops.object.select_all(action="DESELECT")
    for obj in objects:
        obj.select_set(True)
    bpy.context.view_layer.objects.active = objects[0]

    bpy.ops.export_scene.gltf(
        filepath=str(output_path.resolve()),
        export_format="GLB",
        use_selection=True,
        export_yup=True,
        export_materials="EXPORT",
        export_animations=False,
        export_cameras=False,
        export_lights=False,
    )


def main() -> None:
    args = script_args()
    asset_dir = args.asset.resolve()
    manifest = load_json(asset_dir / "manifest.json")
    source_path = asset_dir / manifest["source"]
    data = load_json(source_path)

    clear_scene()
    objects, metrics = build_objects(data)

    if not objects:
        raise RuntimeError("No mesh objects were generated")

    output_path = asset_dir / manifest.get("outputs", {}).get("model", "output/model.glb")
    export_glb(output_path, objects)
    render_views(asset_dir / "review", objects)

    metrics_path = asset_dir / "review" / "metrics.json"
    metrics_path.write_text(
        json.dumps(metrics, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )

    print(json.dumps(metrics, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()

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

import bmesh
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

    # 1. Build unified watertight mesh
    mesh = bpy.data.meshes.new(f"{data['name']}_raw_mesh")
    bm = bmesh.new()

    for (sx, sy, sz), token in occupied.items():
        cx, cy, cz = source_to_blender(sx, sy, sz, width, depth, voxel_size)
        for (dx, dy, dz), face_name in NEIGHBORS:
            neighbor = (sx + dx, sy + dy, sz + dz)
            if neighbor in occupied:
                continue
            quad_coords = face_vertices(cx, cy, cz, h, face_name)
            verts = [bm.verts.new(coord) for coord in quad_coords]
            bm.faces.new(verts)

    bm.verts.ensure_lookup_table()
    bm.faces.ensure_lookup_table()

    # Weld duplicate vertices so we have continuous manifold geometry
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=0.001)
    bm.verts.ensure_lookup_table()
    bm.edges.ensure_lookup_table()
    bm.faces.ensure_lookup_table()

    # Dissolve coplanar faces to form clean planar facets before beveling
    bmesh.ops.dissolve_limit(bm, angle_limit=math.radians(2.0), verts=bm.verts, edges=bm.edges)
    bm.verts.ensure_lookup_table()
    bm.edges.ensure_lookup_table()
    bm.faces.ensure_lookup_table()

    # 2. Identify strictly convex sharp edges to bevel into stylized facets
    convex_edges = []
    for e in bm.edges:
        if len(e.link_faces) == 2 and not e.is_boundary:
            # Preserve flat ground contact: do not bevel bottom edges resting at z=0
            if abs(e.verts[0].co.z) <= 0.001 and abs(e.verts[1].co.z) <= 0.001:
                continue

            f1, f2 = e.link_faces
            angle = f1.normal.angle(f2.normal)
            if angle > math.radians(45):
                # Check convexity: midpoint of face centers vs edge midpoint
                edge_mid = (e.verts[0].co + e.verts[1].co) * 0.5
                face_mid = (f1.calc_center_bounds() + f2.calc_center_bounds()) * 0.5
                avg_normal = f1.normal + f2.normal
                # In a convex corner, face_mid is inside the solid volume
                if (face_mid - edge_mid).dot(avg_normal) < 0:
                    convex_edges.append(e)

    # Apply bevel with 1 segment (chamfer)
    bevel_width = voxel_size * 0.26  # ~0.039m for 0.15m voxels
    if convex_edges:
        bmesh.ops.bevel(
            bm,
            geom=convex_edges,
            offset=bevel_width,
            offset_type="OFFSET",
            segments=1,
            profile=0.5,
            affect="EDGES",
            clamp_overlap=True,
        )

    bm.to_mesh(mesh)
    bm.free()

    raw_obj = bpy.data.objects.new(f"{data['name']}_base", mesh)
    bpy.context.collection.objects.link(raw_obj)

    # Attach all available materials in consistent token order
    mat_token_by_name = {spec.get("name", f"mat_{tok}"): tok for tok, spec in data["materials"].items()}
    token_to_idx = {}
    for tok in ["S", "D", "L", "M"]:
        if tok in materials:
            token_to_idx[tok] = len(raw_obj.data.materials)
            raw_obj.data.materials.append(materials[tok])

    # 3. Surface-oriented material assignment based on surface normals and voxel roles
    moss_voxels = {pos for pos, tok in occupied.items() if tok == "M"}
    dark_voxels = {pos for pos, tok in occupied.items() if tok == "D"}
    light_voxels = {pos for pos, tok in occupied.items() if tok == "L"}

    for poly in mesh.polygons:
        nz = poly.normal.z
        center = poly.center

        # Approximate source voxel coordinate from face center
        sx = int(round(center.x / voxel_size + (width - 1) / 2.0))
        sz = int(round((depth - 1) / 2.0 - center.y / voxel_size))
        sy = int(round(center.z / voxel_size - 0.5))
        voxel_pos = (sx, sy, sz)

        # Check if polygon is on a moss shelf (upward facing and near an M-marked voxel)
        is_near_moss = any(
            (sx + dx, sy + dy, sz + dz) in moss_voxels
            for dx in (-1, 0, 1) for dy in (-1, 0, 1) for dz in (-1, 0, 1)
        )

        if "M" in token_to_idx and is_near_moss and nz > 0.45:
            poly.material_index = token_to_idx["M"]
        elif "D" in token_to_idx and nz < -0.6:
            # Undercuts pointing downward
            poly.material_index = token_to_idx["D"]
        elif "D" in token_to_idx and voxel_pos in dark_voxels and nz < 0.3:
            # Deep crevices and cavities
            poly.material_index = token_to_idx["D"]
        elif "L" in token_to_idx and nz > 0.6:
            # Sunlit horizontal surfaces, summit plateaus, and terraces
            poly.material_index = token_to_idx["L"]
        elif "L" in token_to_idx and nz > 0.35 and (voxel_pos in light_voxels or center.z > (height * 0.65 * voxel_size)):
            # Upper sunlit chamfers and peaks
            poly.material_index = token_to_idx["L"]
        else:
            # Main rock vertical and side walls
            poly.material_index = token_to_idx.get("S", 0)

    # 4. Separate mesh by material into one mesh object per material
    bpy.ops.object.select_all(action="DESELECT")
    bpy.context.view_layer.objects.active = raw_obj
    raw_obj.select_set(True)
    bpy.ops.mesh.separate(type="MATERIAL")

    separated = list(bpy.context.selected_objects)
    bpy.ops.object.select_all(action="DESELECT")
    objects = []


    for obj in separated:
        # Determine the primary material used by this object
        used_mat_indices = {p.material_index for p in obj.data.polygons if p.material_index < len(obj.data.materials)}
        if not used_mat_indices:
            # Unused empty split object
            bpy.data.objects.remove(obj, do_unlink=True)
            continue

        active_mat_idx = list(used_mat_indices)[0]
        active_mat = obj.data.materials[active_mat_idx]
        mat_name = active_mat.name
        tok = mat_token_by_name.get(mat_name, "S")

        obj.name = f"{data['name']}_{tok}"
        obj.data.name = f"{data['name']}_{tok}_mesh"

        # Clean material slots so this object only has its own active material
        obj.data.materials.clear()
        obj.data.materials.append(active_mat)
        for p in obj.data.polygons:
            p.material_index = 0

        objects.append(obj)

    # Sort objects deterministically: S, D, L, M
    token_sort = {"S": 0, "D": 1, "L": 2, "M": 3}
    objects.sort(key=lambda o: token_sort.get(o.name.split("_")[-1], 99))

    total_polys = sum(len(o.data.polygons) for o in objects)
    total_tris = sum(len(p.vertices) - 2 for o in objects for p in o.data.polygons)

    metrics = {
        "occupied_voxels": len(occupied),
        "visible_faces": total_polys,
        "triangles": total_tris,
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
    cam.data.ortho_scale = max_dim * 1.55

    # Directional SUN lights for crisp stylized facet highlights and shadows
    key_data = bpy.data.lights.new("Key", type="SUN")
    key_data.energy = 4.2
    key_data.color = (1.0, 0.98, 0.94)
    key = bpy.data.objects.new("Key", key_data)
    bpy.context.collection.objects.link(key)
    key.location = center + Vector((-max_dim * 2.0, -max_dim * 2.5, max_dim * 3.5))
    look_at(key, center)

    fill_data = bpy.data.lights.new("Fill", type="SUN")
    fill_data.energy = 1.8
    fill_data.color = (0.85, 0.90, 1.0)
    fill = bpy.data.objects.new("Fill", fill_data)
    bpy.context.collection.objects.link(fill)
    fill.location = center + Vector((max_dim * 2.5, max_dim * 1.5, max_dim * 2.0))
    look_at(fill, center)

    rim_data = bpy.data.lights.new("Rim", type="SUN")
    rim_data.energy = 1.0
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

"""render_tree_mockup.py - Render gameplay scale mockup with 2m character guide for Standard Oak.

Run with Blender:
  blender --background --factory-startup --python tools/blender/render_tree_mockup.py -- \
    --asset assets/environment/tree_oak/var_0_standard_oak
"""

from __future__ import annotations

import argparse
import json
import math
import sys
from pathlib import Path

import bpy
from mathutils import Vector

REPO_ROOT = Path(__file__).resolve().parent.parent.parent


def script_args() -> argparse.Namespace:
    argv = sys.argv
    argv = argv[argv.index("--") + 1 :] if "--" in argv else []
    parser = argparse.ArgumentParser()
    parser.add_argument("--asset", required=True, type=Path)
    return parser.parse_args(argv)


def clear_scene() -> None:
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete(use_global=False)
    for datablocks in (bpy.data.meshes, bpy.data.curves, bpy.data.materials, bpy.data.cameras, bpy.data.lights):
        for block in list(datablocks):
            if block.users == 0:
                datablocks.remove(block)


def look_at(obj: bpy.types.Object, target: Vector) -> None:
    direction = target - obj.location
    obj.rotation_euler = direction.to_track_quat("-Z", "Y").to_euler()


def resolve_eevee_engine() -> str:
    enum_items = {
        item.identifier
        for item in bpy.types.RenderSettings.bl_rna.properties["engine"].enum_items
    }
    if "BLENDER_EEVEE" in enum_items:
        return "BLENDER_EEVEE"
    elif "BLENDER_EEVEE_NEXT" in enum_items:
        return "BLENDER_EEVEE_NEXT"
    raise RuntimeError(f"No EEVEE engine available: {sorted(enum_items)}")


def render_mockup(asset_dir: Path) -> Path:
    clear_scene()

    glb_path = asset_dir / "output" / "model.glb"
    if not glb_path.exists():
        raise FileNotFoundError(f"Missing GLB model: {glb_path}")

    # Import exported tree GLB
    bpy.ops.import_scene.gltf(filepath=str(glb_path.resolve()))
    tree_objects = [o for o in bpy.context.selected_objects if o.type == "MESH"]
    if not tree_objects:
        raise RuntimeError("No mesh objects imported from tree GLB")

    # Center tree at origin (0, 0, 0)
    for o in tree_objects:
        o.location = Vector((0.0, 0.0, 0.0))

    # 1. Stylized Grassy Ground Base
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=(0.0, 0.0, -0.15))
    ground = bpy.context.active_object
    ground.scale = (11.0, 11.0, 0.3)
    mat_ground = bpy.data.materials.new(name="terrain_grass_base")
    mat_ground.use_nodes = True
    mat_ground.node_tree.nodes["Principled BSDF"].inputs["Base Color"].default_value = (0.045, 0.150, 0.020, 1.0)
    mat_ground.node_tree.nodes["Principled BSDF"].inputs["Roughness"].default_value = 0.90
    ground.data.materials.append(mat_ground)

    # 2. Stylized 2.0m Humanoid Warrior Scale Mannequin
    # Placed next to the tree at (-1.5, -0.6, 0.0)
    char_x = -1.65
    char_y = -0.75

    mat_mannequin = bpy.data.materials.new(name="warrior_scale_guide")
    mat_mannequin.use_nodes = True
    mat_mannequin.node_tree.nodes["Principled BSDF"].inputs["Base Color"].default_value = (0.78, 0.38, 0.14, 1.0)
    mat_mannequin.node_tree.nodes["Principled BSDF"].inputs["Roughness"].default_value = 0.75

    # Legs (z=0..0.85m)
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=(char_x, char_y, 0.425))
    legs = bpy.context.active_object
    legs.scale = (0.38, 0.26, 0.85)
    legs.data.materials.append(mat_mannequin)

    # Torso (z=0.85..1.60m)
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=(char_x, char_y, 1.225))
    torso = bpy.context.active_object
    torso.scale = (0.52, 0.32, 0.75)
    torso.data.materials.append(mat_mannequin)

    # Head (z=1.60..2.00m, top exactly at 2.00m)
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=(char_x, char_y, 1.80))
    head = bpy.context.active_object
    head.scale = (0.34, 0.34, 0.40)
    head.data.materials.append(mat_mannequin)

    # 3. Precision 2.0m Height Scale Ruler
    # Alternating 0.5m bands up to 2.0m
    mat_white = bpy.data.materials.new(name="ruler_white")
    mat_white.use_nodes = True
    mat_white.node_tree.nodes["Principled BSDF"].inputs["Base Color"].default_value = (0.9, 0.9, 0.9, 1.0)

    mat_dark = bpy.data.materials.new(name="ruler_dark")
    mat_dark.use_nodes = True
    mat_dark.node_tree.nodes["Principled BSDF"].inputs["Base Color"].default_value = (0.1, 0.1, 0.1, 1.0)

    ruler_x = char_x - 0.45
    ruler_y = char_y
    for band_idx in range(4):
        z_start = band_idx * 0.5
        z_mid = z_start + 0.25
        bpy.ops.mesh.primitive_cube_add(size=1.0, location=(ruler_x, ruler_y, z_mid))
        band = bpy.context.active_object
        band.scale = (0.08, 0.08, 0.50)
        band.data.materials.append(mat_white if band_idx % 2 == 0 else mat_dark)

    # 4. Lighting & Environment
    world = bpy.context.scene.world
    if not world:
        world = bpy.data.worlds.new("World")
        bpy.context.scene.world = world
    world.color = (0.045, 0.050, 0.060)

    target_center = Vector((0.0, 0.0, 2.1))

    # Sun key
    key_data = bpy.data.lights.new("SunKey", type="SUN")
    key_data.energy = 4.0
    key_data.color = (1.0, 0.97, 0.92)
    key = bpy.data.objects.new("SunKey", key_data)
    bpy.context.collection.objects.link(key)
    key.location = target_center + Vector((-8.0, -10.0, 12.0))
    look_at(key, target_center)

    # Fill
    fill_data = bpy.data.lights.new("SunFill", type="SUN")
    fill_data.energy = 1.6
    fill_data.color = (0.82, 0.88, 1.0)
    fill = bpy.data.objects.new("SunFill", fill_data)
    bpy.context.collection.objects.link(fill)
    fill.location = target_center + Vector((10.0, 6.0, 8.0))
    look_at(fill, target_center)

    # Rim
    rim_data = bpy.data.lights.new("SunRim", type="SUN")
    rim_data.energy = 1.2
    rim_data.color = (0.95, 0.95, 1.0)
    rim = bpy.data.objects.new("SunRim", rim_data)
    bpy.context.collection.objects.link(rim)
    rim.location = target_center + Vector((4.0, 10.0, 9.0))
    look_at(rim, target_center)

    # 5. Camera (In-game Isometric View)
    cam_data = bpy.data.cameras.new("MockupCamera")
    cam = bpy.data.objects.new("MockupCamera", cam_data)
    bpy.context.collection.objects.link(cam)
    bpy.context.scene.camera = cam
    cam.data.type = "ORTHO"
    cam.data.ortho_scale = 8.6

    cam_dist = 14.0
    cam.location = target_center + Vector((cam_dist * 0.72, -cam_dist * 0.72, cam_dist * 0.58))
    look_at(cam, target_center)

    scene = bpy.context.scene
    scene.render.engine = resolve_eevee_engine()
    scene.render.resolution_x = 1280
    scene.render.resolution_y = 720
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = "PNG"

    output_path = asset_dir / "review" / "gameplay_mockup.png"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    scene.render.filepath = str(output_path.resolve())
    bpy.ops.render.render(write_still=True)
    print(f"[OK] Rendered base mockup to {output_path}")
    return output_path


def main() -> None:
    args = script_args()
    asset_dir = args.asset.resolve()
    render_mockup(asset_dir)


if __name__ == "__main__":
    main()

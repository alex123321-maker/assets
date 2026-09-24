"""Build family lineup review renders for Cube Siege enemies.
Loads exported runtime GLBs for:
  - Hero Proxy (standard player scale reference: 1.8m height)
  - Zombie (standard melee undead)
  - Ranged Skirmisher (undead skeleton archer with bow)
  - Siege Breaker (massive undead siege brute)

Generates:
  1. Front orthographic scale chart with height tick marks (1m, 2m, 3m)
  2. Isometric 3D presentation
  3. Pure silhouette test (black silhouettes on white ground/sky)
  4. In-game camera perspective (Godot 4.6 camera profile: FOV 45, pitch 35 deg)
"""

from __future__ import annotations
import math
import os
import sys
from pathlib import Path

import bpy
import bmesh
from mathutils import Vector, Euler

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.append(str(Path(__file__).resolve().parent))
import character_builder_core as core

OUT_DIR = REPO_ROOT / "assets" / "characters" / "references"


def create_hero_proxy(loc_x: float):
    # Blueish proxy material
    mat_hero = core.create_pbr_material("mat_hero_proxy", "#3b6998", roughness=0.6)
    mat_skin = core.create_pbr_material("mat_hero_skin", "#e2b896", roughness=0.7)
    mat_metal = core.create_pbr_material("mat_hero_metal", "#7c858c", roughness=0.3, metallic=0.8)

    bm = bmesh.new()
    weights = {}

    # Torso (Z=0.9 to 1.4)
    core.add_box_geometry(bm, (loc_x, 0, 1.15), (0.50, 0.28, 0.50), "Root", weights, mat_index=0)
    # Head (Z=1.45 to 1.75)
    core.add_box_geometry(bm, (loc_x, 0, 1.60), (0.32, 0.32, 0.32), "Root", weights, mat_index=1)
    # Visor / Helmet front
    core.add_box_geometry(bm, (loc_x, -0.16, 1.62), (0.34, 0.04, 0.12), "Root", weights, mat_index=2)
    # Legs (Z=0 to 0.9)
    core.add_box_geometry(bm, (loc_x - 0.14, 0, 0.45), (0.18, 0.20, 0.90), "Root", weights, mat_index=0)
    core.add_box_geometry(bm, (loc_x + 0.14, 0, 0.45), (0.18, 0.20, 0.90), "Root", weights, mat_index=0)
    # Arms
    core.add_box_geometry(bm, (loc_x + 0.35, 0, 1.15), (0.14, 0.16, 0.50), "Root", weights, mat_index=0)
    core.add_box_geometry(bm, (loc_x - 0.35, -0.10, 1.25), (0.14, 0.16, 0.45), "Root", weights, mat_index=0, rot=(-30, 0, 0))
    # Sword proxy in right hand (held forward at -Y)
    core.add_box_geometry(bm, (loc_x - 0.35, -0.32, 1.35), (0.06, 0.12, 0.85), "Root", weights, mat_index=2, rot=(-30, 0, 0))

    me = bpy.data.meshes.new("HeroProxy_Mesh")
    bm.to_mesh(me)
    bm.free()

    me.materials.append(mat_hero)
    me.materials.append(mat_skin)
    me.materials.append(mat_metal)

    obj = bpy.data.objects.new("HeroProxy", me)
    bpy.context.collection.objects.link(obj)
    return obj


def create_height_markers():
    mat_guide = core.create_pbr_material("mat_guide", "#808080", roughness=0.9)
    mat_marker = core.create_pbr_material("mat_marker", "#c0392b", roughness=0.9)

    bm = bmesh.new()
    weights = {}
    # Horizontal line at 1.0m, 2.0m, 2.5m
    for z in [1.0, 2.0, 2.5]:
        core.add_box_geometry(bm, (0, -0.6, z), (10.0, 0.02, 0.02), "Root", weights, mat_index=0)
        # Left and right vertical poles
        core.add_box_geometry(bm, (-4.8, -0.6, z), (0.08, 0.04, 0.04), "Root", weights, mat_index=1)
        core.add_box_geometry(bm, (4.8, -0.6, z), (0.08, 0.04, 0.04), "Root", weights, mat_index=1)

    # Poles
    core.add_box_geometry(bm, (-4.8, -0.6, 1.5), (0.04, 0.04, 3.0), "Root", weights, mat_index=0)
    core.add_box_geometry(bm, (4.8, -0.6, 1.5), (0.04, 0.04, 3.0), "Root", weights, mat_index=0)

    me = bpy.data.meshes.new("HeightGuides_Mesh")
    bm.to_mesh(me)
    bm.free()
    me.materials.append(mat_guide)
    me.materials.append(mat_marker)

    obj = bpy.data.objects.new("HeightGuides", me)
    bpy.context.collection.objects.link(obj)
    return obj


def main():
    core.clear_scene()
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    # Ground plane
    mat_ground = core.create_pbr_material("mat_ground", "#33383e", roughness=0.9)
    bpy.ops.mesh.primitive_plane_add(size=30, location=(0, 0, 0))
    ground = bpy.context.active_object
    ground.name = "Ground"
    ground.data.materials.append(mat_ground)

    # Create Hero proxy at X = -3.0
    create_hero_proxy(-3.0)

    # Import Zombie GLB at X = -1.0
    zombie_glb = REPO_ROOT / "assets" / "characters" / "zombie" / "output" / "model.glb"
    bpy.ops.import_scene.gltf(filepath=str(zombie_glb))
    zombie_objs = [o for o in bpy.context.selected_objects]
    for o in zombie_objs:
        if o.parent is None:
            o.location = Vector((-1.0, 0, 0))

    # Import Ranged Skirmisher GLB at X = 1.0
    skirmisher_glb = REPO_ROOT / "assets" / "characters" / "ranged_skirmisher" / "output" / "model.glb"
    bpy.ops.import_scene.gltf(filepath=str(skirmisher_glb))
    skirmisher_objs = [o for o in bpy.context.selected_objects]
    for o in skirmisher_objs:
        if o.parent is None:
            o.location = Vector((1.0, 0, 0))

    # Import Siege Breaker GLB at X = 3.6
    siege_glb = REPO_ROOT / "assets" / "characters" / "siege_breaker" / "output" / "model.glb"
    bpy.ops.import_scene.gltf(filepath=str(siege_glb))
    siege_objs = [o for o in bpy.context.selected_objects]
    for o in siege_objs:
        if o.parent is None:
            o.location = Vector((3.6, 0, 0))

    guides = create_height_markers()

    # Lighting
    core.setup_lights()

    # Set up rendering
    scene = bpy.context.scene
    scene.render.engine = core.get_eevee_engine()
    scene.render.resolution_x = 1920
    scene.render.resolution_y = 1080
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = "PNG"
    scene.render.image_settings.color_mode = "RGBA"

    cam_data = bpy.data.cameras.new("FamilyCam")
    cam_obj = bpy.data.objects.new("FamilyCam", cam_data)
    bpy.context.collection.objects.link(cam_obj)
    scene.camera = cam_obj

    # 1. Front Orthographic Scale Chart
    guides.hide_render = False
    cam_data.type = "ORTHO"
    cam_data.ortho_scale = 10.5
    cam_obj.location = (0.3, -12, 1.4)
    cam_obj.rotation_euler = (math.radians(90), 0, 0)
    scene.render.filepath = str(OUT_DIR / "family_lineup_front.png")
    bpy.ops.render.render(write_still=True)
    print("Rendered family_lineup_front.png")

    # 2. Isometric 3D Presentation
    guides.hide_render = True
    cam_data.type = "PERSP"
    cam_data.lens = 65
    cam_obj.location = (0.5, -11.0, 6.5)
    cam_obj.rotation_euler = (math.radians(62), 0, 0)
    scene.render.filepath = str(OUT_DIR / "family_lineup_iso.png")
    bpy.ops.render.render(write_still=True)
    print("Rendered family_lineup_iso.png")

    # 3. In-Game Gameplay Camera (Godot 4.6 profile: pitch 35 deg, FOV 45, viewing angle)
    cam_data.lens_unit = "FOV"
    cam_data.angle = math.radians(45)
    cam_obj.location = (0.5, -12.0, 8.4)
    cam_obj.rotation_euler = (math.radians(55), 0, 0)
    scene.render.filepath = str(OUT_DIR / "family_lineup_gameplay.png")
    bpy.ops.render.render(write_still=True)
    print("Rendered family_lineup_gameplay.png")

    # 3b. Night Gameplay Lineup (Cool moonlight + low ambient - LIGHT-01)
    sun_obj = bpy.data.objects.get("Sun")
    fill_obj = bpy.data.objects.get("Fill")
    orig_sun_energy = sun_obj.data.energy
    orig_sun_color = tuple(sun_obj.data.color)
    orig_fill_energy = fill_obj.data.energy
    orig_fill_color = tuple(fill_obj.data.color)

    sun_obj.data.energy = 1.4
    sun_obj.data.color = (0.45, 0.65, 1.0)
    fill_obj.data.energy = 0.5
    fill_obj.data.color = (0.2, 0.35, 0.65)

    scene.render.filepath = str(OUT_DIR / "family_lineup_gameplay_night.png")
    bpy.ops.render.render(write_still=True)
    print("Rendered family_lineup_gameplay_night.png")

    sun_obj.data.energy = orig_sun_energy
    sun_obj.data.color = orig_sun_color
    fill_obj.data.energy = orig_fill_energy
    fill_obj.data.color = orig_fill_color

    # 4. Pure Silhouette Test (Black silhouettes on white background)
    guides.hide_render = True
    ground.hide_render = True
    # Pure white world
    world = bpy.data.worlds.new("WhiteWorld")
    world.use_nodes = True
    bg_node = world.node_tree.nodes.get("Background")
    bg_node.inputs["Color"].default_value = (1.0, 1.0, 1.0, 1.0)
    bg_node.inputs["Strength"].default_value = 1.0
    scene.world = world

    # Override all character materials with pure black unlit emission
    black_mat = bpy.data.materials.new("BlackMat")
    black_mat.use_nodes = True
    b_nodes = black_mat.node_tree.nodes
    b_nodes.clear()
    emit = b_nodes.new("ShaderNodeEmission")
    emit.inputs["Color"].default_value = (0.0, 0.0, 0.0, 1.0)
    emit.inputs["Strength"].default_value = 1.0
    out = b_nodes.new("ShaderNodeOutputMaterial")
    black_mat.node_tree.links.new(emit.outputs["Emission"], out.inputs["Surface"])

    for obj in bpy.data.objects:
        if obj.type == "MESH" and obj != ground and obj != guides:
            obj.data.materials.clear()
            obj.data.materials.append(black_mat)

    cam_data.type = "ORTHO"
    cam_data.ortho_scale = 10.5
    cam_obj.location = (0.3, -12, 1.4)
    cam_obj.rotation_euler = (math.radians(90), 0, 0)
    scene.render.filepath = str(OUT_DIR / "family_lineup_silhouette.png")
    bpy.ops.render.render(write_still=True)
    print("Rendered family_lineup_silhouette.png")


if __name__ == "__main__":
    main()

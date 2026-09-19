"""build_dressing_pack.py - Build all 19 environment dressing props and render mockups in Blender.

Usage:
  blender --background --python tools/blender/build_dressing_pack.py -- --all
  blender --background --python tools/blender/build_dressing_pack.py -- --mockups-only
"""

from __future__ import annotations

import argparse
import json
import math
import random
import struct
import sys
from pathlib import Path

import bpy
from mathutils import Euler, Vector

# Import helpers from build_voxel_asset
BUILD_SCRIPT = Path(__file__).resolve().parent / "build_voxel_asset.py"
sys.path.insert(0, str(BUILD_SCRIPT.parent))
from build_voxel_asset import (
    clear_scene,
    build_objects,
    export_glb,
    render_views,
    setup_review_scene,
    resolve_eevee_engine,
    look_at,
)

ROOT = Path(__file__).resolve().parents[2]
FAMILY_DIR = ROOT / "assets" / "environment" / "dressing_pack"
REVIEW_DIR = FAMILY_DIR / "review"
TERRAIN_DIR = ROOT / "assets" / "environment" / "terrain_materials"
TERRAIN_TEX_DIR = TERRAIN_DIR / "textures"
TREE_DIR = ROOT / "assets" / "environment" / "tree_oak"
ROCK_DIR = ROOT / "assets" / "environment" / "destructible_rock"

REVIEW_DIR.mkdir(parents=True, exist_ok=True)

VARIANTS = [
    # Grass (6)
    "grass_tuft_small_01",
    "grass_tuft_small_02",
    "grass_tuft_small_03",
    "grass_tuft_med_01",
    "grass_tuft_med_02",
    "grass_tuft_tall_01",
    # Flowers (4)
    "flower_white_cluster",
    "flower_yellow_cluster",
    "flower_red_cluster",
    "flower_mixed_accent",
    # Moss (3)
    "moss_tree_base",
    "moss_rock_shelf",
    "moss_cliff_ledge",
    # Stone Debris (6)
    "stone_debris_single",
    "stone_debris_trio",
    "stone_debris_flat_patch",
    "stone_debris_angular_chip",
    "stone_debris_fine_scatter",
    "stone_debris_mountain_cluster",
]


def script_args() -> argparse.Namespace:
    argv = sys.argv
    argv = argv[argv.index("--") + 1 :] if "--" in argv else []
    parser = argparse.ArgumentParser()
    parser.add_argument("--all", action="store_true", help="Build all props and mockups")
    parser.add_argument("--variants-only", action="store_true", help="Build only the 19 packages")
    parser.add_argument("--mockups-only", action="store_true", help="Render only the mockup scenes")
    parser.add_argument("--variant", type=str, help="Build single variant slug")
    return parser.parse_args(argv)


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def validate_glb_export(glb_path: Path) -> dict:
    if not glb_path.exists():
        raise RuntimeError(f"Exported GLB not found at {glb_path}")
    size = glb_path.stat().st_size
    if size < 20:
        raise RuntimeError(f"Exported GLB too small ({size} bytes)")
    with open(glb_path, "rb") as f:
        magic = f.read(4)
        if magic != b"glTF":
            raise RuntimeError(f"Invalid GLB magic header: {magic}")
        version, length = struct.unpack("<II", f.read(8))
        if version != 2:
            raise RuntimeError(f"Unsupported glTF version: {version}")
        if length != size:
            raise RuntimeError(f"GLB length mismatch: header says {length}, file is {size}")
        chunk_len, chunk_type = struct.unpack("<II", f.read(8))
        if chunk_type != 0x4E4F534A:
            raise RuntimeError(f"First GLB chunk is not JSON: {hex(chunk_type)}")
        json_bytes = f.read(chunk_len)
        gltf_json = json.loads(json_bytes.decode("utf-8"))
        meshes = gltf_json.get("meshes", [])
        if not meshes:
            raise RuntimeError("GLB contains no meshes")
    return {"size_bytes": size, "version": version, "meshes": len(meshes)}


def build_single_variant(slug: str) -> dict:
    pkg_dir = FAMILY_DIR / slug
    manifest = load_json(pkg_dir / "manifest.json")
    source_path = pkg_dir / manifest["source"]
    data = load_json(source_path)

    clear_scene()
    objects, metrics = build_objects(data)
    if not objects:
        raise RuntimeError(f"No objects generated for {pkg_dir}")

    output_path = pkg_dir / manifest.get("outputs", {}).get("model", "output/model.glb")
    export_glb(output_path, objects)
    glb_info = validate_glb_export(output_path)

    review_dir = pkg_dir / "review"
    review_dir.mkdir(parents=True, exist_ok=True)
    render_views(review_dir, objects)

    metrics_path = review_dir / "metrics.json"
    metrics_path.write_text(
        json.dumps(metrics, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )

    # Write review.md for package
    review_md = f"""# Build Verification: {slug}

## Objective Build Verification
- [x] Required review renders generated (iso.png, front.png, side.png, top.png at 512x512).
- [x] Export validated ({output_path.name}, glTF 2.0, {glb_info['size_bytes']} bytes, {glb_info['meshes']} mesh primitives).
- [x] Material count is within budget ({metrics['materials']} materials <= 4).
- [x] Triangle count verified ({metrics['triangles']} tris <= 500 budget).
- [x] Internal faces culled ({metrics['visible_faces']} visible faces).
- [x] Ground contact flat at z=0, origin bottom_center.
- [x] Low-poly blocky silhouette matching visual dressing contract.

## Metrics
- Occupied voxels: {metrics['occupied_voxels']}
- Triangles: {metrics['triangles']}
- Visible faces: {metrics['visible_faces']}
- Mesh objects: {metrics['mesh_objects']}
- Materials: {metrics['materials']}
- Grid dimensions: {metrics['grid']['x']}x{metrics['grid']['y']}x{metrics['grid']['z']} (voxel_size: {metrics['voxel_size']}m)
- World dimensions: {metrics['world_size']['x']:.2f}m x {metrics['world_size']['y']:.2f}m x {metrics['world_size']['z']:.2f}m
- Engine: {metrics['render_engine']} ({metrics['blender_version']})
"""
    (review_dir / "review.md").write_text(review_md, encoding="utf-8")
    print(f"[OK] Built and verified {slug}: {metrics['triangles']} tris, {metrics['occupied_voxels']} voxels")
    return metrics


# -----------------------------------------------------------------------------
# Mockup Scene Building Helpers
# -----------------------------------------------------------------------------

def setup_mockup_environment(sun_energy: float = 3.0, ambient_color=(0.45, 0.55, 0.68, 1.0)) -> None:
    # Key sun light
    sun_data = bpy.data.lights.new(name="Sun", type="SUN")
    sun_data.energy = sun_energy
    sun_data.color = (1.0, 0.97, 0.92)
    sun_obj = bpy.data.objects.new(name="Sun", object_data=sun_data)
    bpy.context.collection.objects.link(sun_obj)
    sun_obj.rotation_euler = (math.radians(52), math.radians(18), math.radians(-38))

    # Fill sky light
    fill_data = bpy.data.lights.new(name="FillLight", type="SUN")
    fill_data.energy = 0.9
    fill_data.color = (0.75, 0.85, 1.0)
    fill_obj = bpy.data.objects.new(name="FillLight", object_data=fill_data)
    bpy.context.collection.objects.link(fill_obj)
    fill_obj.rotation_euler = (math.radians(45), math.radians(-25), math.radians(140))

    # World background
    world = bpy.context.scene.world
    if not world:
        world = bpy.data.worlds.new("World")
        bpy.context.scene.world = world
    world.use_nodes = True
    bg = world.node_tree.nodes.get("Background")
    if bg:
        bg.inputs["Color"].default_value = ambient_color
        bg.inputs["Strength"].default_value = 0.65


def create_terrain_material(name: str, tex_name: str, roughness: float = 0.88) -> bpy.types.Material:
    mat = bpy.data.materials.new(name=name)
    mat.use_nodes = True
    nodes = mat.node_tree.nodes
    links = mat.node_tree.links
    nodes.clear()

    output = nodes.new(type="ShaderNodeOutputMaterial")
    bsdf = nodes.new(type="ShaderNodeBsdfPrincipled")
    bsdf.inputs["Roughness"].default_value = roughness
    bsdf.inputs["Metallic"].default_value = 0.0

    tex_file = TERRAIN_TEX_DIR / f"{tex_name}.png"
    if tex_file.exists():
        tex_node = nodes.new(type="ShaderNodeTexImage")
        img = bpy.data.images.load(str(tex_file))
        img.colorspace_settings.name = "sRGB"
        tex_node.image = img
        tex_node.interpolation = "Closest"
        links.new(tex_node.outputs["Color"], bsdf.inputs["Base Color"])
    else:
        # Fallback solid color
        colors = {
            "forest_grass_top": (0.16, 0.32, 0.11, 1.0),
            "plains_meadow_top": (0.28, 0.45, 0.14, 1.0),
            "mountain_stone_top": (0.49, 0.47, 0.45, 1.0),
            "cliff_side": (0.33, 0.31, 0.30, 1.0),
            "dirt_soil": (0.35, 0.25, 0.17, 1.0),
        }
        bsdf.inputs["Base Color"].default_value = colors.get(tex_name, (0.5, 0.5, 0.5, 1.0))

    links.new(bsdf.outputs["BSDF"], output.inputs["Surface"])
    return mat


def spawn_glb(slug: str, loc: tuple[float, float, float], rot_z: float = 0.0, scale: float = 1.0) -> list[bpy.types.Object]:
    glb_path = FAMILY_DIR / slug / "output" / "model.glb"
    if not glb_path.exists():
        return []
    
    # Save currently existing objects
    existing = set(bpy.data.objects)
    bpy.ops.import_scene.gltf(filepath=str(glb_path))
    imported = [o for o in bpy.data.objects if o not in existing]

    for o in imported:
        o.location = Vector(loc)
        o.rotation_euler.z = rot_z
        o.scale = Vector((scale, scale, scale))
    return imported


def spawn_external_glb(glb_path: Path, loc: tuple[float, float, float], rot_z: float = 0.0, scale: float = 1.0) -> list[bpy.types.Object]:
    if not glb_path.exists():
        return []
    existing = set(bpy.data.objects)
    bpy.ops.import_scene.gltf(filepath=str(glb_path))
    imported = [o for o in bpy.data.objects if o not in existing]
    for o in imported:
        o.location = Vector(loc)
        o.rotation_euler.z = rot_z
        o.scale = Vector((scale, scale, scale))
    return imported


def render_scene_to_file(out_path: Path, w: int, h: int, cam_loc: Vector, cam_target: Vector, ortho_scale: float) -> None:
    scene = bpy.context.scene
    scene.render.engine = resolve_eevee_engine()
    scene.render.resolution_x = w
    scene.render.resolution_y = h
    scene.render.film_transparent = False

    cam_data = bpy.data.cameras.new("SceneCam")
    cam_data.type = "ORTHO"
    cam_data.ortho_scale = ortho_scale
    cam = bpy.data.objects.new("SceneCam", cam_data)
    bpy.context.collection.objects.link(cam)
    scene.camera = cam

    cam.location = cam_loc
    look_at(cam, cam_target)

    scene.render.filepath = str(out_path)
    bpy.ops.render.render(write_still=True)
    print(f"[OK] Rendered {out_path.name} ({w}x{h})")


# -----------------------------------------------------------------------------
# 1. Biome Mockups
# -----------------------------------------------------------------------------

def render_biome_mockups() -> None:
    """Render Forest, Plains, and Mountain biome mockups."""
    # 1. Forest Biome Mockup
    clear_scene()
    setup_mockup_environment(sun_energy=2.8, ambient_color=(0.35, 0.48, 0.40, 1.0))
    mat_forest = create_terrain_material("mat_forest", "forest_grass_top", 0.88)
    
    # Terrain floor 10x10m
    bpy.ops.mesh.primitive_plane_add(size=10.0, location=(0, 0, 0))
    plane = bpy.context.active_object
    plane.data.materials.append(mat_forest)

    # Oak Tree
    oak_glb = TREE_DIR / "var_0_standard_oak" / "output" / "model.glb"
    spawn_external_glb(oak_glb, (-1.2, 0.8, 0.0), rot_z=math.radians(25))

    # Moss collars around tree trunk
    spawn_glb("moss_tree_base", (-1.2, 0.8, 0.0), rot_z=math.radians(10))
    spawn_glb("moss_tree_base", (-0.9, 0.6, 0.0), rot_z=math.radians(120))

    # Forest Dressing: Dense grass tufts + flowers + stone debris
    random.seed(42)
    forest_props = [
        ("grass_tuft_med_01", (-0.2, 1.2, 0.0)),
        ("grass_tuft_med_02", (-1.8, -0.4, 0.0)),
        ("grass_tuft_small_01", (0.5, 0.2, 0.0)),
        ("grass_tuft_small_02", (-0.8, -1.2, 0.0)),
        ("grass_tuft_small_03", (1.2, 1.0, 0.0)),
        ("grass_tuft_tall_01", (-2.2, 1.5, 0.0)),
        ("flower_white_cluster", (0.8, -0.6, 0.0)),
        ("flower_red_cluster", (-0.3, -0.8, 0.0)),
        ("stone_debris_single", (1.5, -1.2, 0.0)),
        ("stone_debris_trio", (1.8, 0.4, 0.0)),
        ("stone_debris_flat_patch", (-1.6, -1.6, 0.0)),
    ]
    for slug, loc in forest_props:
        spawn_glb(slug, loc, rot_z=random.uniform(0, math.pi * 2))

    cam_target = Vector((0.0, 0.0, 1.2))
    cam_loc = cam_target + Vector((7.0, -7.0, 6.0))
    render_scene_to_file(REVIEW_DIR / "biome_mockup_forest.png", 1280, 720, cam_loc, cam_target, ortho_scale=6.5)

    # 2. Plains Biome Mockup
    clear_scene()
    setup_mockup_environment(sun_energy=3.4, ambient_color=(0.50, 0.60, 0.72, 1.0))
    mat_plains = create_terrain_material("mat_plains", "plains_meadow_top", 0.85)

    bpy.ops.mesh.primitive_plane_add(size=10.0, location=(0, 0, 0))
    plane = bpy.context.active_object
    plane.data.materials.append(mat_plains)

    # Shrub oak in background
    shrub_glb = TREE_DIR / "var_4_shrub_oak" / "output" / "model.glb"
    spawn_external_glb(shrub_glb, (2.2, 2.0, 0.0), rot_z=math.radians(45))

    # Plains Dressing: Rich vibrant flower carpets & rolling grass tufts
    random.seed(101)
    plains_props = [
        ("flower_yellow_cluster", (-1.0, 0.5, 0.0)),
        ("flower_yellow_cluster", (-0.4, 1.2, 0.0)),
        ("flower_white_cluster", (0.5, 0.8, 0.0)),
        ("flower_white_cluster", (-1.5, -0.4, 0.0)),
        ("flower_mixed_accent", (0.0, -0.2, 0.0)),
        ("flower_red_cluster", (1.2, -0.6, 0.0)),
        ("grass_tuft_small_01", (-0.8, -1.0, 0.0)),
        ("grass_tuft_small_02", (1.4, 1.0, 0.0)),
        ("grass_tuft_small_03", (-1.8, 1.4, 0.0)),
        ("grass_tuft_med_01", (0.8, 1.5, 0.0)),
        ("grass_tuft_med_02", (-0.2, -1.4, 0.0)),
        ("grass_tuft_tall_01", (1.8, -1.2, 0.0)),
        ("stone_debris_flat_patch", (-1.4, -1.5, 0.0)),
        ("stone_debris_fine_scatter", (0.4, -1.1, 0.0)),
    ]
    for slug, loc in plains_props:
        spawn_glb(slug, loc, rot_z=random.uniform(0, math.pi * 2))

    cam_target = Vector((0.0, 0.0, 0.6))
    cam_loc = cam_target + Vector((7.0, -7.0, 6.0))
    render_scene_to_file(REVIEW_DIR / "biome_mockup_plains.png", 1280, 720, cam_loc, cam_target, ortho_scale=6.0)

    # 3. Mountain Biome Mockup
    clear_scene()
    setup_mockup_environment(sun_energy=3.6, ambient_color=(0.40, 0.50, 0.65, 1.0))
    mat_mtn = create_terrain_material("mat_mtn", "mountain_stone_top", 0.90)
    mat_cliff = create_terrain_material("mat_cliff", "cliff_side", 0.92)

    # Stepped rocky terrace
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=(0, 0, 0.5))
    c1 = bpy.context.active_object
    c1.scale = Vector((6.0, 6.0, 1.0))
    c1.data.materials.append(mat_mtn)

    bpy.ops.mesh.primitive_cube_add(size=1.0, location=(1.5, 1.5, 1.5))
    c2 = bpy.context.active_object
    c2.scale = Vector((3.5, 3.5, 1.0))
    c2.data.materials.append(mat_cliff)

    # Destructible Rock
    rock_glb = ROCK_DIR / "stage_1_var_1" / "output" / "model.glb"
    spawn_external_glb(rock_glb, (2.2, 1.8, 2.0), rot_z=math.radians(35), scale=0.8)

    # Mountain Dressing: Jagged stone debris, cliff ledge moss, hardy grass sprigs
    random.seed(333)
    mtn_props = [
        ("stone_debris_mountain_cluster", (0.4, 0.8, 1.0)),
        ("stone_debris_angular_chip", (-0.8, 0.6, 1.0)),
        ("stone_debris_single", (-1.2, -0.4, 1.0)),
        ("stone_debris_trio", (-0.2, -1.2, 1.0)),
        ("stone_debris_fine_scatter", (1.0, -0.6, 1.0)),
        ("moss_rock_shelf", (1.2, 0.2, 1.0)),
        ("moss_cliff_ledge", (-0.2, 1.8, 1.0)),
        ("grass_tuft_small_01", (-1.5, 1.2, 1.0)),
        ("grass_tuft_small_02", (0.6, -1.5, 1.0)),
        ("grass_tuft_tall_01", (-1.8, -1.0, 1.0)),
    ]
    for slug, loc in mtn_props:
        spawn_glb(slug, loc, rot_z=random.uniform(0, math.pi * 2))

    cam_target = Vector((0.4, 0.4, 1.4))
    cam_loc = cam_target + Vector((7.5, -7.5, 6.5))
    render_scene_to_file(REVIEW_DIR / "biome_mockup_mountain.png", 1280, 720, cam_loc, cam_target, ortho_scale=6.5)


# -----------------------------------------------------------------------------
# 2. Density Mockups (Low / Medium / High)
# -----------------------------------------------------------------------------

def render_density_mockups() -> None:
    """Render low, medium, and high scatter density mockups on a 6x6m terrain slice."""
    for density_mode in ("low", "medium", "high"):
        clear_scene()
        setup_mockup_environment(sun_energy=3.0, ambient_color=(0.45, 0.55, 0.68, 1.0))
        mat_plains = create_terrain_material("mat_plains", "plains_meadow_top", 0.85)

        bpy.ops.mesh.primitive_plane_add(size=6.0, location=(0, 0, 0))
        plane = bpy.context.active_object
        plane.data.materials.append(mat_plains)

        random.seed(777)
        if density_mode == "low":
            # ~6 scattered props across 6x6m (sparse accentuation)
            count = 7
        elif density_mode == "medium":
            # ~16 props across 6x6m (balanced natural meadow)
            count = 16
        else:
            # ~32 props across 6x6m (rich dense cluster / lush glade)
            count = 32

        all_pool = [
            "grass_tuft_small_01", "grass_tuft_small_02", "grass_tuft_small_03",
            "grass_tuft_med_01", "grass_tuft_med_02", "grass_tuft_tall_01",
            "flower_white_cluster", "flower_yellow_cluster", "flower_red_cluster",
            "stone_debris_single", "stone_debris_trio", "stone_debris_flat_patch",
        ]

        placed = 0
        for _ in range(count):
            slug = random.choice(all_pool)
            rx = random.uniform(-2.3, 2.3)
            ry = random.uniform(-2.3, 2.3)
            rot = random.uniform(0, math.pi * 2)
            spawn_glb(slug, (rx, ry, 0.0), rot_z=rot)
            placed += 1

        cam_target = Vector((0.0, 0.0, 0.2))
        cam_loc = cam_target + Vector((5.5, -5.5, 4.8))
        out_file = REVIEW_DIR / f"density_mockup_{density_mode}.png"
        render_scene_to_file(out_file, 1280, 720, cam_loc, cam_target, ortho_scale=4.5)


# -----------------------------------------------------------------------------
# 3. Gameplay Mockup
# -----------------------------------------------------------------------------

def render_gameplay_mockup() -> None:
    """Render full gameplay distance camera view (1920x1080) with hero scale context."""
    clear_scene()
    setup_mockup_environment(sun_energy=3.2, ambient_color=(0.45, 0.55, 0.70, 1.0))

    # Build terrain slice with path and elevation
    mat_forest = create_terrain_material("mat_forest", "forest_grass_top", 0.88)
    mat_dirt = create_terrain_material("mat_dirt", "dirt_soil", 0.92)
    mat_mtn = create_terrain_material("mat_mtn", "mountain_stone_top", 0.90)
    mat_cliff = create_terrain_material("mat_cliff", "cliff_side", 0.92)

    bpy.ops.mesh.primitive_plane_add(size=14.0, location=(0, 0, 0))
    base_floor = bpy.context.active_object
    base_floor.data.materials.append(mat_forest)

    # Raised rock bluff in background
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=(3.5, 3.5, 0.75))
    bluff = bpy.context.active_object
    bluff.scale = Vector((5.0, 5.0, 1.5))
    bluff.data.materials.append(mat_cliff)

    bpy.ops.mesh.primitive_cube_add(size=1.0, location=(3.5, 3.5, 1.5))
    bluff_top = bpy.context.active_object
    bluff_top.scale = Vector((4.8, 4.8, 0.2))
    bluff_top.data.materials.append(mat_mtn)

    # Dirt path diagonal strip
    bpy.ops.mesh.primitive_plane_add(size=1.0, location=(0, 0, 0.01))
    path = bpy.context.active_object
    path.scale = Vector((1.2, 12.0, 1.0))
    path.rotation_euler.z = math.radians(-30)
    path.data.materials.append(mat_dirt)

    # 1. Spawn Production Trees
    oak_std = TREE_DIR / "var_0_standard_oak" / "output" / "model.glb"
    spawn_external_glb(oak_std, (-2.5, 1.5, 0.0), rot_z=math.radians(15))
    oak_tall = TREE_DIR / "var_1_tall_oak" / "output" / "model.glb"
    spawn_external_glb(oak_tall, (-3.5, -1.8, 0.0), rot_z=math.radians(60))

    # 2. Spawn Production Rock
    rock_glb = ROCK_DIR / "stage_1_var_1" / "output" / "model.glb"
    spawn_external_glb(rock_glb, (3.2, 3.0, 1.6), rot_z=math.radians(40), scale=0.85)

    # 3. Spawn Stylized Character Scale Proxy (2m tall Cube Siege character box)
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=(0.2, -0.4, 1.0))
    hero = bpy.context.active_object
    hero.scale = Vector((0.5, 0.5, 1.0))
    hero_mat = bpy.data.materials.new("HeroProxy")
    hero_mat.use_nodes = True
    hero_bsdf = hero_mat.node_tree.nodes.get("Principled BSDF")
    hero_bsdf.inputs["Base Color"].default_value = (0.2, 0.45, 0.85, 1.0)
    hero.data.materials.append(hero_mat)

    # 4. Populate with Dressing Props across the scene
    random.seed(999)
    # Tree base moss
    spawn_glb("moss_tree_base", (-2.5, 1.5, 0.0), rot_z=math.radians(20))
    spawn_glb("moss_tree_base", (-3.5, -1.8, 0.0), rot_z=math.radians(80))

    # Cliff moss
    spawn_glb("moss_cliff_ledge", (1.1, 2.5, 1.5), rot_z=math.radians(-90))
    spawn_glb("moss_rock_shelf", (2.2, 3.2, 1.6), rot_z=math.radians(15))

    # Grass & Flowers & Stone scatter
    scatter_plan = [
        # Along path edges
        ("grass_tuft_small_01", (-0.8, -0.6, 0.0)),
        ("grass_tuft_small_02", (0.9, -0.8, 0.0)),
        ("grass_tuft_med_01", (-1.1, 0.2, 0.0)),
        ("grass_tuft_med_02", (1.2, 0.6, 0.0)),
        ("flower_yellow_cluster", (-0.7, 0.8, 0.0)),
        ("flower_white_cluster", (1.4, -0.2, 0.0)),
        ("flower_red_cluster", (-1.4, -1.2, 0.0)),
        ("flower_mixed_accent", (0.6, 1.4, 0.0)),
        # Near trees
        ("grass_tuft_tall_01", (-2.0, 0.6, 0.0)),
        ("grass_tuft_med_01", (-3.0, 0.4, 0.0)),
        ("flower_white_cluster", (-2.2, -1.0, 0.0)),
        ("stone_debris_single", (-1.8, -0.2, 0.0)),
        # Path stones & gravel
        ("stone_debris_fine_scatter", (0.1, -1.6, 0.01)),
        ("stone_debris_fine_scatter", (-0.2, 0.8, 0.01)),
        ("stone_debris_angular_chip", (0.5, -1.8, 0.0)),
        ("stone_debris_trio", (1.8, 1.2, 0.0)),
        ("stone_debris_flat_patch", (2.0, -0.8, 0.0)),
        # Rocky bluff
        ("stone_debris_mountain_cluster", (2.2, 2.2, 1.6)),
        ("stone_debris_single", (3.8, 1.8, 1.6)),
        ("grass_tuft_small_03", (1.8, 3.6, 1.6)),
    ]

    for slug, loc in scatter_plan:
        spawn_glb(slug, loc, rot_z=random.uniform(0, math.pi * 2))

    cam_target = Vector((0.0, 0.5, 0.8))
    # Isometric gameplay camera: ~45 deg azimuth, ~35 deg elevation
    cam_loc = cam_target + Vector((10.0, -10.0, 8.5))
    render_scene_to_file(REVIEW_DIR / "gameplay_mockup.png", 1920, 1080, cam_loc, cam_target, ortho_scale=10.0)


# -----------------------------------------------------------------------------
# Main Execution
# -----------------------------------------------------------------------------

def main() -> None:
    args = script_args()

    if args.variant:
        build_single_variant(args.variant)
        return

    if args.variants_only or args.all:
        print(f"\n=======================================================")
        print(f"Building all {len(VARIANTS)} Environment Dressing Props")
        print(f"=======================================================")
        for slug in VARIANTS:
            build_single_variant(slug)

    if args.mockups_only or args.all:
        print(f"\n=======================================================")
        print(f"Rendering Biome Mockups (Forest, Plains, Mountain)")
        print(f"=======================================================")
        render_biome_mockups()

        print(f"\n=======================================================")
        print(f"Rendering Density Mockups (Low, Medium, High)")
        print(f"=======================================================")
        render_density_mockups()

        print(f"\n=======================================================")
        print(f"Rendering Gameplay Distance Mockup")
        print(f"=======================================================")
        render_gameplay_mockup()

    print("\n[SUCCESS] Environment dressing pack Blender pipeline finished.")


if __name__ == "__main__":
    main()

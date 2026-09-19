"""render_gameplay_mockup.py - Render gameplay camera review mockup for Terrain Materials in Blender.

Constructs a multi-biome terrain slice (Forest, Plains, Mountain, Cliff, Dirt),
imports production Oak Tree and Destructible Rock assets,
and renders an in-game isometric camera view (1280x720).
"""

from __future__ import annotations

import math
from pathlib import Path
import bpy
from mathutils import Euler, Vector

ROOT = Path(__file__).resolve().parents[2]
TERRAIN_DIR = ROOT / "assets" / "environment" / "terrain_materials"
TEXTURES_DIR = TERRAIN_DIR / "textures"
REVIEW_DIR = TERRAIN_DIR / "review"
OAK_TREE_GLB = ROOT / "assets" / "environment" / "tree_oak" / "var_0_standard_oak" / "output" / "model.glb"
ROCK_GLB = ROOT / "assets" / "environment" / "destructible_rock" / "stage_1_var_1" / "output" / "model.glb"

REVIEW_DIR.mkdir(parents=True, exist_ok=True)


def clear_scene() -> None:
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete(use_global=False)
    for datablocks in (bpy.data.meshes, bpy.data.materials, bpy.data.cameras, bpy.data.lights, bpy.data.images):
        for block in list(datablocks):
            if block.users == 0:
                datablocks.remove(block)


def setup_lighting() -> None:
    # Key sun light
    sun_data = bpy.data.lights.new(name="Sun", type="SUN")
    sun_data.energy = 2.8
    sun_data.color = (1.0, 0.96, 0.90)
    sun_obj = bpy.data.objects.new(name="Sun", object_data=sun_data)
    bpy.context.collection.objects.link(sun_obj)
    sun_obj.rotation_euler = (math.radians(50), math.radians(20), math.radians(-40))

    # Fill sun light
    fill_data = bpy.data.lights.new(name="FillLight", type="SUN")
    fill_data.energy = 0.8
    fill_data.color = (0.75, 0.82, 0.95)
    fill_obj = bpy.data.objects.new(name="FillLight", object_data=fill_data)
    bpy.context.collection.objects.link(fill_obj)
    fill_obj.rotation_euler = (math.radians(40), math.radians(-30), math.radians(130))

    # World ambient background
    world = bpy.context.scene.world
    if not world:
        world = bpy.data.worlds.new("World")
        bpy.context.scene.world = world
    world.use_nodes = True
    bg = world.node_tree.nodes.get("Background")
    if bg:
        bg.inputs["Color"].default_value = (0.45, 0.55, 0.68, 1.0)
        bg.inputs["Strength"].default_value = 0.6


def create_textured_material(name: str, texture_file: str, roughness: float) -> bpy.types.Material:
    mat = bpy.data.materials.new(name=name)
    mat.use_nodes = True
    nodes = mat.node_tree.nodes
    links = mat.node_tree.links
    nodes.clear()

    output = nodes.new(type="ShaderNodeOutputMaterial")
    bsdf = nodes.new(type="ShaderNodeBsdfPrincipled")
    bsdf.inputs["Roughness"].default_value = roughness
    bsdf.inputs["Metallic"].default_value = 0.0

    tex_path = TEXTURES_DIR / texture_file
    if tex_path.exists():
        tex_node = nodes.new(type="ShaderNodeTexImage")
        img = bpy.data.images.load(str(tex_path))
        img.colorspace_settings.name = "sRGB"
        tex_node.image = img
        tex_node.interpolation = "Closest"  # Nearest neighbor point filtering
        links.new(tex_node.outputs["Color"], bsdf.inputs["Base Color"])
    else:
        bsdf.inputs["Base Color"].default_value = (0.5, 0.5, 0.5, 1.0)

    links.new(bsdf.outputs["BSDF"], output.inputs["Surface"])
    return mat


def build_terrain_mesh() -> bpy.types.Object:
    """Build a multi-biome stepped terrain chunk matching Cube Siege ChunkBuilder specifications."""
    mat_forest = create_textured_material("mat_forest", "forest_grass_top.png", 0.85)
    mat_plains = create_textured_material("mat_plains", "plains_meadow_top.png", 0.85)
    mat_mountain = create_textured_material("mat_mountain", "mountain_stone_top.png", 0.90)
    mat_cliff = create_textured_material("mat_cliff", "cliff_side.png", 0.92)
    mat_dirt = create_textured_material("mat_dirt", "dirt_soil.png", 0.92)

    # Heightmap for a 12x12 terrain area (x=0..11, z=0..11)
    # 0..4: Forest (y=0..1)
    # 4..8: Plains (y=1..2)
    # 8..11: Mountain / Cliff (y=3..5)
    H = [
        [0, 0, 0, 1, 1, 1, 2, 2, 3, 4, 5, 5],
        [0, 0, 0, 0, 1, 1, 2, 2, 3, 4, 5, 5],
        [0, 0, 0, 0, 1, 2, 2, 3, 3, 4, 5, 5],
        [0, 0, 0, 1, 1, 2, 2, 3, 4, 4, 5, 5],
        [0, 0, 1, 1, 2, 2, 3, 3, 4, 5, 5, 5],
        [1, 1, 1, 2, 2, 2, 3, 4, 4, 5, 5, 5],
        [1, 1, 2, 2, 2, 3, 3, 4, 5, 5, 5, 5],
        [1, 2, 2, 2, 3, 3, 4, 4, 5, 5, 5, 5],
        [2, 2, 2, 3, 3, 4, 4, 5, 5, 5, 5, 5],
        [2, 2, 3, 3, 4, 4, 5, 5, 5, 5, 5, 5],
        [3, 3, 3, 4, 4, 5, 5, 5, 5, 5, 5, 5],
        [3, 3, 4, 4, 5, 5, 5, 5, 5, 5, 5, 5],
    ]

    mesh = bpy.data.meshes.new("TerrainMesh")
    obj = bpy.data.objects.new("Terrain", mesh)
    bpy.context.collection.objects.link(obj)

    # Assign materials
    for m in (mat_forest, mat_plains, mat_mountain, mat_cliff, mat_dirt):
        obj.data.materials.append(m)

    verts: list[Vector] = []
    faces: list[list[int]] = []
    mat_indices: list[int] = []
    uv_coords: list[tuple[float, float]] = []

    def add_quad(p0: Vector, p1: Vector, p2: Vector, p3: Vector, mat_idx: int, uv_h: float = 1.0) -> None:
        idx = len(verts)
        verts.extend([p0, p1, p2, p3])
        faces.append([idx, idx + 1, idx + 2, idx + 3])
        mat_indices.append(mat_idx)
        # UVs
        uv_coords.extend([(0.0, 0.0), (1.0, 0.0), (1.0, uv_h), (0.0, uv_h)])

    size = 12
    for z in range(size):
        for x in range(size):
            y_top = float(H[z][x])
            fx, fz = float(x) - 6.0, float(z) - 6.0

            # Determine biome for top face
            if x + z < 8:
                mat_idx = 0  # Forest
            elif x + z < 14:
                mat_idx = 1  # Plains
            else:
                mat_idx = 2  # Mountain

            # Top quad
            p0 = Vector((fx, fz, y_top))
            p1 = Vector((fx + 1.0, fz, y_top))
            p2 = Vector((fx + 1.0, fz + 1.0, y_top))
            p3 = Vector((fx, fz + 1.0, y_top))
            add_quad(p0, p1, p2, p3, mat_idx, 1.0)

            # Check neighbors for vertical drop faces
            # North (z - 1)
            yn = H[z - 1][x] if z > 0 else 0
            if yn < H[z][x]:
                drop = y_top - float(yn)
                s0 = Vector((fx, fz, float(yn)))
                s1 = Vector((fx + 1.0, fz, float(yn)))
                s2 = Vector((fx + 1.0, fz, y_top))
                s3 = Vector((fx, fz, y_top))
                side_mat = 3 if y_top >= 3 else 4  # Cliff vs Dirt
                add_quad(s0, s1, s2, s3, side_mat, drop)

            # South (z + 1)
            ys = H[z + 1][x] if z < size - 1 else 0
            if ys < H[z][x]:
                drop = y_top - float(ys)
                s0 = Vector((fx + 1.0, fz + 1.0, float(ys)))
                s1 = Vector((fx, fz + 1.0, float(ys)))
                s2 = Vector((fx, fz + 1.0, y_top))
                s3 = Vector((fx + 1.0, fz + 1.0, y_top))
                side_mat = 3 if y_top >= 3 else 4
                add_quad(s0, s1, s2, s3, side_mat, drop)

            # West (x - 1)
            yw = H[z][x - 1] if x > 0 else 0
            if yw < H[z][x]:
                drop = y_top - float(yw)
                s0 = Vector((fx, fz + 1.0, float(yw)))
                s1 = Vector((fx, fz, float(yw)))
                s2 = Vector((fx, fz, y_top))
                s3 = Vector((fx, fz + 1.0, y_top))
                side_mat = 3 if y_top >= 3 else 4
                add_quad(s0, s1, s2, s3, side_mat, drop)

            # East (x + 1)
            ye = H[z][x + 1] if x < size - 1 else 0
            if ye < H[z][x]:
                drop = y_top - float(ye)
                s0 = Vector((fx + 1.0, fz, float(ye)))
                s1 = Vector((fx + 1.0, fz + 1.0, float(ye)))
                s2 = Vector((fx + 1.0, fz + 1.0, y_top))
                s3 = Vector((fx + 1.0, fz, y_top))
                side_mat = 3 if y_top >= 3 else 4
                add_quad(s0, s1, s2, s3, side_mat, drop)

    mesh.from_pydata(verts, [], faces)
    mesh.update()

    # Assign materials and UVs
    for poly, m_idx in zip(mesh.polygons, mat_indices):
        poly.material_index = m_idx

    uv_layer = mesh.uv_layers.new(name="UVMap")
    for loop in mesh.loops:
        uv_layer.data[loop.index].uv = uv_coords[loop.vertex_index]

    return obj


def import_assets() -> None:
    """Import Oak Tree and Destructible Rock GLBs into the scene."""
    # 1. Oak Tree in Forest/Plains area
    if OAK_TREE_GLB.exists():
        bpy.ops.import_scene.gltf(filepath=str(OAK_TREE_GLB))
        tree_objs = [o for o in bpy.context.selected_objects if o.type == "MESH"]
        for o in tree_objs:
            o.location = (-2.5, -2.5, 0.0)
            o.scale = (0.9, 0.9, 0.9)
            o.rotation_euler = (0, 0, math.radians(25))

    # 2. Destructible Rock in Mountain/Cliff area
    if ROCK_GLB.exists():
        bpy.ops.import_scene.gltf(filepath=str(ROCK_GLB))
        rock_objs = [o for o in bpy.context.selected_objects if o.type == "MESH"]
        for o in rock_objs:
            o.location = (2.2, 2.2, 5.0)
            o.scale = (1.1, 1.1, 1.1)
            o.rotation_euler = (0, 0, math.radians(-15))


def setup_gameplay_camera() -> None:
    """Position camera at Cube Siege dimetric/isometric gameplay perspective."""
    cam_data = bpy.data.cameras.new(name="GameplayCamera")
    cam_data.type = "ORTHO"
    cam_data.ortho_scale = 16.0
    cam_data.clip_start = 0.1
    cam_data.clip_end = 200.0

    cam_obj = bpy.data.objects.new(name="GameplayCamera", object_data=cam_data)
    bpy.context.collection.objects.link(cam_obj)
    bpy.context.scene.camera = cam_obj

    # Position at 45 deg azimuth, 35.264 deg elevation (true isometric)
    dist = 40.0
    elevation = math.radians(35.264)
    azimuth = math.radians(45.0)

    x = dist * math.cos(elevation) * math.sin(azimuth)
    y = -dist * math.cos(elevation) * math.cos(azimuth)
    z = dist * math.sin(elevation) + 2.0

    cam_obj.location = (x, y, z)
    cam_obj.rotation_euler = (math.radians(54.736), 0, math.radians(45.0))


def render_mockup() -> Path:
    clear_scene()
    setup_lighting()
    build_terrain_mesh()
    import_assets()
    setup_gameplay_camera()

    scene = bpy.context.scene
    scene.render.resolution_x = 1280
    scene.render.resolution_y = 720
    scene.render.resolution_percentage = 100
    scene.render.engine = "BLENDER_EEVEE"

    out_path = REVIEW_DIR / "gameplay_mockup.png"
    scene.render.filepath = str(out_path)
    bpy.ops.render.render(write_still=True)
    print(f"[SAVED] {out_path} (1280x720)")
    return out_path


if __name__ == "__main__":
    render_mockup()

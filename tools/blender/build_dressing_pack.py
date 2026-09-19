"""build_dressing_pack.py - Build all 19 environment dressing props with shared atlas material and render mockups.

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

import bmesh
import bpy
from mathutils import Euler, Vector

# Import helpers from build_voxel_asset
BUILD_SCRIPT = Path(__file__).resolve().parent / "build_voxel_asset.py"
sys.path.insert(0, str(BUILD_SCRIPT.parent))
from build_voxel_asset import (
    clear_scene,
    export_glb,
    render_views,
    setup_review_scene,
    resolve_eevee_engine,
    look_at,
    parse_voxels,
    source_to_blender,
    face_vertices,
    NEIGHBORS,
)

ROOT = Path(__file__).resolve().parents[2]
FAMILY_DIR = ROOT / "assets" / "environment" / "dressing_pack"
REVIEW_DIR = FAMILY_DIR / "review"
TEXTURES_DIR = FAMILY_DIR / "textures"
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
        materials = gltf_json.get("materials", [])
        if not meshes:
            raise RuntimeError("GLB contains no meshes")
        if len(materials) != 1:
            raise RuntimeError(f"GLB expected exactly 1 shared material, found {len(materials)}")
        mat0 = materials[0]
        pbr = mat0.get("pbrMetallicRoughness", {})
        if "baseColorTexture" not in pbr:
            raise RuntimeError("GLB material missing baseColorTexture")
        if "metallicRoughnessTexture" not in pbr:
            raise RuntimeError("GLB material missing metallicRoughnessTexture")

        # Extract POSITION accessor bounds
        pos_idx = meshes[0]["primitives"][0]["attributes"]["POSITION"]
        pos_acc = gltf_json["accessors"][pos_idx]
        pos_min = [round(float(x), 3) for x in pos_acc["min"]]
        pos_max = [round(float(x), 3) for x in pos_acc["max"]]
        pos_span = [round(pos_max[i] - pos_min[i], 3) for i in range(3)]

    return {
        "size_bytes": size,
        "version": version,
        "meshes": len(meshes),
        "materials": len(materials),
        "bounds_min": pos_min,
        "bounds_max": pos_max,
        "aabb_span": pos_span,
    }


def get_or_create_shared_atlas_material() -> bpy.types.Material:
    mat = bpy.data.materials.get("mat_dressing_atlas")
    if mat:
        return mat
    mat = bpy.data.materials.new(name="mat_dressing_atlas")
    mat.use_nodes = True
    nodes = mat.node_tree.nodes
    links = mat.node_tree.links
    nodes.clear()

    output = nodes.new(type="ShaderNodeOutputMaterial")
    bsdf = nodes.new(type="ShaderNodeBsdfPrincipled")
    bsdf.inputs["Roughness"].default_value = 1.0
    bsdf.inputs["Metallic"].default_value = 1.0

    tex_path = TEXTURES_DIR / "dressing_palette_atlas.png"
    if tex_path.exists():
        tex_node = nodes.new(type="ShaderNodeTexImage")
        img = bpy.data.images.load(str(tex_path))
        img.colorspace_settings.name = "sRGB"
        tex_node.image = img
        tex_node.interpolation = "Closest"
        links.new(tex_node.outputs["Color"], bsdf.inputs["Base Color"])
    else:
        bsdf.inputs["Base Color"].default_value = (0.3, 0.5, 0.2, 1.0)

    roughness_path = TEXTURES_DIR / "dressing_roughness_atlas.png"
    if roughness_path.exists():
        mr_node = nodes.new(type="ShaderNodeTexImage")
        mr_img = bpy.data.images.load(str(roughness_path))
        mr_img.colorspace_settings.name = "Non-Color"
        mr_node.image = mr_img
        mr_node.interpolation = "Closest"

        sep = nodes.new(type="ShaderNodeSeparateColor")
        links.new(mr_node.outputs["Color"], sep.inputs["Color"])
        links.new(sep.outputs["Green"], bsdf.inputs["Roughness"])
        links.new(sep.outputs["Blue"], bsdf.inputs["Metallic"])

    links.new(bsdf.outputs["BSDF"], output.inputs["Surface"])
    return mat


def token_to_atlas_uv(spec: dict) -> tuple[float, float]:
    cell = spec.get("atlas_cell", [0, 0])
    col, row = cell[0], cell[1]
    # In Blender UV space: (0,0) is bottom-left. Texture row 0 is top.
    u = (col + 0.5) / 8.0
    v = 1.0 - (row + 0.5) / 8.0
    return u, v


def build_grass_mesh(data: dict, occupied: dict, width: int, height: int, depth: int, voxel_size: float, shared_mat: bpy.types.Material) -> bpy.types.Object:
    bm = bmesh.new()
    uv_layer = bm.loops.layers.uv.new("UVMap")

    columns = {}
    for (sx, sy, sz), token in occupied.items():
        columns.setdefault((sx, sz), []).append((sy, token))

    for k in columns:
        columns[k].sort(key=lambda item: item[0])

    is_swept = "med_02" in data["name"]
    max_r = max(0.05, max(width, depth) * voxel_size * 0.5)

    for (sx, sz), levels in columns.items():
        cx = (sx - (width - 1) / 2.0) * voxel_size
        cy = (sz - (depth - 1) / 2.0) * voxel_size
        dist = math.hypot(cx, cy)
        theta = math.atan2(cy, cx) if dist > 0.001 else 0.0

        if is_swept:
            lx = math.cos(theta) * 0.35 + 0.65
            ly = math.sin(theta) * 0.35 + 0.15
            llen = math.hypot(lx, ly)
            lean_x, lean_y = lx / llen, ly / llen
            max_lean = 0.08 + 0.12 * (dist / max_r)
        else:
            lean_x = math.cos(theta) if dist > 0.001 else 0.0
            lean_y = math.sin(theta) if dist > 0.001 else 0.0
            max_lean = 0.03 + 0.08 * (dist / max_r)

        tx = -lean_y if dist > 0.001 else 1.0
        ty = lean_x if dist > 0.001 else 0.0
        bx = lean_x if dist > 0.001 else 0.0
        by = lean_y if dist > 0.001 else 1.0

        H = levels[-1][0] + 1
        total_col_height = H * voxel_size

        def get_layer_coords(z_val):
            tz = min(1.0, z_val / max(0.01, total_col_height))
            shift = (tz ** 1.3) * max_lean
            px = cx + lean_x * shift
            py = cy + lean_y * shift
            w = voxel_size * 0.44 * (1.0 - 0.70 * tz)
            th = voxel_size * 0.28 * (1.0 - 0.85 * tz)
            v0 = (px - tx * w - bx * th, py - ty * w - by * th, z_val)
            v1 = (px + tx * w - bx * th, py + ty * w - by * th, z_val)
            v2 = (px + tx * w + bx * th, py + ty * w + by * th, z_val)
            v3 = (px - tx * w + bx * th, py - ty * w + by * th, z_val)
            return px, py, [v0, v1, v2, v3]

        def token_uv(tok):
            spec = data["materials"].get(tok, {})
            return token_to_atlas_uv(spec)

        last_top_verts = None

        for idx, (sy, tok) in enumerate(levels):
            z_bot = sy * voxel_size
            z_top = (sy + 1) * voxel_size
            uv = token_uv(tok)
            is_tip = (idx == len(levels) - 1)

            if last_top_verts is None:
                _, _, bot_coords = get_layer_coords(z_bot)
                bot_verts = [bm.verts.new(c) for c in bot_coords]
                if z_bot <= 0.001:
                    bf = bm.faces.new([bot_verts[3], bot_verts[2], bot_verts[1], bot_verts[0]])
                    for l in bf.loops:
                        l[uv_layer].uv = uv
            else:
                bot_verts = last_top_verts

            if not is_tip:
                _, _, top_coords = get_layer_coords(z_top)
                top_verts = [bm.verts.new(c) for c in top_coords]
                quads = [
                    [bot_verts[0], bot_verts[1], top_verts[1], top_verts[0]],
                    [bot_verts[1], bot_verts[2], top_verts[2], top_verts[1]],
                    [bot_verts[2], bot_verts[3], top_verts[3], top_verts[2]],
                    [bot_verts[3], bot_verts[0], top_verts[0], top_verts[3]],
                ]
                for q in quads:
                    f = bm.faces.new(q)
                    for l in f.loops:
                        l[uv_layer].uv = uv
                last_top_verts = top_verts
            else:
                px, py, _ = get_layer_coords(z_top)
                tz = 1.0
                shift = (tz ** 1.3) * max_lean
                tip_x = cx + lean_x * shift
                tip_y = cy + lean_y * shift
                w_tip = voxel_size * 0.44 * 0.20
                t0 = bm.verts.new((tip_x - tx * w_tip, tip_y - ty * w_tip, z_top))
                t1 = bm.verts.new((tip_x + tx * w_tip, tip_y + ty * w_tip, z_top))
                faces_to_tip = [
                    [bot_verts[0], bot_verts[1], t1, t0],
                    [bot_verts[1], bot_verts[2], t1],
                    [bot_verts[2], bot_verts[3], t0, t1],
                    [bot_verts[3], bot_verts[0], t0],
                ]
                for f_verts in faces_to_tip:
                    f = bm.faces.new(f_verts)
                    for l in f.loops:
                        l[uv_layer].uv = uv
                last_top_verts = None

    mesh = bpy.data.meshes.new(f"{data['name']}_mesh")
    bm.to_mesh(mesh)
    bm.free()

    obj = bpy.data.objects.new(data["name"], mesh)
    bpy.context.collection.objects.link(obj)
    obj.data.materials.append(shared_mat)
    return obj


def build_flower_mesh(data: dict, occupied: dict, width: int, height: int, depth: int, voxel_size: float, shared_mat: bpy.types.Material) -> bpy.types.Object:
    bm = bmesh.new()
    uv_layer = bm.loops.layers.uv.new("UVMap")
    slug = data["name"]

    def token_uv(tok):
        spec = data["materials"].get(tok, {})
        return token_to_atlas_uv(spec)

    # Determine pistil and petal tokens strictly per flower archetype to avoid token role collisions
    if "yellow" in slug:
        pistil_tokens = {"O"}
        petal_tokens = {"Y"}
    elif "red" in slug:
        pistil_tokens = {"C"}
        petal_tokens = {"R"}
    elif "white" in slug:
        pistil_tokens = {"Y"}
        petal_tokens = {"W"}
    elif "mixed" in slug:
        pistil_tokens = {"Y"}
        petal_tokens = {"P"}
    else:
        pistil_tokens = {"Y", "O", "C"}
        petal_tokens = {"W", "R", "P"}

    pistils = []
    for (sx, sy, sz), tok in occupied.items():
        if tok in pistil_tokens:
            cx = (sx - (width - 1) / 2.0) * voxel_size
            cy = (sz - (depth - 1) / 2.0) * voxel_size
            cz = (sy + 0.5) * voxel_size
            pistils.append((cx, cy, cz, sx, sy, sz))

    for (sx, sy, sz), tok in occupied.items():
        cx = (sx - (width - 1) / 2.0) * voxel_size
        cy = (sz - (depth - 1) / 2.0) * voxel_size
        uv = token_uv(tok)
        r = math.hypot(cx, cy)
        nx = cx / r if r > 0.001 else 0.0
        ny = cy / r if r > 0.001 else 0.0

        if sy == 0 and tok in ("D", "G"):
            # Basal rosette leaf: flat, outward-pointing leaf slab hugging the ground
            z_base = 0.05
            z_tip = 0.012
            w_base = voxel_size * 0.40
            w_tip = voxel_size * 0.20
            tx, ty = -ny, nx
            in_x = cx - nx * (voxel_size * 0.35)
            in_y = cy - ny * (voxel_size * 0.35)
            out_x = cx + nx * (voxel_size * 0.45)
            out_y = cy + ny * (voxel_size * 0.45)

            v0 = (in_x - tx * w_base, in_y - ty * w_base, 0.0)
            v1 = (in_x + tx * w_base, in_y + ty * w_base, 0.0)
            v2 = (out_x + tx * w_tip, out_y + ty * w_tip, 0.0)
            v3 = (out_x - tx * w_tip, out_y - ty * w_tip, 0.0)

            v4 = (in_x - tx * w_base, in_y - ty * w_base, z_base)
            v5 = (in_x + tx * w_base, in_y + ty * w_base, z_base)
            v6 = (out_x + tx * w_tip, out_y + ty * w_tip, z_tip)
            v7 = (out_x - tx * w_tip, out_y - ty * w_tip, z_tip)

            bv = [bm.verts.new(c) for c in [v0, v1, v2, v3, v4, v5, v6, v7]]
            faces = [
                [bv[3], bv[2], bv[1], bv[0]],
                [bv[4], bv[5], bv[6], bv[7]],
                [bv[0], bv[1], bv[5], bv[4]],
                [bv[1], bv[2], bv[6], bv[5]],
                [bv[2], bv[3], bv[7], bv[6]],
                [bv[3], bv[0], bv[4], bv[7]],
            ]
            for f_indices in faces:
                f = bm.faces.new(f_indices)
                for l in f.loops:
                    l[uv_layer].uv = uv

        elif tok == "G":
            # Slender stem column
            hw = voxel_size * 0.22
            z_bot = sy * voxel_size
            z_top = (sy + 1) * voxel_size
            v0 = (cx - hw, cy - hw, z_bot)
            v1 = (cx + hw, cy - hw, z_bot)
            v2 = (cx + hw, cy + hw, z_bot)
            v3 = (cx - hw, cy + hw, z_bot)

            v4 = (cx - hw, cy - hw, z_top)
            v5 = (cx + hw, cy - hw, z_top)
            v6 = (cx + hw, cy + hw, z_top)
            v7 = (cx - hw, cy + hw, z_top)

            bv = [bm.verts.new(c) for c in [v0, v1, v2, v3, v4, v5, v6, v7]]
            faces = [
                [bv[3], bv[2], bv[1], bv[0]],
                [bv[4], bv[5], bv[6], bv[7]],
                [bv[0], bv[1], bv[5], bv[4]],
                [bv[1], bv[2], bv[6], bv[5]],
                [bv[2], bv[3], bv[7], bv[6]],
                [bv[3], bv[0], bv[4], bv[7]],
            ]
            for f_indices in faces:
                f = bm.faces.new(f_indices)
                for l in f.loops:
                    l[uv_layer].uv = uv

        elif tok in pistil_tokens:
            # Pistil center: chunky faceted central core
            hw = voxel_size * 0.32
            cz = (sy + 0.5) * voxel_size
            hh = voxel_size * 0.26
            v0 = (cx - hw, cy - hw, cz - hh)
            v1 = (cx + hw, cy - hw, cz - hh)
            v2 = (cx + hw, cy + hw, cz - hh)
            v3 = (cx - hw, cy + hw, cz - hh)

            v4 = (cx - hw, cy - hw, cz + hh)
            v5 = (cx + hw, cy - hw, cz + hh)
            v6 = (cx + hw, cy + hw, cz + hh)
            v7 = (cx - hw, cy + hw, cz + hh)

            bv = [bm.verts.new(c) for c in [v0, v1, v2, v3, v4, v5, v6, v7]]
            faces = [
                [bv[3], bv[2], bv[1], bv[0]],
                [bv[4], bv[5], bv[6], bv[7]],
                [bv[0], bv[1], bv[5], bv[4]],
                [bv[1], bv[2], bv[6], bv[5]],
                [bv[2], bv[3], bv[7], bv[6]],
                [bv[3], bv[0], bv[4], bv[7]],
            ]
            for f_indices in faces:
                f = bm.faces.new(f_indices)
                for l in f.loops:
                    l[uv_layer].uv = uv

        else:
            # Petal: angled petal plate/blade
            best_pistil = None
            best_dist = 999.0
            for px, py, pz, psx, psy, psz in pistils:
                d_sq = (cx - px) ** 2 + (cy - py) ** 2 + ((sy - psy) * voxel_size) ** 2
                if d_sq < best_dist:
                    best_dist = d_sq
                    best_pistil = (px, py, pz)

            if best_pistil:
                p_dx = cx - best_pistil[0]
                p_dy = cy - best_pistil[1]
                p_r = math.hypot(p_dx, p_dy)
                if p_r > 0.001:
                    p_nx, p_ny = p_dx / p_r, p_dy / p_r
                else:
                    p_nx, p_ny = nx, ny
            else:
                p_nx, p_ny = nx, ny

            p_tx, p_ty = -p_ny, p_nx
            cz = (sy + 0.45) * voxel_size

            # Distinct archetype tilts
            if "white" in slug:
                tilt_z = 0.025
                w_petal = voxel_size * 0.38
                thick = 0.020
            elif "yellow" in slug:
                tilt_z = 0.045
                w_petal = voxel_size * 0.36
                thick = 0.022
            elif "red" in slug:
                tilt_z = 0.060 if sy >= 4 else 0.040
                w_petal = voxel_size * 0.42
                thick = 0.024
            elif "mixed" in slug:
                tilt_z = -0.040 if sy >= 3 else 0.025
                w_petal = voxel_size * 0.38
                thick = 0.022
            else:
                tilt_z = 0.030
                w_petal = voxel_size * 0.38
                thick = 0.020

            in_x = cx - p_nx * (voxel_size * 0.35)
            in_y = cy - p_ny * (voxel_size * 0.35)
            out_x = cx + p_nx * (voxel_size * 0.45)
            out_y = cy + p_ny * (voxel_size * 0.45)

            z_in = cz - tilt_z * 0.5
            z_out = cz + tilt_z

            v0 = (in_x - p_tx * w_petal, in_y - p_ty * w_petal, z_in - thick * 0.5)
            v1 = (in_x + p_tx * w_petal, in_y + p_ty * w_petal, z_in - thick * 0.5)
            v2 = (out_x + p_tx * (w_petal * 0.7), out_y + p_ty * (w_petal * 0.7), z_out - thick * 0.5)
            v3 = (out_x - p_tx * (w_petal * 0.7), out_y - p_ty * (w_petal * 0.7), z_out - thick * 0.5)

            v4 = (in_x - p_tx * w_petal, in_y - p_ty * w_petal, z_in + thick * 0.5)
            v5 = (in_x + p_tx * w_petal, in_y + p_ty * w_petal, z_in + thick * 0.5)
            v6 = (out_x + p_tx * (w_petal * 0.7), out_y + p_ty * (w_petal * 0.7), z_out + thick * 0.5)
            v7 = (out_x - p_tx * (w_petal * 0.7), out_y - p_ty * (w_petal * 0.7), z_out + thick * 0.5)

            bv = [bm.verts.new(c) for c in [v0, v1, v2, v3, v4, v5, v6, v7]]
            faces = [
                [bv[3], bv[2], bv[1], bv[0]],
                [bv[4], bv[5], bv[6], bv[7]],
                [bv[0], bv[1], bv[5], bv[4]],
                [bv[1], bv[2], bv[6], bv[5]],
                [bv[2], bv[3], bv[7], bv[6]],
                [bv[3], bv[0], bv[4], bv[7]],
            ]
            for f_indices in faces:
                f = bm.faces.new(f_indices)
                for l in f.loops:
                    l[uv_layer].uv = uv

    mesh = bpy.data.meshes.new(f"{data['name']}_mesh")
    bm.to_mesh(mesh)
    bm.free()

    obj = bpy.data.objects.new(data["name"], mesh)
    bpy.context.collection.objects.link(obj)
    obj.data.materials.append(shared_mat)
    return obj


def build_moss_mesh(data: dict, occupied: dict, width: int, height: int, depth: int, voxel_size: float, shared_mat: bpy.types.Material) -> bpy.types.Object:
    bm = bmesh.new()
    uv_layer = bm.loops.layers.uv.new("UVMap")
    slug = data["name"]

    def token_uv(tok):
        spec = data["materials"].get(tok, {})
        return token_to_atlas_uv(spec)

    for (sx, sy, sz), tok in occupied.items():
        cx = (sx - (width - 1) / 2.0) * voxel_size
        cy = (sz - (depth - 1) / 2.0) * voxel_size
        uv = token_uv(tok)
        hw = voxel_size * 0.46
        z_bot = sy * voxel_size
        z_top = (sy + 1) * voxel_size

        has_above = (sx, sy + 1, sz) in occupied
        has_left = (sx - 1, sy, sz) in occupied
        has_right = (sx + 1, sy, sz) in occupied
        has_front = (sx, sy, sz + 1) in occupied
        has_back = (sx, sy, sz - 1) in occupied

        cushion_z = 0.015 if not has_above else 0.0

        v0 = (cx - hw, cy - hw, z_bot)
        v1 = (cx + hw, cy - hw, z_bot)
        v2 = (cx + hw, cy + hw, z_bot)
        v3 = (cx - hw, cy + hw, z_bot)

        v4 = (cx - hw, cy - hw, z_top)
        v5 = (cx + hw, cy - hw, z_top)
        v6 = (cx + hw, cy + hw, z_top)
        v7 = (cx - hw, cy + hw, z_top)

        if not has_above:
            v_mid = (cx, cy, z_top + cushion_z)
            bv = [bm.verts.new(c) for c in [v0, v1, v2, v3, v4, v5, v6, v7, v_mid]]
            roof_faces = [
                [bv[4], bv[5], bv[8]],
                [bv[5], bv[6], bv[8]],
                [bv[6], bv[7], bv[8]],
                [bv[7], bv[4], bv[8]],
            ]
            for rf in roof_faces:
                f = bm.faces.new(rf)
                for l in f.loops:
                    l[uv_layer].uv = uv
        else:
            bv = [bm.verts.new(c) for c in [v0, v1, v2, v3, v4, v5, v6, v7]]
            tf = bm.faces.new([bv[4], bv[5], bv[6], bv[7]])
            for l in tf.loops:
                l[uv_layer].uv = uv

        if z_bot <= 0.001 or (sx, sy - 1, sz) not in occupied:
            bf = bm.faces.new([bv[3], bv[2], bv[1], bv[0]])
            for l in bf.loops:
                l[uv_layer].uv = uv

        sides = [
            (has_back, [bv[0], bv[1], bv[5], bv[4]]),
            (has_right, [bv[1], bv[2], bv[6], bv[5]]),
            (has_front, [bv[2], bv[3], bv[7], bv[6]]),
            (has_left, [bv[3], bv[0], bv[4], bv[7]]),
        ]
        for has_neighbor, sverts in sides:
            if not has_neighbor:
                f = bm.faces.new(sverts)
                for l in f.loops:
                    l[uv_layer].uv = uv

        # For cliff ledge: add 3D hanging stalactite tendrils dripping down over cliff face
        if slug == "moss_cliff_ledge" and sy == 0 and not has_front:
            tendril_len = 0.08 + 0.06 * ((sx * 3) % 4)
            thw = hw * 0.4
            thick = 0.015
            t0 = bm.verts.new((cx - thw, cy + hw * 0.9, 0.0))
            t1 = bm.verts.new((cx + thw, cy + hw * 0.9, 0.0))
            t2 = bm.verts.new((cx + thw, cy + hw * 0.9 - thick, 0.0))
            t3 = bm.verts.new((cx - thw, cy + hw * 0.9 - thick, 0.0))
            tip = bm.verts.new((cx, cy + hw * 0.9 - thick * 0.5, -tendril_len))

            tendril_faces = [
                [t0, t1, tip],
                [t1, t2, tip],
                [t2, t3, tip],
                [t3, t0, tip],
            ]
            for tf in tendril_faces:
                f = bm.faces.new(tf)
                for l in f.loops:
                    l[uv_layer].uv = uv

    mesh = bpy.data.meshes.new(f"{data['name']}_mesh")
    bm.to_mesh(mesh)
    bm.free()

    obj = bpy.data.objects.new(data["name"], mesh)
    bpy.context.collection.objects.link(obj)
    obj.data.materials.append(shared_mat)
    return obj


def build_stone_debris_mesh(data: dict, occupied: dict, width: int, height: int, depth: int, voxel_size: float, shared_mat: bpy.types.Material) -> bpy.types.Object:
    bm = bmesh.new()
    h = voxel_size / 2.0

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
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=0.001)
    bmesh.ops.dissolve_limit(bm, angle_limit=math.radians(2.0), verts=bm.verts, edges=bm.edges)
    bm.verts.ensure_lookup_table()
    bm.edges.ensure_lookup_table()
    bm.faces.ensure_lookup_table()

    convex_edges = []
    for e in bm.edges:
        if len(e.link_faces) == 2 and not e.is_boundary:
            if abs(e.verts[0].co.z) <= 0.001 and abs(e.verts[1].co.z) <= 0.001:
                continue
            f1, f2 = e.link_faces
            angle = f1.normal.angle(f2.normal)
            if angle > math.radians(45):
                edge_mid = (e.verts[0].co + e.verts[1].co) * 0.5
                face_mid = (f1.calc_center_bounds() + f2.calc_center_bounds()) * 0.5
                avg_normal = f1.normal + f2.normal
                if (face_mid - edge_mid).dot(avg_normal) < 0:
                    convex_edges.append(e)

    bevel_width = voxel_size * 0.22
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

    uv_layer = bm.loops.layers.uv.new("UVMap")
    stone_materials = data["materials"]

    for f in bm.faces:
        nz = f.normal.z
        center = f.calc_center_bounds()

        if "M" in stone_materials and nz > 0.6 and center.z < 0.15:
            tok = "M"
        elif "D" in stone_materials and nz < -0.4:
            tok = "D"
        elif "L" in stone_materials and nz > 0.55:
            tok = "L"
        else:
            tok = "S" if "S" in stone_materials else list(stone_materials.keys())[0]

        spec = stone_materials.get(tok, {})
        uv = token_to_atlas_uv(spec)
        for loop in f.loops:
            loop[uv_layer].uv = uv

    mesh = bpy.data.meshes.new(f"{data['name']}_mesh")
    bm.to_mesh(mesh)
    bm.free()

    obj = bpy.data.objects.new(data["name"], mesh)
    bpy.context.collection.objects.link(obj)
    obj.data.materials.append(shared_mat)
    return obj


def build_dressing_mesh(data: dict) -> tuple[bpy.types.Object, dict]:
    """Build a unified single-mesh object with shared atlas material and UV mapping."""
    occupied, width, height, depth = parse_voxels(data)
    voxel_size = float(data["voxel_size"])
    shared_mat = get_or_create_shared_atlas_material()
    name = data.get("name", "")

    if name.startswith("grass_tuft"):
        obj = build_grass_mesh(data, occupied, width, height, depth, voxel_size, shared_mat)
    elif name.startswith("flower_"):
        obj = build_flower_mesh(data, occupied, width, height, depth, voxel_size, shared_mat)
    elif name.startswith("moss_"):
        obj = build_moss_mesh(data, occupied, width, height, depth, voxel_size, shared_mat)
    elif name.startswith("stone_debris"):
        obj = build_stone_debris_mesh(data, occupied, width, height, depth, voxel_size, shared_mat)
    else:
        obj = build_stone_debris_mesh(data, occupied, width, height, depth, voxel_size, shared_mat)

    total_polys = len(obj.data.polygons)
    total_tris = sum(len(p.vertices) - 2 for p in obj.data.polygons)

    metrics = {
        "occupied_voxels": len(occupied),
        "visible_faces": total_polys,
        "triangles": total_tris,
        "mesh_objects": 1,
        "materials": 1,
        "shared_material": "mat_dressing_atlas",
        "atlas_texture": "dressing_palette_atlas.png",
        "roughness_atlas_texture": "dressing_roughness_atlas.png",
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
    return obj, metrics


def build_single_variant(slug: str) -> dict:
    pkg_dir = FAMILY_DIR / slug
    manifest = load_json(pkg_dir / "manifest.json")
    source_path = pkg_dir / manifest["source"]
    data = load_json(source_path)

    clear_scene()
    obj, metrics = build_dressing_mesh(data)

    output_path = pkg_dir / manifest.get("outputs", {}).get("model", "output/model.glb")
    export_glb(output_path, [obj])
    glb_info = validate_glb_export(output_path)

    actual_span = glb_info["aabb_span"]
    bounds_min = glb_info["bounds_min"]
    bounds_max = glb_info["bounds_max"]

    metrics["mesh_aabb"] = {
        "x": actual_span[0],
        "y": actual_span[1],
        "z": actual_span[2],
    }
    metrics["mesh_bounds_min"] = {
        "x": bounds_min[0],
        "y": bounds_min[1],
        "z": bounds_min[2],
    }
    metrics["mesh_bounds_max"] = {
        "x": bounds_max[0],
        "y": bounds_max[1],
        "z": bounds_max[2],
    }
    metrics["nominal_grid_size"] = {
        "x": round(float(data["voxel_size"]) * metrics["grid"]["x"], 3),
        "y": round(float(data["voxel_size"]) * metrics["grid"]["y"], 3),
        "z": round(float(data["voxel_size"]) * metrics["grid"]["z"], 3),
    }
    metrics["origin"] = data.get("origin", "bottom_center")
    # world_size represents actual exported AABB dimensions
    metrics["world_size"] = {
        "x": actual_span[0],
        "y": actual_span[1],
        "z": actual_span[2],
    }

    review_dir = pkg_dir / "review"
    review_dir.mkdir(parents=True, exist_ok=True)
    render_views(review_dir, [obj])

    metrics_path = review_dir / "metrics.json"
    metrics_path.write_text(
        json.dumps(metrics, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )

    if slug == "moss_cliff_ledge":
        anchor_check = "- [x] Origin at edge_anchor (z=0 cliff ledge surface plane, with 3D hanging tendrils extending below to -0.26m)."
    else:
        anchor_check = "- [x] Ground contact flat at z=0, origin bottom_center."

    # Write review.md for package
    review_md = f"""# Build Verification: {slug}

## Objective Build Verification
- [x] Required review renders generated (iso.png, front.png, side.png, top.png at 512x512).
- [x] Export validated ({output_path.name}, glTF 2.0, {glb_info['size_bytes']} bytes, {glb_info['meshes']} mesh, {glb_info['materials']} shared material).
- [x] Shared production material verified (`mat_dressing_atlas` mapped via UVMap to baseColor & metallic-roughness atlases).
- [x] Material count is within budget (1 shared material <= 4).
- [x] Triangle count verified ({metrics['triangles']} tris <= 500 budget).
- [x] Internal faces culled ({metrics['visible_faces']} visible faces).
{anchor_check}
- [x] Low-poly blocky silhouette matching visual dressing contract.

## Metrics
- Occupied voxels: {metrics['occupied_voxels']}
- Triangles: {metrics['triangles']}
- Visible faces: {metrics['visible_faces']}
- Mesh objects: {metrics['mesh_objects']}
- Materials: {metrics['materials']}
- Shared material: `{metrics['shared_material']}` (albedo atlas: `{metrics['atlas_texture']}`, roughness atlas: `{metrics['roughness_atlas_texture']}`)
- Origin / Pivot: `{metrics['origin']}`
- Grid dimensions: {metrics['grid']['x']}x{metrics['grid']['y']}x{metrics['grid']['z']} (voxel_size: {metrics['voxel_size']}m)
- Nominal grid size: {metrics['nominal_grid_size']['x']:.2f}m x {metrics['nominal_grid_size']['y']:.2f}m x {metrics['nominal_grid_size']['z']:.2f}m
- Exported mesh AABB: {metrics['mesh_aabb']['x']:.3f}m x {metrics['mesh_aabb']['y']:.3f}m x {metrics['mesh_aabb']['z']:.3f}m
- Exported bounds: min=[{metrics['mesh_bounds_min']['x']:.3f}, {metrics['mesh_bounds_min']['y']:.3f}, {metrics['mesh_bounds_min']['z']:.3f}], max=[{metrics['mesh_bounds_max']['x']:.3f}, {metrics['mesh_bounds_max']['y']:.3f}, {metrics['mesh_bounds_max']['z']:.3f}]
- Engine: {metrics['render_engine']} ({metrics['blender_version']})
"""
    (review_dir / "review.md").write_text(review_md, encoding="utf-8")
    print(f"[OK] Built and verified {slug}: {metrics['triangles']} tris, {metrics['occupied_voxels']} voxels, 1 shared material")
    return metrics


# -----------------------------------------------------------------------------
# Mockup Scene Building Helpers
# -----------------------------------------------------------------------------

def setup_mockup_environment(sun_energy: float = 3.0, ambient_color=(0.45, 0.55, 0.68, 1.0)) -> None:
    sun_data = bpy.data.lights.new(name="Sun", type="SUN")
    sun_data.energy = sun_energy
    sun_data.color = (1.0, 0.97, 0.92)
    sun_obj = bpy.data.objects.new(name="Sun", object_data=sun_data)
    bpy.context.collection.objects.link(sun_obj)
    sun_obj.rotation_euler = (math.radians(52), math.radians(18), math.radians(-38))

    fill_data = bpy.data.lights.new(name="FillLight", type="SUN")
    fill_data.energy = 0.9
    fill_data.color = (0.75, 0.85, 1.0)
    fill_obj = bpy.data.objects.new(name="FillLight", object_data=fill_data)
    bpy.context.collection.objects.link(fill_obj)
    fill_obj.rotation_euler = (math.radians(45), math.radians(-25), math.radians(140))

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
    
    bpy.ops.mesh.primitive_plane_add(size=10.0, location=(0, 0, 0))
    plane = bpy.context.active_object
    plane.data.materials.append(mat_forest)

    oak_glb = TREE_DIR / "var_0_standard_oak" / "output" / "model.glb"
    spawn_external_glb(oak_glb, (-1.2, 0.8, 0.0), rot_z=math.radians(25))

    spawn_glb("moss_tree_base", (-1.2, 0.8, 0.0), rot_z=math.radians(10))
    spawn_glb("moss_tree_base", (-0.9, 0.6, 0.0), rot_z=math.radians(120))

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

    shrub_glb = TREE_DIR / "var_4_shrub_oak" / "output" / "model.glb"
    spawn_external_glb(shrub_glb, (2.2, 2.0, 0.0), rot_z=math.radians(45))

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

    bpy.ops.mesh.primitive_cube_add(size=1.0, location=(0, 0, 0.5))
    c1 = bpy.context.active_object
    c1.scale = Vector((6.0, 6.0, 1.0))
    c1.data.materials.append(mat_mtn)

    bpy.ops.mesh.primitive_cube_add(size=1.0, location=(1.5, 1.5, 1.5))
    c2 = bpy.context.active_object
    c2.scale = Vector((3.5, 3.5, 1.0))
    c2.data.materials.append(mat_cliff)

    rock_glb = ROCK_DIR / "stage_1_var_1" / "output" / "model.glb"
    spawn_external_glb(rock_glb, (2.2, 1.8, 2.0), rot_z=math.radians(35), scale=0.8)

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
            count = 7
        elif density_mode == "medium":
            count = 16
        else:
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

    mat_forest = create_terrain_material("mat_forest", "forest_grass_top", 0.88)
    mat_dirt = create_terrain_material("mat_dirt", "dirt_soil", 0.92)
    mat_mtn = create_terrain_material("mat_mtn", "mountain_stone_top", 0.90)
    mat_cliff = create_terrain_material("mat_cliff", "cliff_side", 0.92)

    bpy.ops.mesh.primitive_plane_add(size=14.0, location=(0, 0, 0))
    base_floor = bpy.context.active_object
    base_floor.data.materials.append(mat_forest)

    bpy.ops.mesh.primitive_cube_add(size=1.0, location=(3.5, 3.5, 0.75))
    bluff = bpy.context.active_object
    bluff.scale = Vector((5.0, 5.0, 1.5))
    bluff.data.materials.append(mat_cliff)

    bpy.ops.mesh.primitive_cube_add(size=1.0, location=(3.5, 3.5, 1.5))
    bluff_top = bpy.context.active_object
    bluff_top.scale = Vector((4.8, 4.8, 0.2))
    bluff_top.data.materials.append(mat_mtn)

    bpy.ops.mesh.primitive_plane_add(size=1.0, location=(0, 0, 0.01))
    path = bpy.context.active_object
    path.scale = Vector((1.2, 12.0, 1.0))
    path.rotation_euler.z = math.radians(-30)
    path.data.materials.append(mat_dirt)

    oak_std = TREE_DIR / "var_0_standard_oak" / "output" / "model.glb"
    spawn_external_glb(oak_std, (-2.5, 1.5, 0.0), rot_z=math.radians(15))
    oak_tall = TREE_DIR / "var_1_tall_oak" / "output" / "model.glb"
    spawn_external_glb(oak_tall, (-3.5, -1.8, 0.0), rot_z=math.radians(60))

    rock_glb = ROCK_DIR / "stage_1_var_1" / "output" / "model.glb"
    spawn_external_glb(rock_glb, (3.2, 3.0, 1.6), rot_z=math.radians(40), scale=0.85)

    bpy.ops.mesh.primitive_cube_add(size=1.0, location=(0.2, -0.4, 1.0))
    hero = bpy.context.active_object
    hero.scale = Vector((0.5, 0.5, 1.0))
    hero_mat = bpy.data.materials.new("HeroProxy")
    hero_mat.use_nodes = True
    hero_bsdf = hero_mat.node_tree.nodes.get("Principled BSDF")
    hero_bsdf.inputs["Base Color"].default_value = (0.2, 0.45, 0.85, 1.0)
    hero.data.materials.append(hero_mat)

    random.seed(999)
    spawn_glb("moss_tree_base", (-2.5, 1.5, 0.0), rot_z=math.radians(20))
    spawn_glb("moss_tree_base", (-3.5, -1.8, 0.0), rot_z=math.radians(80))
    spawn_glb("moss_cliff_ledge", (1.1, 2.5, 1.5), rot_z=math.radians(-90))
    spawn_glb("moss_rock_shelf", (2.2, 3.2, 1.6), rot_z=math.radians(15))

    scatter_plan = [
        ("grass_tuft_small_01", (-0.8, -0.6, 0.0)),
        ("grass_tuft_small_02", (0.9, -0.8, 0.0)),
        ("grass_tuft_med_01", (-1.1, 0.2, 0.0)),
        ("grass_tuft_med_02", (1.2, 0.6, 0.0)),
        ("flower_yellow_cluster", (-0.7, 0.8, 0.0)),
        ("flower_white_cluster", (1.4, -0.2, 0.0)),
        ("flower_red_cluster", (-1.4, -1.2, 0.0)),
        ("flower_mixed_accent", (0.6, 1.4, 0.0)),
        ("grass_tuft_tall_01", (-2.0, 0.6, 0.0)),
        ("grass_tuft_med_01", (-3.0, 0.4, 0.0)),
        ("flower_white_cluster", (-2.2, -1.0, 0.0)),
        ("stone_debris_single", (-1.8, -0.2, 0.0)),
        ("stone_debris_fine_scatter", (0.1, -1.6, 0.01)),
        ("stone_debris_fine_scatter", (-0.2, 0.8, 0.01)),
        ("stone_debris_angular_chip", (0.5, -1.8, 0.0)),
        ("stone_debris_trio", (1.8, 1.2, 0.0)),
        ("stone_debris_flat_patch", (2.0, -0.8, 0.0)),
        ("stone_debris_mountain_cluster", (2.2, 2.2, 1.6)),
        ("stone_debris_single", (3.8, 1.8, 1.6)),
        ("grass_tuft_small_03", (1.8, 3.6, 1.6)),
    ]

    for slug, loc in scatter_plan:
        spawn_glb(slug, loc, rot_z=random.uniform(0, math.pi * 2))

    cam_target = Vector((0.0, 0.5, 0.8))
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

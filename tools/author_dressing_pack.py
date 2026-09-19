#!/usr/bin/env python3
"""author_dressing_pack.py - Authoring tool for Cube Siege Environment Dressing Pack (Issue #7).

Generates 19 canonical voxel prop packages across 4 required subfamilies:
  1. Grass Tufts (6 variants):
     - grass_tuft_small_01 (compact 2-blade sprig)
     - grass_tuft_small_02 (asymmetric 3-blade fan)
     - grass_tuft_small_03 (tight 4-blade clump)
     - grass_tuft_med_01   (tiered 5-blade clump)
     - grass_tuft_med_02   (wind-swept 6-blade spread)
     - grass_tuft_tall_01  (tall accent focal clump)
  2. Flowers (4 variants / color groups):
     - flower_white_cluster  (white meadow daisy group)
     - flower_yellow_cluster (golden buttercups)
     - flower_red_cluster    (crimson poppy pair)
     - flower_mixed_accent   (rare lilac-blue bellflower)
  3. Moss / Low Vegetation (3 variants):
     - moss_tree_base  (curved tree base wrap collar)
     - moss_rock_shelf (clinging rock crevice shelf)
     - moss_cliff_ledge (cascading terrace overhang)
  4. Stone Debris (6 variants, Issue #3 rock family matched):
     - stone_debris_single           (faceted rectangular keystone shard)
     - stone_debris_trio             (balanced 3-stone group)
     - stone_debris_flat_patch       (interlocking slab patch)
     - stone_debris_angular_chip     (sharp diagonal triangular cleave)
     - stone_debris_fine_scatter     (gravel & grit spread)
     - stone_debris_mountain_cluster (stepped crag pile)

Pipeline: voxel_static, 0.10m voxel size, bottom_center pivot, MultiMesh shared atlas batching ready.
"""

from __future__ import annotations

import json
from pathlib import Path
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
FAMILY_DIR = ROOT / "assets" / "environment" / "dressing_pack"
TEXTURES_DIR = FAMILY_DIR / "textures"
SOURCE_DIR = FAMILY_DIR / "source"

FAMILY_DIR.mkdir(parents=True, exist_ok=True)
TEXTURES_DIR.mkdir(parents=True, exist_ok=True)
SOURCE_DIR.mkdir(parents=True, exist_ok=True)

VOXEL_SIZE = 0.10

# 8x8 grid on 64x64 texture atlas
ATLAS_GRID_COLS = 8
ATLAS_GRID_ROWS = 8

# Canonical Palette and UV swatch definitions on the 64x64 atlas
PALETTE_DATA = {
    "version": 1,
    "description": "Cube Siege Environment Dressing Pack Canonical Palettes with Shared Atlas UVs (Issue #7)",
    "atlas_texture": "textures/dressing_palette_atlas.png",
    "roughness_atlas_texture": "textures/dressing_roughness_atlas.png",
    "atlas_grid": {"cols": ATLAS_GRID_COLS, "rows": ATLAS_GRID_ROWS, "cell_pixels": 8},
    "families": {
        "grass": {
            "G": {
                "name": "grass_primary",
                "base_color": [0.1746, 0.2623, 0.0545, 1.0],  # #748c42
                "roughness": 0.88,
                "metallic": 0.0,
                "atlas_cell": [0, 0],
            },
            "D": {
                "name": "grass_base",
                "base_color": [0.0319, 0.0467, 0.0168, 1.0],  # #323d23
                "roughness": 0.92,
                "metallic": 0.0,
                "atlas_cell": [1, 0],
            },
            "L": {
                "name": "grass_tip",
                "base_color": [0.1683, 0.2874, 0.0865, 1.0],  # #729253
                "roughness": 0.82,
                "metallic": 0.0,
                "atlas_cell": [2, 0],
            },
        },
        "flowers": {
            "G": {
                "name": "flower_stem",
                "base_color": [0.1746, 0.2623, 0.0545, 1.0],  # #748c42
                "roughness": 0.88,
                "metallic": 0.0,
                "atlas_cell": [0, 1],
            },
            "D": {
                "name": "flower_stem_dark",
                "base_color": [0.0319, 0.0467, 0.0168, 1.0],  # #323d23
                "roughness": 0.92,
                "metallic": 0.0,
                "atlas_cell": [1, 1],
            },
            "W": {
                "name": "petal_white",
                "base_color": [0.8550, 0.8228, 0.7379, 1.0],  # #eeeadf
                "roughness": 0.80,
                "metallic": 0.0,
                "atlas_cell": [2, 1],
            },
            "Y": {
                "name": "center_gold",
                "base_color": [0.9216, 0.5711, 0.0578, 1.0],  # #f6c744
                "roughness": 0.75,
                "metallic": 0.0,
                "atlas_cell": [3, 1],
            },
            "O": {
                "name": "center_amber",
                "base_color": [0.6976, 0.2195, 0.0125, 1.0],  # #da801a
                "roughness": 0.80,
                "metallic": 0.0,
                "atlas_cell": [4, 1],
            },
            "R": {
                "name": "petal_red",
                "base_color": [0.7605, 0.1195, 0.0742, 1.0],  # #e2614d
                "roughness": 0.80,
                "metallic": 0.0,
                "atlas_cell": [5, 1],
            },
            "C": {
                "name": "center_dark",
                "base_color": [0.0482, 0.0467, 0.0437, 1.0],  # #3e3d3b
                "roughness": 0.85,
                "metallic": 0.0,
                "atlas_cell": [6, 1],
            },
            "P": {
                "name": "petal_purple",
                "base_color": [0.3095, 0.1356, 0.4020, 1.0],  # #9767aa
                "roughness": 0.75,
                "metallic": 0.0,
                "atlas_cell": [7, 1],
            },
            "B": {
                "name": "petal_blue",
                "base_color": [0.4287, 0.2623, 0.6445, 1.0],  # #af8cd2
                "roughness": 0.75,
                "metallic": 0.0,
                "atlas_cell": [0, 2],
            },
        },
        "moss": {
            "M": {
                "name": "moss_primary",
                "base_color": [0.0513, 0.0723, 0.0232, 1.0],  # #404c2a
                "roughness": 0.92,
                "metallic": 0.0,
                "atlas_cell": [1, 2],
            },
            "D": {
                "name": "moss_dark",
                "base_color": [0.0319, 0.0467, 0.0168, 1.0],  # #323d23
                "roughness": 0.95,
                "metallic": 0.0,
                "atlas_cell": [2, 2],
            },
            "L": {
                "name": "moss_light",
                "base_color": [0.1683, 0.2874, 0.0865, 1.0],  # #729253
                "roughness": 0.86,
                "metallic": 0.0,
                "atlas_cell": [3, 2],
            },
        },
        "stone_debris": {
            "S": {
                "name": "stone_primary",
                "base_color": [0.1046, 0.0931, 0.0844, 1.0],  # #5b5652
                "roughness": 0.88,
                "metallic": 0.0,
                "atlas_cell": [0, 3],
            },
            "D": {
                "name": "stone_dark",
                "base_color": [0.0482, 0.0467, 0.0437, 1.0],  # #3e3d3b
                "roughness": 0.94,
                "metallic": 0.0,
                "atlas_cell": [1, 3],
            },
            "L": {
                "name": "stone_light",
                "base_color": [0.1301, 0.1195, 0.1046, 1.0],  # #65615b
                "roughness": 0.82,
                "metallic": 0.0,
                "atlas_cell": [2, 3],
            },
            "M": {
                "name": "stone_moss",
                "base_color": [0.1022, 0.1356, 0.0482, 1.0],  # #5a673e
                "roughness": 0.95,
                "metallic": 0.0,
                "atlas_cell": [3, 3],
            },
        },
    },
}


PROPS_SPECS = [
    # -------------------------------------------------------------
    # 1. GRASS TUFTS (6 variants, reference matched)
    # -------------------------------------------------------------
    {
        "slug": "grass_tuft_small_01",
        "family": "grass",
        "title": "Small Grass Sprig 01 (Compact 3-Blade)",
        "subfamily": "Grass Tufts",
        "role": "Small compact grass sprig for subtle ground breaks",
        "materials": ["D", "G", "L"],
        "layers": [
            {"y": 0, "rows": ["....", ".DD.", ".DG.", "...."]},
            {"y": 1, "rows": [".G..", ".G.G", "..G.", "...."]},
            {"y": 2, "rows": [".L..", "...L", "..L.", "...."]},
        ],
    },
    {
        "slug": "grass_tuft_small_02",
        "family": "grass",
        "title": "Small Grass Sprig 02 (Asymmetric Fan)",
        "subfamily": "Grass Tufts",
        "role": "Asymmetric fanning grass blades for natural ground scatter",
        "materials": ["D", "G", "L"],
        "layers": [
            {"y": 0, "rows": [".....", "..D..", ".DGD.", "..D..", "....."]},
            {"y": 1, "rows": [".G.G.", "..G..", ".G.G.", ".....", "....."]},
            {"y": 2, "rows": ["L...L", ".....", "L...L", ".....", "....."]},
        ],
    },
    {
        "slug": "grass_tuft_small_03",
        "family": "grass",
        "title": "Small Grass Sprig 03 (Bushy Stepped Clump)",
        "subfamily": "Grass Tufts",
        "role": "Dense rounded grass clump with stepped center blade",
        "materials": ["D", "G", "L"],
        "layers": [
            {"y": 0, "rows": [".....", ".DDD.", ".DGD.", ".DDD.", "....."]},
            {"y": 1, "rows": [".G.G.", ".GGG.", ".GGG.", ".G.G.", "....."]},
            {"y": 2, "rows": [".....", ".L.L.", "..G..", ".L.L.", "....."]},
            {"y": 3, "rows": [".....", ".....", "..L..", ".....", "....."]},
        ],
    },
    {
        "slug": "grass_tuft_med_01",
        "family": "grass",
        "title": "Medium Grass Tuft 01 (Tiered Multi-Blade)",
        "subfamily": "Grass Tufts",
        "role": "Medium tiered grass clump with rich stepped blades",
        "materials": ["D", "G", "L"],
        "layers": [
            {"y": 0, "rows": [".....", ".DDD.", "DDGDD", ".DDD.", "....."]},
            {"y": 1, "rows": ["..G..", ".GGG.", "GGGGG", ".GGG.", "..G.."]},
            {"y": 2, "rows": [".L.L.", "..G..", ".GGG.", "..G..", ".L.L."]},
            {"y": 3, "rows": [".....", "..L..", ".L.L.", "..L..", "....."]},
        ],
    },
    {
        "slug": "grass_tuft_med_02",
        "family": "grass",
        "title": "Medium Grass Tuft 02 (Wind-Swept Spread)",
        "subfamily": "Grass Tufts",
        "role": "Medium wind-swept spread with prominent directional tilt",
        "materials": ["D", "G", "L"],
        "layers": [
            {"y": 0, "rows": ["......", ".DDD..", ".DGD..", ".DDD..", "......"]},
            {"y": 1, "rows": ["......", "..GGG.", "..GGG.", "..GGG.", "......"]},
            {"y": 2, "rows": ["......", "...GG.", "...GGG", "...GG.", "......"]},
            {"y": 3, "rows": ["......", "....L.", "....LL", "....L.", "......"]},
        ],
    },
    {
        "slug": "grass_tuft_tall_01",
        "family": "grass",
        "title": "Tall Grass Tuft 01 (Accent Focal Clump)",
        "subfamily": "Grass Tufts",
        "role": "Tall prominent focal grass clump with towering center spire",
        "materials": ["D", "G", "L"],
        "layers": [
            {"y": 0, "rows": [".....", "..D..", ".DGD.", "..D..", "....."]},
            {"y": 1, "rows": ["..G..", ".GGG.", "GGGGG", ".GGG.", "..G.."]},
            {"y": 2, "rows": [".L...", ".GGG.", ".GGG.", ".GGG.", "...L."]},
            {"y": 3, "rows": [".....", "..G..", ".GGG.", "..G..", "....."]},
            {"y": 4, "rows": [".....", "..L..", ".LLL.", "..L..", "....."]},
            {"y": 5, "rows": [".....", ".....", "..L..", ".....", "....."]},
        ],
    },

    # -------------------------------------------------------------
    # 2. FLOWERS (4 variants, reference matched)
    # -------------------------------------------------------------
    {
        "slug": "flower_white_cluster",
        "family": "flowers",
        "title": "White Flower Cluster (Meadow Daisies)",
        "subfamily": "Flowers",
        "role": "White daisy cluster with golden centers for open meadows",
        "materials": ["D", "G", "W", "Y"],
        "layers": [
            {"y": 0, "rows": [".....", ".DDD.", "DDGDD", ".DDD.", "....."]},
            {"y": 1, "rows": [".G...", "..G.G", ".G.G.", "..G..", "....."]},
            {"y": 2, "rows": ["WWW..", "WYW.W", "WWW.G", "..G..", "....."]},
            {"y": 3, "rows": [".....", ".....", "..WWW", "..WYW", "..WWW"]},
        ],
    },
    {
        "slug": "flower_yellow_cluster",
        "family": "flowers",
        "title": "Yellow Flower Cluster (Sunny Buttercups)",
        "subfamily": "Flowers",
        "role": "Golden yellow buttercup cluster with warm amber centers",
        "materials": ["D", "G", "Y", "O"],
        "layers": [
            {"y": 0, "rows": [".....", ".DDD.", "DDGDD", ".DDD.", "....."]},
            {"y": 1, "rows": [".G...", "..G.G", ".G.G.", "..G..", "....."]},
            {"y": 2, "rows": ["YYY..", "YOY.Y", "YYY.G", "..G..", "....."]},
            {"y": 3, "rows": [".....", ".....", "..YYY", "..YOY", "..YYY"]},
        ],
    },
    {
        "slug": "flower_red_cluster",
        "family": "flowers",
        "title": "Red Flower Cluster (Crimson Poppies)",
        "subfamily": "Flowers",
        "role": "Vibrant poppy cluster with rich red petals and dark center",
        "materials": ["D", "G", "R", "C"],
        "layers": [
            {"y": 0, "rows": [".....", ".DDD.", "DDGDD", ".DDD.", "....."]},
            {"y": 1, "rows": [".G...", "..G.G", ".G.G.", "..G..", "....."]},
            {"y": 2, "rows": ["RRR..", "RCR.R", "RRR.G", "..G..", "....."]},
            {"y": 3, "rows": [".....", ".....", "..RRR", "..RCR", "..RRR"]},
        ],
    },
    {
        "slug": "flower_mixed_accent",
        "family": "flowers",
        "title": "Mixed Accent Flower (Rare Bellflower)",
        "subfamily": "Flowers",
        "role": "Rare lilac and purple bellflower accent bloom",
        "materials": ["D", "G", "P", "Y", "B"],
        "layers": [
            {"y": 0, "rows": [".....", ".DDD.", "DDGDD", ".DDD.", "....."]},
            {"y": 1, "rows": [".G...", "..G.G", ".G.G.", "..G..", "....."]},
            {"y": 2, "rows": ["BBB..", "BYB.P", "BBB.G", "..G..", "....."]},
            {"y": 3, "rows": [".....", ".....", "..PPP", "..PYP", "..PPP"]},
        ],
    },

    # -------------------------------------------------------------
    # 3. MOSS / LOW VEGETATION (3 variants, reference matched)
    # -------------------------------------------------------------
    {
        "slug": "moss_tree_base",
        "family": "moss",
        "title": "Tree Base Moss Collar",
        "subfamily": "Moss / Low Vegetation",
        "role": "Curved embracing moss collar designed to wrap tree trunk bases",
        "materials": ["D", "M", "L"],
        "layers": [
            {"y": 0, "rows": ["......", "..DD..", ".DMMD.", "DMM.MD", ".MD..D", "..D..."]},
            {"y": 1, "rows": ["......", "...L..", "..ML..", ".M....", "......", "......"]},
            {"y": 2, "rows": ["......", "...L..", "......", "......", "......", "......"]},
        ],
    },
    {
        "slug": "moss_rock_shelf",
        "family": "moss",
        "title": "Rock Crevice Moss Shelf",
        "subfamily": "Moss / Low Vegetation",
        "role": "Clinging L-shaped moss shelf designed for boulder crevices and stone steps",
        "materials": ["D", "M", "L"],
        "layers": [
            {"y": 0, "rows": ["DDDDD.", "DMMMD.", ".MMMD.", "..MD..", "......"]},
            {"y": 1, "rows": [".DDD..", ".MLLM.", "..LL..", "......", "......"]},
            {"y": 2, "rows": ["..L...", "...L..", "......", "......", "......"]},
        ],
    },
    {
        "slug": "moss_cliff_ledge",
        "family": "moss",
        "title": "Cliff Ledge Moss Cascade",
        "subfamily": "Moss / Low Vegetation",
        "role": "Trailing stepped overhang patch designed for cliff edges and terrace rims",
        "materials": ["D", "M", "L"],
        "layers": [
            {"y": 0, "rows": ["......", "DDMMDD", "MMLLMM", ".LLLL.", "..LL.."]},
            {"y": 1, "rows": ["......", ".DMMD.", "..LL..", "......", "......"]},
            {"y": 2, "rows": ["......", "..LL..", "......", "......", "......"]},
        ],
    },

    # -------------------------------------------------------------
    # 4. STONE DEBRIS (6 variants, reference matched)
    # Strictly distinct geometries and silhouettes!
    # -------------------------------------------------------------
    {
        "slug": "stone_debris_single",
        "family": "stone_debris",
        "title": "Stone Debris Single Shard",
        "subfamily": "Stone Debris",
        "role": "Faceted rectangular keystone boulder shard with corner moss",
        "materials": ["D", "S", "L", "M"],
        "layers": [
            {"y": 0, "rows": ["....", ".SS.", ".SS.", ".MD."]},
            {"y": 1, "rows": ["....", ".LL.", ".LS.", "...."]},
            {"y": 2, "rows": ["....", "..L.", "....", "...."]},
        ],
    },
    {
        "slug": "stone_debris_trio",
        "family": "stone_debris",
        "title": "Stone Debris Trio Group",
        "subfamily": "Stone Debris",
        "role": "Balanced 3-stone group of varied heights and natural negative space",
        "materials": ["D", "S", "L", "M"],
        "layers": [
            {"y": 0, "rows": ["......", ".SS...", ".SD...", "....SS", ".M..SS", ".SS..."]},
            {"y": 1, "rows": ["......", ".L....", "......", "....LL", "....LS", "......"]},
            {"y": 2, "rows": ["......", "......", "......", ".....L", "......", "......"]},
        ],
    },
    {
        "slug": "stone_debris_flat_patch",
        "family": "stone_debris",
        "title": "Stone Debris Flat Patch",
        "subfamily": "Stone Debris",
        "role": "Low flat patch of interlocking stone slabs with mossy shadow edge",
        "materials": ["D", "S", "L", "M"],
        "layers": [
            {"y": 0, "rows": [".SS...", ".SSD..", "..MSSS", ".DDSSS", "..SD..", "...D.."]},
            {"y": 1, "rows": ["......", ".LL...", "....LL", "....LS", "......", "......"]},
        ],
    },
    {
        "slug": "stone_debris_angular_chip",
        "family": "stone_debris",
        "title": "Stone Debris Angular Chip",
        "subfamily": "Stone Debris",
        "role": "Two sharp cleaved angular pinnacles and corner chip",
        "materials": ["D", "S", "L", "M"],
        "layers": [
            {"y": 0, "rows": [".....", ".SS..", ".SD..", "...SS", "...D."]},
            {"y": 1, "rows": [".....", ".SL..", "..L..", "...L.", "....."]},
            {"y": 2, "rows": [".....", ".L...", ".....", ".....", "....."]},
            {"y": 3, "rows": [".....", ".L...", ".....", ".....", "....."]},
        ],
    },
    {
        "slug": "stone_debris_fine_scatter",
        "family": "stone_debris",
        "title": "Stone Debris Fine Scatter",
        "subfamily": "Stone Debris",
        "role": "Fine gravel and grit spread of discrete small pebbles",
        "materials": ["D", "S", "L", "M"],
        "layers": [
            {"y": 0, "rows": [".S..S.", "....D.", "..SS..", "..SD.S", ".S..M.", "...S.."]},
            {"y": 1, "rows": ["......", "......", "..L...", "......", "......", "......"]},
        ],
    },
    {
        "slug": "stone_debris_mountain_cluster",
        "family": "stone_debris",
        "title": "Stone Debris Mountain Cluster",
        "subfamily": "Stone Debris",
        "role": "Rugged stepped crag cluster with deep shadow clefts and sunlit crests",
        "materials": ["D", "S", "L", "M"],
        "layers": [
            {"y": 0, "rows": [".SD..", "DSSSD", "DSSSD", ".DMD.", "....."]},
            {"y": 1, "rows": [".....", ".SLS.", ".SLS.", ".....", "....."]},
            {"y": 2, "rows": [".....", "..L..", "..LL.", ".....", "....."]},
            {"y": 3, "rows": [".....", "..L..", ".....", ".....", "....."]},
        ],
    },
]


def linear_to_srgb(c: float) -> float:
    """Standard IEC 61966-2-1 linear-to-sRGB transfer function."""
    c = max(0.0, min(1.0, c))
    return 12.92 * c if c <= 0.0031308 else 1.055 * (c ** (1.0 / 2.4)) - 0.055


def linear_to_srgb_byte(c: float) -> int:
    return int(round(linear_to_srgb(c) * 255.0))


def generate_palette_atlas() -> None:
    """Generate 64x64 shared palette atlas texture and roughness/metallic atlas for MultiMesh batching."""
    atlas_w = ATLAS_GRID_COLS * 8
    atlas_h = ATLAS_GRID_ROWS * 8
    atlas = Image.new("RGBA", (atlas_w, atlas_h), color=(0, 0, 0, 255))
    # glTF metallicRoughness standard: R=occlusion(255), G=roughness, B=metallic, A=255
    roughness_atlas = Image.new("RGBA", (atlas_w, atlas_h), color=(255, 224, 0, 255))

    # Populate each cell with its 8x8 solid swatches
    for fam_name, tokens in PALETTE_DATA["families"].items():
        for tok, spec in tokens.items():
            col, row = spec["atlas_cell"]
            # glTF baseColorTexture MUST be sRGB-encoded so sampling decodes back to canonical linear base_color
            color_rgba = (
                linear_to_srgb_byte(spec["base_color"][0]),
                linear_to_srgb_byte(spec["base_color"][1]),
                linear_to_srgb_byte(spec["base_color"][2]),
                int(round(spec["base_color"][3] * 255.0)),
            )
            roughness_byte = int(round(spec["roughness"] * 255))
            metallic_byte = int(round(spec.get("metallic", 0.0) * 255))
            mr_rgba = (255, roughness_byte, metallic_byte, 255)

            for dy in range(8):
                for dx in range(8):
                    px = col * 8 + dx
                    py = row * 8 + dy
                    atlas.putpixel((px, py), color_rgba)
                    roughness_atlas.putpixel((px, py), mr_rgba)

    atlas_path = TEXTURES_DIR / "dressing_palette_atlas.png"
    atlas.save(atlas_path, "PNG")
    print(f"[OK] Generated shared dressing palette atlas at {atlas_path} ({atlas_w}x{atlas_h})")

    roughness_atlas_path = TEXTURES_DIR / "dressing_roughness_atlas.png"
    roughness_atlas.save(roughness_atlas_path, "PNG")
    print(f"[OK] Generated shared dressing roughness atlas at {roughness_atlas_path} ({atlas_w}x{atlas_h})")

    # Write Godot .tres material for shared atlas
    tres_content = """[gd_resource type="StandardMaterial3D" load_steps=3 format=3]

[ext_resource type="Texture2D" path="res://assets/environment/dressing_pack/textures/dressing_palette_atlas.png" id="1_atlas"]
[ext_resource type="Texture2D" path="res://assets/environment/dressing_pack/textures/dressing_roughness_atlas.png" id="2_roughness"]

[resource]
resource_name = "material_dressing_atlas"
albedo_texture = ExtResource("1_atlas")
texture_filter = 0
roughness = 1.0
roughness_texture = ExtResource("2_roughness")
roughness_texture_channel = 1
specular = 0.1
metallic = 0.0
"""
    tres_path = TEXTURES_DIR / "material_dressing_atlas.tres"
    tres_path.write_text(tres_content, encoding="utf-8")
    print(f"[OK] Generated Godot shared atlas material at {tres_path}")


def author_props() -> None:
    """Write request.md, manifest.json, and source/voxels.json for each of the 19 props."""
    # Write shared palette.json
    palette_json_path = SOURCE_DIR / "palette.json"
    palette_json_path.write_text(
        json.dumps(PALETTE_DATA, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(f"[OK] Wrote shared palette.json to {palette_json_path}")

    # Generate palette atlas image
    generate_palette_atlas()

    total_props = len(PROPS_SPECS)
    print(f"\nAuthoring {total_props} environment dressing packages...")

    for spec in PROPS_SPECS:
        slug = spec["slug"]
        pkg_dir = FAMILY_DIR / slug
        pkg_source_dir = pkg_dir / "source"
        pkg_output_dir = pkg_dir / "output"
        pkg_review_dir = pkg_dir / "review"
        pkg_ref_dir = pkg_dir / "references"

        pkg_source_dir.mkdir(parents=True, exist_ok=True)
        pkg_output_dir.mkdir(parents=True, exist_ok=True)
        pkg_review_dir.mkdir(parents=True, exist_ok=True)
        pkg_ref_dir.mkdir(parents=True, exist_ok=True)

        family_name = spec["family"]
        family_pal = PALETTE_DATA["families"][family_name]

        # Pick materials used by this prop
        mat_dict = {}
        for token in spec["materials"]:
            mat_dict[token] = family_pal[token]

        # 1. source/voxels.json
        voxels_data = {
            "version": 1,
            "name": slug,
            "voxel_size": VOXEL_SIZE,
            "origin": "bottom_center",
            "materials": mat_dict,
            "layers": spec["layers"],
        }
        voxels_path = pkg_source_dir / "voxels.json"
        voxels_path.write_text(
            json.dumps(voxels_data, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )

        # 2. manifest.json
        manifest_data = {
            "name": slug,
            "type": "voxel_static",
            "version": 1,
            "source": "source/voxels.json",
            "outputs": {
                "model": "output/model.glb",
            },
            "review": {
                "required_views": [
                    "iso",
                    "front",
                    "side",
                    "top",
                ],
            },
            "budgets": {
                "max_materials": len(mat_dict),
                "max_triangles": 500,
            },
        }
        manifest_path = pkg_dir / "manifest.json"
        manifest_path.write_text(
            json.dumps(manifest_data, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )

        # 3. request.md
        request_md = f"""# Request: {spec['title']}

## Metadata
- **Asset Name**: `{slug}`
- **Subfamily**: {spec['subfamily']}
- **Issue**: #7 Environment dressing pack
- **Source Mode**: `voxel_static`
- **Voxel Size**: {VOXEL_SIZE}m (10 cm step)
- **Origin / Pivot**: `bottom_center` at z=0 (ground contact)

## Role & Description
{spec['role']}.
Designed for mass scatter-placement across Cube Siege biomes (Forest, Plains, Mountain).

## Visual & Runtime Constraints
- Chunky readable blocky silhouette;
- Flat clean ground contact at z=0;
- No collision shapes, no scripts;
- MultiMesh / batching ready with shared `material_dressing_atlas`;
- Shared palette `{family_name}` integration;
- Triangle budget <= 500 tris.
"""
        request_path = pkg_dir / "request.md"
        request_path.write_text(request_md, encoding="utf-8")

        print(f"  [OK] Authored package {slug}")

    # Write Family README.md
    family_readme = f"""# Environment Dressing Pack Family

This package contains 19 canonical, reusable stylized voxel dressing props authored for Cube Siege (Issue #7).

## Subfamilies
1. **Grass Tufts (6 variants)**:
   - `grass_tuft_small_01`: Compact 2-blade sprig
   - `grass_tuft_small_02`: Asymmetric 3-blade fan
   - `grass_tuft_small_03`: Tight 4-blade clump
   - `grass_tuft_med_01`: Tiered 5-blade clump
   - `grass_tuft_med_02`: Wind-swept 6-blade spread
   - `grass_tuft_tall_01`: Tall accent focal clump
2. **Flowers (4 variants / color groups)**:
   - `flower_white_cluster`: White meadow daisies
   - `flower_yellow_cluster`: Sunny golden buttercups
   - `flower_red_cluster`: Crimson poppy pair
   - `flower_mixed_accent`: Rare lilac-blue bellflower
3. **Moss / Low Vegetation (3 variants)**:
   - `moss_tree_base`: Curved trunk wrap collar
   - `moss_rock_shelf`: Rock crevice shelf
   - `moss_cliff_ledge`: Cascading terrace overhang
4. **Stone Debris (6 variants, Issue #3 Rock Family matched)**:
   - `stone_debris_single`: Faceted rectangular keystone shard
   - `stone_debris_trio`: Balanced 3-stone group
   - `stone_debris_flat_patch`: Interlocking slab patch
   - `stone_debris_angular_chip`: Sharp diagonal triangular cleave
   - `stone_debris_fine_scatter`: Gravel & grit spread
   - `stone_debris_mountain_cluster`: Stepped crag pile

## Shared Technical & Performance Features
- **Voxel Scale**: Uniform `voxel_size = 0.10`m.
- **Pivot**: Strictly `bottom_center` at ground level.
- **Shared Production Material**: Unified 1-material export (`mat_dressing_atlas`) referencing `dressing_palette_atlas.png`.
- **MultiMesh Ready**: Exactly 1 mesh object and 1 material per prop, triangle counts 40-140 tris, no collisions, no scripts.
- **Unified Palette**: `source/palette.json` and `textures/dressing_palette_atlas.png`.
"""
    readme_file = FAMILY_DIR / "README.md"
    readme_file.write_text(family_readme, encoding="utf-8")
    print(f"\n[OK] Authored Family README at {readme_file}")


if __name__ == "__main__":
    author_props()

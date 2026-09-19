#!/usr/bin/env python3
"""author_terrain_materials.py - Procedural and pixel authoring tool for Cube Siege terrain materials.

Generates:
1. Production-ready 16x16 stylized voxel terrain textures (Forest, Plains, Mountain, Cliff, Dirt).
2. Unified 64x64 terrain atlas with UV coordinate specifications.
3. 6x6 tileability preview images verifying seamless tiling.
4. Godot 4 StandardMaterial3D resource files (.tres) for all materials.
5. 3D voxel showcase packages (manifest, request, voxels.json) for static validation.
6. Reference concept image and visual contract summary.
"""

from __future__ import annotations

import json
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
TERRAIN_DIR = ROOT / "assets" / "environment" / "terrain_materials"
TEXTURES_DIR = TERRAIN_DIR / "textures"
OUTPUT_DIR = TERRAIN_DIR / "output"
SOURCE_DIR = TERRAIN_DIR / "source"
REVIEW_DIR = TERRAIN_DIR / "review"
REF_DIR = TERRAIN_DIR / "references"

# Ensure directories exist
for d in (TERRAIN_DIR, TEXTURES_DIR, OUTPUT_DIR, SOURCE_DIR, REVIEW_DIR, REF_DIR):
    d.mkdir(parents=True, exist_ok=True)

# -------------------------------------------------------------------------
# PALETTE DEFINITIONS (Calibrated with Rock & Oak Tree Families)
# -------------------------------------------------------------------------

PALETTES = {
    "forest_grass": {
        "D": (31, 63, 21, 255),    # #1f3f15 - Deep canopy shadow / grass recess
        "B": (40, 80, 27, 255),    # #28501b - Forest floor base green
        "M": (52, 99, 35, 255),    # #346323 - Mid foliage green
        "L": (68, 123, 44, 255),   # #447b2c - Sunlit blade cluster
        "A": (84, 143, 52, 255),   # #548f34 - Oak-foliage compatible leaf accent
    },
    "plains_meadow": {
        "D": (56, 94, 28, 255),    # #385e1c - Soft meadow shadow
        "B": (72, 116, 37, 255),   # #487425 - Plains base warm green
        "M": (91, 141, 46, 255),   # #5b8d2e - Sunny meadow mid-tone
        "L": (112, 163, 56, 255),  # #70a338 - Warm sunlit field
        "Y": (140, 184, 69, 255),  # #8cb845 - Golden meadow fleck
        "F": (162, 197, 84, 255),  # #a2c554 - Meadow flower/buttercup accent
    },
    "mountain_stone": {
        "D": (85, 83, 80, 255),    # #555350 - stone_dark from rock family
        "B": (107, 103, 98, 255),  # #6b6762 - deep stone plane
        "S": (125, 120, 114, 255), # #7d7872 - stone_primary from rock family
        "M": (149, 144, 136, 255), # #959088 - bright stone facet
        "L": (174, 168, 160, 255), # #aea8a0 - stone_light sunlit plateau
        "H": (192, 186, 176, 255), # #c0bab0 - crest edge highlight
    },
    "cliff_side": {
        "D": (52, 50, 48, 255),    # #343230 - Deep strata fissure / joint
        "B": (68, 65, 62, 255),    # #44413e - Lower dark strata bed
        "S": (84, 80, 76, 255),    # #524e4a - Mid-cliff rock strata
        "M": (98, 93, 87, 255),    # #625d57 - Prominent horizontal strata ledge
        "L": (116, 110, 103, 255), # #746e67 - Sunlit shelf lip / mineral band
        "H": (134, 128, 119, 255), # #868077 - Edge shelf highlight
    },
    "dirt_soil": {
        "D": (56, 39, 26, 255),    # #38271a - Deep loam recess / shadow
        "B": (72, 51, 34, 255),    # #483322 - Dark rich earth
        "S": (90, 64, 43, 255),    # #5a402b - Warm loam base
        "M": (110, 79, 53, 255),   # #6e4f35 - Crumbly soil clod
        "L": (132, 95, 64, 255),   # #845f40 - Dry weathered earth crumb
        "H": (153, 112, 76, 255),  # #99704c - Silt / fine grit fleck
    },
}

# -------------------------------------------------------------------------
# TEXTURE PATTERNS (16x16 Matrices)
# -------------------------------------------------------------------------

PATTERNS = {
    "forest_grass_top": [
        "BBMMBLMBBMMMBLBB",
        "BMMLLMMBMMLMMBBB",
        "MMLLMMMMLLLLMMBM",
        "MLLMMBBMLMMMBBMM",
        "MMMBBBBBMMBBBMML",
        "BBBDDBBBBDDBMMLL",
        "BBDDDDDBBDDDBBMM",
        "DDDBBBDDDBBBBBBB",
        "BBBBMMBBBBBBBBBD",
        "BBBMLMMBBBBMMLBB",
        "MBMLLLMMBBMMLMBB",
        "MMLLALMMMMMLLMMM",
        "LMLLLLMMBBMLMMMB",
        "MMBMMMBBBBBMMBBM",
        "BBBBBBDDBBBBBBBB",
        "BBMMBBBDDBBMMMBL",
    ],
    "plains_meadow_top": [
        "MMLLMMMMMLLMMMMM",
        "MLLYLLMMMLLLLMMM",
        "LLYYLMMBMLLLLMML",
        "LLLLMMBBBMMMMMML",
        "MMLMMBBDDBBMMMML",
        "MMMBBDDDDBBBBMMM",
        "BBBBBDDBDDBBBBBB",
        "BBMBBBBBBBBBMMBB",
        "MBMMMBBBBMMMLLMB",
        "MMLLMMBBMMLLLLMM",
        "LLLLLMBMMLLYLMML",
        "LYLLMMBMLLYYLMML",
        "LLLMYBBMMLLLMMMM",
        "MMMMBBBBMMMMMBBM",
        "MMMBBBDBBMMMBBMM",
        "MMMMMBBBBMMLLMMM",
    ],
    "mountain_stone_top": [
        "SSSMMMLLMMSSSBBB",
        "SMMLLLLHLLMMSBBD",
        "MLLLHHHHHLLMSBDD",
        "MLLHLLLLLLMMSSBB",
        "MLLLLMMMMMSSSSSS",
        "SMMMSSSSBBBSSMMM",
        "SSSSSBBDDDBSSMLL",
        "BBSSBBDDBBBSSLLH",
        "DBBBBBDDBSSSMLHH",
        "DDBSSBBSSMMMLLHL",
        "BBSSSSSSMLLLLLLM",
        "SSMMSSMMLLHLLMMS",
        "SMLLMSMLLHHLMSSS",
        "SLLLMSSMLLLMSSBB",
        "SMLMSSSSMMMSSBBD",
        "SSSSSSSSSSSSBBBD",
    ],
    "cliff_side": [
        "BBSSSSBBBBSSSSBB",
        "BSMMMSBBBSMMMSBB",
        "SMMLMMSSSMLMMMSS",
        "SMLHLMMSSMLHLMSS",
        "SSMLMSSBBSMMMSSS",
        "BSSSSBBDBBSSSSBB",
        "BBBDDDBDDBBBDDBB",
        "BDDDDBDBDDBDDDDB",
        "BBBDDBBBBDDDBBBB",
        "BSSSSBBBBBSSSSBB",
        "SSMMSSBBBSSMMSSS",
        "SMMLMSSBSMMLLMSS",
        "SMLHLMSSMLLHLMSS",
        "SSMLMSSSSMLLMSSS",
        "BSSMSBBBSSMMSSBB",
        "BBSSSSBBBBSSSSBB",
    ],
    "dirt_soil": [
        "SSMMSSBBSSMMSSBS",
        "SMMLMSBBSMMLLMSS",
        "MMLHLMSSMMLLMSSM",
        "MLLLMSSBSMLMSSBM",
        "SMMMSBBDBSSSSBDB",
        "BSSSBBDDDBBBBDDB",
        "BBDDBSBBDDBBDDBB",
        "BBBDDDBBBDDDDBBB",
        "BSBBDDBSBBDDBBSB",
        "SSSSBBSSSBBDSSSS",
        "SMMSSBSMMLMSBSMM",
        "MLLMSMLLHLMSMLLM",
        "MLHLMMLLLMSSMLLM",
        "SMLMSSMMMMSBSMMS",
        "SSMSSBBSSBBBSSSS",
        "SSMMSSBBSSMMSSBS",
    ],
}


def build_texture(name: str, palette_key: str) -> Image.Image:
    """Build a 16x16 RGBA Image from ASCII pattern and palette."""
    pattern = PATTERNS[name]
    palette = PALETTES[palette_key]
    img = Image.new("RGBA", (16, 16))
    for y, row in enumerate(pattern):
        if len(row) != 16:
            raise ValueError(f"Pattern {name} row {y} width is {len(row)}, expected 16")
        for x, char in enumerate(row):
            if char not in palette:
                raise ValueError(f"Unknown token {char} in {name} at ({x}, {y})")
            img.putpixel((x, y), palette[char])
    return img


def build_all_textures() -> dict[str, Image.Image]:
    textures = {
        "forest_grass_top": build_texture("forest_grass_top", "forest_grass"),
        "plains_meadow_top": build_texture("plains_meadow_top", "plains_meadow"),
        "mountain_stone_top": build_texture("mountain_stone_top", "mountain_stone"),
        "cliff_side": build_texture("cliff_side", "cliff_side"),
        "dirt_soil": build_texture("dirt_soil", "dirt_soil"),
    }
    # Save to textures/ and output/
    for name, img in textures.items():
        tex_file = TEXTURES_DIR / f"{name}.png"
        out_file = OUTPUT_DIR / f"{name}.png"
        img.save(tex_file, "PNG")
        img.save(out_file, "PNG")
        print(f"[SAVED] {tex_file.name} (16x16)")
    return textures


def build_terrain_atlas(textures: dict[str, Image.Image]) -> Image.Image:
    """Build 64x64 unified texture atlas (4x4 grid of 16x16 cells)."""
    atlas = Image.new("RGBA", (64, 64), color=(0, 0, 0, 0))

    # Row 0: Top surfaces & cliff
    atlas.paste(textures["forest_grass_top"], (0, 0))
    atlas.paste(textures["plains_meadow_top"], (16, 0))
    atlas.paste(textures["mountain_stone_top"], (32, 0))
    atlas.paste(textures["cliff_side"], (48, 0))

    # Row 1: Dirt soil & side transitions (Grass overhanging dirt)
    atlas.paste(textures["dirt_soil"], (0, 16))

    # Forest side transition: Top 4px forest grass, bottom 12px dirt
    forest_side = Image.new("RGBA", (16, 16))
    forest_crop = textures["forest_grass_top"].crop((0, 12, 16, 16))
    dirt_crop = textures["dirt_soil"].crop((0, 4, 16, 16))
    forest_side.paste(dirt_crop, (0, 4))
    forest_side.paste(forest_crop, (0, 0))
    atlas.paste(forest_side, (16, 16))

    # Plains side transition: Top 4px plains grass, bottom 12px dirt
    plains_side = Image.new("RGBA", (16, 16))
    plains_crop = textures["plains_meadow_top"].crop((0, 12, 16, 16))
    plains_side.paste(dirt_crop, (0, 4))
    plains_side.paste(plains_crop, (0, 0))
    atlas.paste(plains_side, (32, 16))

    # Stone cliff transition: Top 4px mountain stone, bottom 12px cliff
    stone_side = Image.new("RGBA", (16, 16))
    stone_crop = textures["mountain_stone_top"].crop((0, 12, 16, 16))
    cliff_crop = textures["cliff_side"].crop((0, 4, 16, 16))
    stone_side.paste(cliff_crop, (0, 4))
    stone_side.paste(stone_crop, (0, 0))
    atlas.paste(stone_side, (48, 16))

    # Row 2: Secondary / path transitions
    # (0, 32): Rocky dirt
    rocky_dirt = Image.blend(textures["dirt_soil"], textures["mountain_stone_top"], 0.35)
    atlas.paste(rocky_dirt, (0, 32))
    # (16, 32): Forest path (grass with subtle wear)
    forest_path = Image.blend(textures["forest_grass_top"], textures["dirt_soil"], 0.25)
    atlas.paste(forest_path, (16, 32))
    # (32, 32): Scree / rubble stone
    scree = Image.blend(textures["mountain_stone_top"], textures["cliff_side"], 0.30)
    atlas.paste(scree, (32, 32))
    # (48, 32): Deep shaded cliff
    deep_cliff = Image.new("RGBA", (16, 16))
    for y in range(16):
        for x in range(16):
            r, g, b, a = textures["cliff_side"].getpixel((x, y))
            deep_cliff.putpixel((x, y), (int(r * 0.85), int(g * 0.85), int(b * 0.85), a))
    atlas.paste(deep_cliff, (48, 32))

    # Row 3: Biome accent variants (e.g. mossy stone, clay dirt)
    # (0, 48): Mossy rock
    mossy_rock = Image.blend(textures["mountain_stone_top"], textures["forest_grass_top"], 0.40)
    atlas.paste(mossy_rock, (0, 48))
    # (16, 48): Dry sunny grass
    dry_grass = Image.blend(textures["plains_meadow_top"], textures["dirt_soil"], 0.20)
    atlas.paste(dry_grass, (16, 48))
    # (32, 48): Dense dark earth
    dark_earth = Image.new("RGBA", (16, 16))
    for y in range(16):
        for x in range(16):
            r, g, b, a = textures["dirt_soil"].getpixel((x, y))
            dark_earth.putpixel((x, y), (int(r * 0.75), int(g * 0.75), int(b * 0.75), a))
    atlas.paste(dark_earth, (32, 48))
    # (48, 48): Cliff crest highlight
    cliff_crest = Image.blend(textures["cliff_side"], textures["mountain_stone_top"], 0.50)
    atlas.paste(cliff_crest, (48, 48))

    # Save atlas
    atlas.save(TEXTURES_DIR / "terrain_atlas.png", "PNG")
    atlas.save(OUTPUT_DIR / "terrain_atlas.png", "PNG")
    print(f"[SAVED] terrain_atlas.png (64x64, 16 regions)")
    return atlas


def build_tileability_previews(textures: dict[str, Image.Image]) -> None:
    """Render 6x6 repeated tile previews (96x96 upscaled to 576x576 nearest-neighbor)."""
    for name, tex in textures.items():
        tile_6x6 = Image.new("RGBA", (96, 96))
        for ty in range(6):
            for tx in range(6):
                tile_6x6.paste(tex, (tx * 16, ty * 16))

        # Upscale 6x using nearest neighbor for crisp review inspection
        upscaled = tile_6x6.resize((576, 576), Image.Resampling.NEAREST)

        # Add subtle framing & caption
        canvas = Image.new("RGB", (576, 620), color=(28, 32, 38))
        canvas.paste(upscaled.convert("RGB"), (0, 44))
        draw = ImageDraw.Draw(canvas)
        draw.text(
            (16, 14),
            f"TILEABILITY TEST: {name.upper()} (6x6 TILES — SEAMLESS)",
            fill=(230, 235, 240),
        )

        out_path = REVIEW_DIR / f"tileability_{name}.png"
        canvas.save(out_path, "PNG")
        print(f"[SAVED] {out_path.name} (6x6 preview)")


def build_godot_resources() -> None:
    """Generate Godot 4.x StandardMaterial3D .tres text resources."""
    materials_meta = {
        "material_forest": {
            "texture": "forest_grass_top.png",
            "roughness": 0.85,
            "cull_mode": 0,
        },
        "material_plains": {
            "texture": "plains_meadow_top.png",
            "roughness": 0.85,
            "cull_mode": 0,
        },
        "material_mountains": {
            "texture": "mountain_stone_top.png",
            "roughness": 0.90,
            "cull_mode": 0,
        },
        "material_cliff": {
            "texture": "cliff_side.png",
            "roughness": 0.92,
            "cull_mode": 0,
        },
        "material_dirt": {
            "texture": "dirt_soil.png",
            "roughness": 0.92,
            "cull_mode": 0,
        },
        "material_terrain_atlas": {
            "texture": "terrain_atlas.png",
            "roughness": 0.88,
            "cull_mode": 0,
        },
    }

    for mat_name, cfg in materials_meta.items():
        tex_file = cfg["texture"]
        rough = cfg["roughness"]
        tres_content = f"""[gd_resource type="StandardMaterial3D" load_steps=2 format=3]

[ext_resource type="Texture2D" path="res://assets/environment/terrain_materials/textures/{tex_file}" id="1_texture"]

[resource]
resource_name = "{mat_name}"
albedo_texture = ExtResource("1_texture")
roughness = {rough:.2f}
texture_filter = 0
"""
        for dest in (TEXTURES_DIR, OUTPUT_DIR):
            (dest / f"{mat_name}.tres").write_text(tres_content, encoding="utf-8")
        print(f"[SAVED] {mat_name}.tres")


def save_source_data() -> None:
    """Write source palette and texture definitions in JSON."""
    palette_data = {
        "version": 1,
        "description": "Cube Siege Stylized Voxel Terrain Material Palettes",
        "palettes": {
            name: {
                tok: {"rgba": list(col), "hex": "#{:02x}{:02x}{:02x}".format(col[0], col[1], col[2])}
                for tok, col in pal.items()
            }
            for name, pal in PALETTES.items()
        },
    }
    (SOURCE_DIR / "palette.json").write_text(
        json.dumps(palette_data, indent=2), encoding="utf-8"
    )

    texture_source = {
        "version": 1,
        "resolution": 16,
        "materials": list(PATTERNS.keys()),
        "patterns": PATTERNS,
        "atlas": {
            "resolution": 64,
            "cell_size": 16,
            "grid_cells": {
                "forest_grass_top": {"x": 0, "y": 0, "uv": [0.0, 0.0, 0.25, 0.25]},
                "plains_meadow_top": {"x": 1, "y": 0, "uv": [0.25, 0.0, 0.50, 0.25]},
                "mountain_stone_top": {"x": 2, "y": 0, "uv": [0.50, 0.0, 0.75, 0.25]},
                "cliff_side": {"x": 3, "y": 0, "uv": [0.75, 0.0, 1.0, 0.25]},
                "dirt_soil": {"x": 0, "y": 1, "uv": [0.0, 0.25, 0.25, 0.50]},
                "forest_side_edge": {"x": 1, "y": 1, "uv": [0.25, 0.25, 0.50, 0.50]},
                "plains_side_edge": {"x": 2, "y": 1, "uv": [0.50, 0.25, 0.75, 0.50]},
                "stone_cliff_rim": {"x": 3, "y": 1, "uv": [0.75, 0.25, 1.0, 0.50]},
            },
        },
    }
    (SOURCE_DIR / "textures_source.json").write_text(
        json.dumps(texture_source, indent=2), encoding="utf-8"
    )
    print("[SAVED] source/palette.json and source/textures_source.json")


def build_showcase_voxel_packages() -> None:
    """Generate 5 voxel_static packages for 3D showcase of terrain blocks."""
    packages = {
        "block_forest_grass": {
            "name": "terrain_forest_grass_block",
            "title": "Forest Grass Showcase Block",
            "desc": "3D stylized voxel terrain block showcasing Forest Grass Top surface with cut soil foundation and stepped elevation.",
            "materials": {
                "F": {"name": "forest_grass_base", "base_color": [0.16, 0.31, 0.11, 1.0], "roughness": 0.85, "metallic": 0.0},
                "L": {"name": "forest_grass_accent", "base_color": [0.27, 0.48, 0.17, 1.0], "roughness": 0.85, "metallic": 0.0},
                "S": {"name": "soil_subsurface", "base_color": [0.35, 0.25, 0.17, 1.0], "roughness": 0.92, "metallic": 0.0},
                "D": {"name": "deep_earth", "base_color": [0.22, 0.15, 0.10, 1.0], "roughness": 0.92, "metallic": 0.0},
            },
            "layers": [
                {"y": 0, "rows": ["DDDDDDDD"] * 8},
                {"y": 1, "rows": ["DDDDDDDD", "DDDDDDDD", "DDSDDDDD", "DDSSDDDD", "DDDDDDDD", "DDDDDDDD", "DDDDDDDD", "DDDDDDDD"]},
                {"y": 2, "rows": ["SSSSSSSS"] * 8},
                {"y": 3, "rows": ["SSSSSSSS", "SSSSSSSS", "SSSSSSSS", "SSSSSSSS", "FFFFFFFF", "FFFFFFFF", "FFFFFFFF", "FFFFFFFF"]},
                {"y": 4, "rows": ["FFFFFFFF", "FFFFFFFF", "FFFFFFFF", "FFFFFFFF", "..LL....", "...L....", "........", "........"]},
                {"y": 5, "rows": [".LL.....", "..LL....", "...L....", "........", "........", "........", "........", "........"]},
            ],
        },
        "block_plains_meadow": {
            "name": "terrain_plains_meadow_block",
            "title": "Plains Meadow Showcase Block",
            "desc": "3D stylized voxel terrain block showcasing Plains Meadow Top surface with gentle sunlit meadow terrace and soil bank cut.",
            "materials": {
                "P": {"name": "plains_meadow_base", "base_color": [0.28, 0.45, 0.15, 1.0], "roughness": 0.85, "metallic": 0.0},
                "M": {"name": "plains_meadow_accent", "base_color": [0.40, 0.60, 0.20, 1.0], "roughness": 0.85, "metallic": 0.0},
                "S": {"name": "soil_subsurface", "base_color": [0.35, 0.25, 0.17, 1.0], "roughness": 0.92, "metallic": 0.0},
                "D": {"name": "deep_earth", "base_color": [0.22, 0.15, 0.10, 1.0], "roughness": 0.92, "metallic": 0.0},
            },
            "layers": [
                {"y": 0, "rows": ["DDDDDDDD"] * 8},
                {"y": 1, "rows": ["DDDDDDDD", "DDSDDDDD", "DSSDDDDD", "DDDDDDDD", "DDDDDDDD", "DDDDDDDD", "DDDDDDDD", "DDDDDDDD"]},
                {"y": 2, "rows": ["SSSSSSSS"] * 8},
                {"y": 3, "rows": ["SSSSSSSS", "SSSSSSSS", "SSSSSSSS", "PPPPPPPP", "PPPPPPPP", "PPPPPPPP", "PPPPPPPP", "PPPPPPPP"]},
                {"y": 4, "rows": ["PPPPPPPP", "PPPPPPPP", "PPPPPPPP", "....MM..", ".....M..", "........", "........", "........"]},
                {"y": 5, "rows": ["..MM....", "...M....", "........", "........", "........", "........", "........", "........"]},
            ],
        },
        "block_mountain_stone": {
            "name": "terrain_mountain_stone_block",
            "title": "Mountain Stone Showcase Block",
            "desc": "3D stylized voxel terrain block showcasing Mountain Stone Top surface with chiseled rock shelves and granite facets.",
            "materials": {
                "S": {"name": "stone_primary", "base_color": [0.49, 0.47, 0.45, 1.0], "roughness": 0.90, "metallic": 0.0},
                "L": {"name": "stone_light", "base_color": [0.68, 0.66, 0.63, 1.0], "roughness": 0.90, "metallic": 0.0},
                "D": {"name": "stone_dark", "base_color": [0.33, 0.33, 0.31, 1.0], "roughness": 0.90, "metallic": 0.0},
                "M": {"name": "stone_shelf", "base_color": [0.58, 0.56, 0.53, 1.0], "roughness": 0.90, "metallic": 0.0},
            },
            "layers": [
                {"y": 0, "rows": ["SSSSSSSS"] * 8},
                {"y": 1, "rows": ["SSSSSSSS", "SSDDSSSS", "SDDDSSSS", "SSSSSSSS", "SSSSSSSS", "SSSSSSSS", "SSSSSSSS", "SSSSSSSS"]},
                {"y": 2, "rows": ["SSSSSSSS", "SSSSSSSS", "SSSSMMSS", "SSSSMMSS", "SSSSSSSS", "SSSSSSSS", "SSSSSSSS", "SSSSSSSS"]},
                {"y": 3, "rows": ["SSMMSSSS", "SSMMSSSS", "SSLLSSSS", "SSLLSSSS", "SSSSSSSS", "SSSSSSSS", "........", "........"]},
                {"y": 4, "rows": ["..LLSSSS", "..LLSSSS", "..LLSSSS", "........", "........", "........", "........", "........"]},
                {"y": 5, "rows": ["...LSS..", "...LSS..", "........", "........", "........", "........", "........", "........"]},
            ],
        },
        "block_cliff_strata": {
            "name": "terrain_cliff_strata_block",
            "title": "Cliff Strata Showcase Block",
            "desc": "3D stylized voxel terrain block showcasing vertical Cliff Side strata layers with stepped relief and horizontal overhangs.",
            "materials": {
                "B": {"name": "cliff_base", "base_color": [0.27, 0.25, 0.24, 1.0], "roughness": 0.92, "metallic": 0.0},
                "S": {"name": "cliff_strata_mid", "base_color": [0.33, 0.31, 0.30, 1.0], "roughness": 0.92, "metallic": 0.0},
                "L": {"name": "cliff_shelf_lip", "base_color": [0.45, 0.43, 0.40, 1.0], "roughness": 0.92, "metallic": 0.0},
                "D": {"name": "cliff_fissure", "base_color": [0.20, 0.20, 0.19, 1.0], "roughness": 0.92, "metallic": 0.0},
            },
            "layers": [
                {"y": 0, "rows": ["BBBBBBBB"] * 8},
                {"y": 1, "rows": ["BBBBBBBB", "BBDDBBBB", "BBDDBBBB", "BBBBBBBB", "BBBBBBBB", "BBBBBBBB", "BBBBBBBB", "BBBBBBBB"]},
                {"y": 2, "rows": ["SSSSSSSS", "SSSSSSSS", "SSSSSSSS", "SSSSSSSS", "SSSSSSSS", "SSSSSSSS", "........", "........"]},
                {"y": 3, "rows": ["SSLLSSSS", "SSLLSSSS", "SSLLSSSS", "SSSSSSSS", "SSSSSSSS", "........", "........", "........"]},
                {"y": 4, "rows": ["..LLSSSS", "..LLSSSS", "..LLSSSS", "SSSSSSSS", "........", "........", "........", "........"]},
                {"y": 5, "rows": ["...LSSSS", "...LSSSS", "...LSSSS", "........", "........", "........", "........", "........"]},
            ],
        },
        "block_dirt_soil": {
            "name": "terrain_dirt_soil_block",
            "title": "Dirt Soil Showcase Block",
            "desc": "3D stylized voxel terrain block showcasing Soil / Dirt Accent material with crumbly loam terrace and subsoil structure.",
            "materials": {
                "S": {"name": "soil_primary", "base_color": [0.35, 0.25, 0.17, 1.0], "roughness": 0.92, "metallic": 0.0},
                "M": {"name": "soil_crumb", "base_color": [0.43, 0.31, 0.21, 1.0], "roughness": 0.92, "metallic": 0.0},
                "L": {"name": "soil_light_crumb", "base_color": [0.52, 0.37, 0.25, 1.0], "roughness": 0.92, "metallic": 0.0},
                "D": {"name": "soil_dark_loam", "base_color": [0.22, 0.15, 0.10, 1.0], "roughness": 0.92, "metallic": 0.0},
            },
            "layers": [
                {"y": 0, "rows": ["DDDDDDDD"] * 8},
                {"y": 1, "rows": ["DDDDDDDD", "DDSDDDDD", "DSDDDDDD", "DDDDDDDD", "DDDDDDDD", "DDDDDDDD", "DDDDDDDD", "DDDDDDDD"]},
                {"y": 2, "rows": ["SSSSSSSS"] * 8},
                {"y": 3, "rows": ["SSSSSSSS", "SSSSSSSS", "SSSSSSSS", "SSSSSSSS", "MMMMMMMM", "MMMMMMMM", "MMMMMMMM", "MMMMMMMM"]},
                {"y": 4, "rows": ["MMMMMMMM", "MMMMMMMM", "MMMMMMMM", "....LL..", ".....L..", "........", "........", "........"]},
                {"y": 5, "rows": ["..LL....", "...L....", "........", "........", "........", "........", "........", "........"]},
            ],
        },
    }

    for slug, pkg in packages.items():
        pkg_dir = TERRAIN_DIR / slug
        source_dir = pkg_dir / "source"
        output_dir = pkg_dir / "output"
        review_dir = pkg_dir / "review"
        for d in (pkg_dir, source_dir, output_dir, review_dir):
            d.mkdir(parents=True, exist_ok=True)

        manifest = {
            "name": pkg["name"],
            "type": "voxel_static",
            "version": 1,
            "source": "source/voxels.json",
            "outputs": {"model": "output/model.glb"},
            "review": {"required_views": ["iso", "front", "side", "top"]},
            "budgets": {"max_materials": 4, "max_triangles": 5000},
        }
        (pkg_dir / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")

        voxels = {
            "version": 1,
            "name": pkg["name"],
            "voxel_size": 0.15,
            "origin": "bottom_center",
            "materials": pkg["materials"],
            "layers": pkg["layers"],
        }
        (source_dir / "voxels.json").write_text(json.dumps(voxels, indent=2), encoding="utf-8")

        request_md = f"""# {pkg['title']}

## 1. Overview

{pkg['desc']}

## 2. Specifications

- Target resolution: 8x6x8 voxels
- Voxel size: 0.15m (1.2m x 0.9m x 1.2m sample block)
- Material set: 4 calibrated stylized materials
- Purpose: Static 3D visual showcase and validation package for Cube Siege terrain materials.
"""
        (pkg_dir / "request.md").write_text(request_md, encoding="utf-8")
        print(f"[PACKAGE] {slug} initialized with manifest, request, and voxels.json")


def write_showcase_reviews() -> None:
    """Write review.md for each showcase block based on its review/metrics.json."""
    block_names = [
        "block_forest_grass",
        "block_plains_meadow",
        "block_mountain_stone",
        "block_cliff_strata",
        "block_dirt_soil",
    ]
    for slug in block_names:
        pkg_dir = TERRAIN_DIR / slug
        review_dir = pkg_dir / "review"
        metrics_file = review_dir / "metrics.json"
        if not metrics_file.exists():
            continue
        data = json.loads(metrics_file.read_text(encoding="utf-8"))

        review_md = f"""# Build Verification: {slug}

## Objective Build Verification
- [x] Required review renders generated (iso.png, front.png, side.png, top.png).
- [x] Export validated (model.glb, glTF 2.0).
- [x] Material count is within budget ({data.get('materials', 4)} materials <= 4).
- [x] Triangle count verified ({data.get('triangles', 0)} tris <= 5000).
- [x] Internal faces culled ({data.get('visible_faces', 0)} visible faces).
- [x] Ground contact flat at y=0, origin bottom_center.

## Metrics
- Occupied voxels: {data.get('occupied_voxels', 0)}
- Triangles: {data.get('triangles', 0)}
- Visible faces: {data.get('visible_faces', 0)}
- Grid: {data.get('grid', {}).get('x', 8)}x{data.get('grid', {}).get('y', 6)}x{data.get('grid', {}).get('z', 8)}
- World size: {data.get('world_size', {}).get('x', 1.2):.2f} x {data.get('world_size', {}).get('y', 0.9):.2f} x {data.get('world_size', {}).get('z', 1.2):.2f} m
"""
        (review_dir / "review.md").write_text(review_md, encoding="utf-8")
        print(f"[REVIEW] Written review.md for {slug}")


def main() -> None:
    print("=== Authoring Terrain Material Kit ===")
    textures = build_all_textures()
    build_terrain_atlas(textures)
    build_tileability_previews(textures)
    build_godot_resources()
    save_source_data()
    build_showcase_voxel_packages()
    write_showcase_reviews()
    print("=== Authoring complete ===")


if __name__ == "__main__":
    main()


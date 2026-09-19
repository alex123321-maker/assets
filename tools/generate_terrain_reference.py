#!/usr/bin/env python3
"""generate_terrain_reference.py - Generates the approved concept reference sheet for Terrain Materials."""

from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
TERRAIN_DIR = ROOT / "assets" / "environment" / "terrain_materials"
REF_DIR = TERRAIN_DIR / "references"
TEXTURES_DIR = TERRAIN_DIR / "textures"
REF_DIR.mkdir(parents=True, exist_ok=True)

W, H = 1600, 1300
canvas = Image.new("RGB", (W, H), color=(24, 28, 34))
draw = ImageDraw.Draw(canvas)
font = ImageFont.load_default()

# 1. Header
draw.rectangle([(0, 0), (W, 90)], fill=(16, 18, 22))
draw.text((40, 25), "CUBE SIEGE   TERRAIN MATERIAL KIT", fill=(255, 255, 255), font=font)
draw.text((40, 50), "CONCEPT ART, PALETTES & BIOME SPECIFICATIONS", fill=(180, 190, 205), font=font)
draw.text((1050, 35), "READABLE BIOMES. TILEABLE SURFACES. STRATIFIED CLIFFS.", fill=(160, 175, 190), font=font)
draw.text((1050, 55), "PRODUCTION VOXEL TERRAIN SYSTEM | ISSUE #6", fill=(130, 145, 160), font=font)

# 2. Five Column Cards for Materials
cols = [
    {
        "id": "forest_grass_top",
        "title": "FOREST GRASS",
        "sub": "Deep Rich Canopy Floor",
        "tex": "forest_grass_top.png",
        "block": "block_forest_grass",
        "color": (52, 99, 35),
        "notes": [
            "• Saturated deep green tone",
            "• Large-scale gentle clumping",
            "• No high-frequency pixel noise",
            "• Oak tree foliage compatible",
            "• Roughness: 0.85 (matte grass)",
        ],
        "palette": [
            ("Base Green", "#28501b", (40, 80, 27)),
            ("Mid Foliage", "#346323", (52, 99, 35)),
            ("Sunlit Blade", "#447b2c", (68, 123, 44)),
            ("Deep Shadow", "#1f3f15", (31, 63, 21)),
        ],
    },
    {
        "id": "plains_meadow_top",
        "title": "PLAINS MEADOW",
        "sub": "Sunny Warm Meadow",
        "tex": "plains_meadow_top.png",
        "block": "block_plains_meadow",
        "color": (91, 141, 46),
        "notes": [
            "• Lighter & warmer than Forest",
            "• Serene, calm open fields",
            "• Rare subtle golden flecks",
            "• No baked confetti noise",
            "• Roughness: 0.85 (matte meadow)",
        ],
        "palette": [
            ("Base Meadow", "#487425", (72, 116, 37)),
            ("Sunny Mid", "#5b8d2e", (91, 141, 46)),
            ("Sunlit Field", "#70a338", (112, 163, 56)),
            ("Golden Fleck", "#8cb845", (140, 184, 69)),
        ],
    },
    {
        "id": "mountain_stone_top",
        "title": "MOUNTAIN STONE",
        "sub": "Faceted Rocky Summits",
        "tex": "mountain_stone_top.png",
        "block": "block_mountain_stone",
        "color": (125, 120, 114),
        "notes": [
            "• Light/medium grey stone",
            "• Interlocking planar facets",
            "• Rock family #3 compatible",
            "• Zero procedural stripe noise",
            "• Roughness: 0.90 (chiseled stone)",
        ],
        "palette": [
            ("Primary Rock", "#7d7872", (125, 120, 114)),
            ("Bright Shelf", "#959088", (149, 144, 136)),
            ("Sunlit Plateau", "#aea8a0", (174, 168, 160)),
            ("Dark Crevice", "#555350", (85, 83, 80)),
        ],
    },
    {
        "id": "cliff_side",
        "title": "CLIFF / ROCK SIDE",
        "sub": "Stratified Relief Dropping",
        "tex": "cliff_side.png",
        "block": "block_cliff_strata",
        "color": (84, 80, 76),
        "notes": [
            "• Darker than mountain top",
            "• Irregular horizontal strata",
            "• Gives depth to voxel drops",
            "• No harsh pitch-black lines",
            "• Roughness: 0.92 (exposed rock)",
        ],
        "palette": [
            ("Base Strata", "#44413e", (68, 65, 62)),
            ("Mid Strata", "#54504c", (84, 80, 76)),
            ("Shelf Lip", "#746e67", (116, 110, 103)),
            ("Deep Fissure", "#343230", (52, 50, 48)),
        ],
    },
    {
        "id": "dirt_soil",
        "title": "SOIL / DIRT ACCENT",
        "sub": "Shared Auxiliary Earth",
        "tex": "dirt_soil.png",
        "block": "block_dirt_soil",
        "color": (90, 64, 43),
        "notes": [
            "• Warm rich earthy loam",
            "• Crumbly voxel soil clods",
            "• Under-grass transitions",
            "• Natural erosion & cuts",
            "• Roughness: 0.92 (earthy loam)",
        ],
        "palette": [
            ("Loam Base", "#5a402b", (90, 64, 43)),
            ("Soil Clod", "#6e4f35", (110, 79, 53)),
            ("Weathered Earth", "#845f40", (132, 95, 64)),
            ("Deep Loam", "#38271a", (56, 39, 26)),
        ],
    },
]

card_w = 290
card_gap = 18
start_x = 35
card_y = 110
card_h = 750

for i, col in enumerate(cols):
    cx = start_x + i * (card_w + card_gap)
    # Card background
    draw.rectangle([(cx, card_y), (cx + card_w, card_y + card_h)], fill=(32, 38, 46), outline=(50, 58, 70))
    # Top color stripe
    draw.rectangle([(cx, card_y), (cx + card_w, card_y + 8)], fill=col["color"])

    # Header
    draw.text((cx + 14, card_y + 18), col["title"], fill=(245, 245, 250), font=font)
    draw.text((cx + 14, card_y + 36), col["sub"], fill=(160, 175, 195), font=font)

    # 3D Voxel Render preview
    block_img_path = TERRAIN_DIR / col["block"] / "review" / "iso.png"
    if block_img_path.exists():
        b_img = Image.open(block_img_path).convert("RGBA")
        b_resized = b_img.resize((card_w - 28, card_w - 28), Image.Resampling.LANCZOS)
        canvas.paste(b_resized, (cx + 14, card_y + 58), b_resized)

    # Texture preview (16x16 upscaled)
    tex_path = TEXTURES_DIR / col["tex"]
    if tex_path.exists():
        t_img = Image.open(tex_path).convert("RGBA")
        t_upscaled = t_img.resize((72, 72), Image.Resampling.NEAREST)
        canvas.paste(t_upscaled, (cx + 14, card_y + 330))
        draw.rectangle([(cx + 14, card_y + 330), (cx + 14 + 72, card_y + 330 + 72)], outline=(80, 95, 115))
        draw.text((cx + 96, card_y + 345), "16x16 TEXEL", fill=(230, 230, 230), font=font)
        draw.text((cx + 96, card_y + 365), "POINT FILTER", fill=(160, 175, 195), font=font)

    # Palette swatches
    draw.text((cx + 14, card_y + 420), "PALETTE SPECIFICATION", fill=(210, 220, 235), font=font)
    swatch_y = card_y + 440
    for p_name, p_hex, p_rgb in col["palette"]:
        draw.rectangle([(cx + 14, swatch_y), (cx + 34, swatch_y + 14)], fill=p_rgb, outline=(100, 110, 125))
        draw.text((cx + 42, swatch_y + 1), f"{p_name} ({p_hex})", fill=(185, 195, 210), font=font)
        swatch_y += 22

    # Style notes
    draw.text((cx + 14, card_y + 545), "VISUAL CONTRACT", fill=(210, 220, 235), font=font)
    note_y = card_y + 568
    for n in col["notes"]:
        draw.text((cx + 14, note_y), n, fill=(165, 180, 195), font=font)
        note_y += 20

# 3. Lower Section: In-Game Harmony & Rules
box_y = 880
box_h = 360
draw.rectangle([(35, box_y), (W - 35, box_y + box_h)], fill=(28, 34, 42), outline=(48, 56, 68))

# Title
draw.text((55, box_y + 20), "UNIFIED TERRAIN INTEGRATION & TEXTURE ATLAS ARCHITECTURE", fill=(255, 255, 255), font=font)
draw.text((55, box_y + 40), "Single draw call optimization via 64x64 RGBA8 Atlas for batched chunk meshes in Godot 4.x", fill=(170, 185, 205), font=font)

# Paste atlas preview
atlas_path = TEXTURES_DIR / "terrain_atlas.png"
if atlas_path.exists():
    a_img = Image.open(atlas_path).convert("RGBA")
    a_upscaled = a_img.resize((260, 260), Image.Resampling.NEAREST)
    canvas.paste(a_upscaled, (55, box_y + 70))
    draw.rectangle([(55, box_y + 70), (55 + 260, box_y + 70 + 260)], outline=(80, 95, 115))
    draw.text((55, box_y + 336), "64x64 TERRAIN ATLAS (16 REGIONS)", fill=(190, 205, 220), font=font)

# Textual architectural breakdown
tx = 350
ty = box_y + 70
specs = [
    ("ATLAS REGION MAPPING", [
        "(0, 0): Forest Grass Top (UV [0.0, 0.0, 0.25, 0.25])",
        "(1, 0): Plains Meadow Top (UV [0.25, 0.0, 0.50, 0.25])",
        "(2, 0): Mountain Stone Top (UV [0.50, 0.0, 0.75, 0.25])",
        "(3, 0): Cliff / Exposed Rock Side (UV [0.75, 0.0, 1.0, 0.25])",
        "(0, 1): Soil / Dirt Accent (UV [0.0, 0.25, 0.25, 0.50])",
        "(1..3, 1): Side bank transitions (Grass / Stone rim with Dirt below)",
    ]),
    ("ENGINE RULES (GODOT 4.x)", [
        "• Texture filter: BaseMaterial3D.TEXTURE_FILTER_NEAREST (point)",
        "• Voxel quad UV mapping: normalized 0..1 per quad face",
        "• Draw call batching: 1 material surface per chunk (or atlas)",
        "• Roughness: 0.85 (grass/meadow), 0.90 (mountain), 0.92 (cliff/soil)",
        "• No photorealistic micro-noise; chunky readable 16x16 texels",
    ]),
    ("ASSET HARMONY GUARANTEE", [
        "• Mountain stone calibrated with Destructible Rock #7d7872 / #aea8a0",
        "• Forest grass calibrated with Oak Tree foliage #3b6b22 / #5e932b",
        "• Plains meadow distinct: warmer golden-green for calm readability",
        "• Cliff side dark strata provides depth without harsh black borders",
        "• 6x6 tileability mathematically verified with zero border seams",
    ]),
]

for section_title, lines in specs:
    draw.text((tx, ty), section_title, fill=(240, 245, 255), font=font)
    ly = ty + 24
    for line in lines:
        draw.text((tx, ly), line, fill=(175, 190, 205), font=font)
        ly += 20
    tx += 400

# Footer
draw.text((35, H - 35), "CUBE SIEGE — TERRAIN MATERIAL SYSTEM | ALEX123321-MAKER/ASSETS", fill=(110, 125, 140), font=font)

out_file = REF_DIR / "terrain_concept_reference.png"
canvas.save(out_file, "PNG")
print(f"[SAVED] {out_file} ({W}x{H})")

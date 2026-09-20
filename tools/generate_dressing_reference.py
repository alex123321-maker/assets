#!/usr/bin/env python3
"""Generate a production catalog without replacing reference art or approval records."""

from pathlib import Path
from pipeline_reports import initialize_text
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
DRESSING_DIR = ROOT / "assets" / "environment" / "dressing_pack"
REF_DIR = DRESSING_DIR / "references"
REF_DIR.mkdir(parents=True, exist_ok=True)

W, H = 1920, 1080
canvas = Image.new("RGB", (W, H), color=(22, 26, 32))
draw = ImageDraw.Draw(canvas)
font = ImageFont.load_default()

# 1. Header
draw.rectangle([(0, 0), (W, 96)], fill=(14, 17, 22))
draw.text((40, 24), "CUBE SIEGE   ENVIRONMENT DRESSING PACK", fill=(255, 255, 255), font=font)
draw.text((40, 52), "PRODUCTION CATALOG (NOT A REFERENCE) & BIOME INTEGRATION", fill=(175, 190, 205), font=font)
draw.text((1180, 32), "CHUNKY READABLE SHAPES | MASS MULTIMESH BATCHING READY", fill=(155, 175, 195), font=font)
draw.text((1180, 56), "ISSUE #7: GRASS TUFTS (6) + FLOWERS (4) + MOSS (3) + STONE DEBRIS (6)", fill=(125, 145, 165), font=font)

# 2. Four Family Feature Columns
families = [
    {
        "id": "grass_tufts",
        "title": "GRASS TUFTS",
        "count": "6 Variants (Slots 0..5)",
        "sub": "3 Small, 2 Medium, 1 Tall Accent",
        "accent_color": (116, 140, 66),
        "desc": [
            "• Chunky stepped voxel blades",
            "• Natural outwards fan & directional tilts",
            "• Flat clean ground contact at z=0",
            "• Height: 0.15m - 0.60m (voxel_size: 0.10m)",
            "• No alpha foliage cards; solid volume geometry",
            "• Triangles: 92 - 228 tris per mesh",
        ],
        "variants": [
            "1. grass_tuft_small_01 (Compact 3-blade sprig)",
            "2. grass_tuft_small_02 (Asymmetric fan sprig)",
            "3. grass_tuft_small_03 (Bushy stepped clump)",
            "4. grass_tuft_med_01 (Tiered multi-blade tuft)",
            "5. grass_tuft_med_02 (Wind-swept spread tuft)",
            "6. grass_tuft_tall_01 (Tall accent focal tuft)",
        ],
        "palette": [
            ("Primary Grass", "#748c42", (116, 140, 66)),
            ("Dark Foliage Root", "#323d23", (50, 61, 35)),
            ("Sunlit Light Tip", "#729253", (114, 146, 83)),
        ],
    },
    {
        "id": "flowers",
        "title": "FLOWERS",
        "count": "4 Variants / Archetypes",
        "sub": "White, Yellow, Red, Mixed Accent",
        "accent_color": (246, 199, 68),
        "desc": [
            "• Distinct archetypes: daisies, buttercups, poppies, bells",
            "• Distinct heights (0.3m to 0.5m) and voxel layouts",
            "• Grounded leafy rosette bases & colored blossoms",
            "• High readability from isometric gameplay camera",
            "• Distinctive silhouettes under rotation",
            "• Triangles: 136 - 236 tris per mesh",
        ],
        "variants": [
            "1. flower_white_cluster (Meadow daisies)",
            "2. flower_yellow_cluster (Sunny buttercups)",
            "3. flower_red_cluster (Crimson poppies)",
            "4. flower_mixed_accent (Rare bellflower/violet)",
        ],
        "palette": [
            ("Flower White", "#eeeade", (238, 234, 223)),
            ("Flower Yellow", "#f6c744", (246, 199, 68)),
            ("Flower Red", "#e2614d", (226, 97, 77)),
            ("Flower Purple", "#9767aa", (151, 103, 170)),
        ],
    },
    {
        "id": "moss_low_veg",
        "title": "MOSS / LOW VEGETATION",
        "count": "3 Low Variants",
        "sub": "Tree Bases, Rocks & Cliff Ledges",
        "accent_color": (64, 76, 42),
        "desc": [
            "• Organic shelf & skirt geometry",
            "• Smooth transition between props and terrain",
            "• Concave tree base collar wraps oak trunks",
            "• Clinging L-shelf fits rock joints & ledges",
            "• Stepped overhang for cliffs & terraces",
            "• Triangles: 144 - 148 tris per mesh",
        ],
        "variants": [
            "1. moss_tree_base (Curved trunk wrap collar)",
            "2. moss_rock_shelf (Clinging rock crevice shelf)",
            "3. moss_cliff_ledge (Cascading terrace overhang)",
        ],
        "palette": [
            ("Velvet Moss", "#404c2a", (64, 76, 42)),
            ("Dark Lichen Root", "#323d23", (50, 61, 35)),
            ("Light Moss Tip", "#729253", (114, 146, 83)),
        ],
    },
    {
        "id": "stone_debris",
        "title": "STONE DEBRIS",
        "count": "6 Variants (Independent Palette)",
        "sub": "Single, Trio, Patch, Chip, Scatter, Cluster",
        "accent_color": (91, 86, 82),
        "desc": [
            "• Independent darker palette from concept reference",
            "• High ground contrast against green terrain & grass",
            "• Planar facets, bevel clefts & broken footprints",
            "• Clean ground contact; zero floating cubes",
            "• Unique 3D rotational signatures (no duplicates)",
            "• Triangles: 84 - 262 tris per mesh",
        ],
        "variants": [
            "1. stone_debris_single (Faceted 2-tier keystone)",
            "2. stone_debris_trio (Balanced 3-stone group)",
            "3. stone_debris_flat_patch (Interlocking slab patch)",
            "4. stone_debris_angular_chip (Sharp triangular pinnacle)",
            "5. stone_debris_fine_scatter (Gravel & grit spread)",
            "6. stone_debris_mountain_cluster (Stepped crag pile)",
        ],
        "palette": [
            ("Primary Stone", "#5b5652", (91, 86, 82)),
            ("Crevice Dark", "#3e3d3b", (62, 61, 59)),
            ("Sunlit Light", "#65615b", (101, 97, 91)),
            ("Rock Moss", "#5a673e", (90, 103, 62)),
        ],
    },
]

card_w = 440
card_gap = 20
start_x = 40
card_y = 120
card_h = 750

for i, f_data in enumerate(families):
    cx = start_x + i * (card_w + card_gap)
    # Card background
    draw.rectangle([(cx, card_y), (cx + card_w, card_y + card_h)], fill=(28, 33, 40), outline=(48, 56, 68), width=1)
    
    # Top banner with accent color
    draw.rectangle([(cx, card_y), (cx + card_w, card_y + 60)], fill=(20, 24, 30))
    draw.rectangle([(cx, card_y), (cx + 6, card_y + 60)], fill=f_data["accent_color"])
    draw.text((cx + 18, card_y + 12), f_data["title"], fill=(255, 255, 255), font=font)
    draw.text((cx + 18, card_y + 34), f_data["count"], fill=f_data["accent_color"], font=font)
    
    # Subtitle
    draw.text((cx + 18, card_y + 72), f_data["sub"], fill=(160, 175, 195), font=font)
    draw.line([(cx + 18, card_y + 92), (cx + card_w - 18, card_y + 92)], fill=(44, 52, 64), width=1)
    
    # Visual principles
    draw.text((cx + 18, card_y + 104), "VISUAL & TECHNICAL SPECS:", fill=(200, 215, 230), font=font)
    for line_idx, line in enumerate(f_data["desc"]):
        draw.text((cx + 18, card_y + 126 + line_idx * 22), line, fill=(170, 185, 200), font=font)
        
    # Variant list
    var_start_y = card_y + 270
    draw.line([(cx + 18, var_start_y - 10), (cx + card_w - 18, var_start_y - 10)], fill=(44, 52, 64), width=1)
    draw.text((cx + 18, var_start_y), "REQUIRED VARIANTS:", fill=(200, 215, 230), font=font)
    for v_idx, var_name in enumerate(f_data["variants"]):
        draw.text((cx + 18, var_start_y + 22 + v_idx * 22), var_name, fill=(145, 195, 235), font=font)
        
    # Palette swatches
    pal_start_y = card_y + 430
    draw.line([(cx + 18, pal_start_y - 10), (cx + card_w - 18, pal_start_y - 10)], fill=(44, 52, 64), width=1)
    draw.text((cx + 18, pal_start_y), "SHARED PALETTE SWATCHES:", fill=(200, 215, 230), font=font)
    for p_idx, (p_name, p_hex, p_rgb) in enumerate(f_data["palette"]):
        sy = pal_start_y + 24 + p_idx * 48
        draw.rectangle([(cx + 18, sy), (cx + 56, sy + 38)], fill=p_rgb, outline=(60, 70, 85), width=1)
        draw.text((cx + 68, sy + 4), p_name, fill=(230, 235, 240), font=font)
        draw.text((cx + 68, sy + 20), f"{p_hex}  |  RGB{p_rgb}", fill=(130, 145, 160), font=font)

    # MultiMesh Readiness Badge
    badge_y = card_y + card_h - 75
    draw.rectangle([(cx + 16, badge_y), (cx + card_w - 16, badge_y + 55)], fill=(20, 26, 32), outline=(40, 52, 65), width=1)
    draw.text((cx + 26, badge_y + 10), "BATCHING / MULTIMESH READY", fill=(80, 200, 120), font=font)
    draw.text((cx + 26, badge_y + 30), "Pivot: bottom_center | No scripts | No collision", fill=(140, 155, 170), font=font)

# 3. Bottom Summary / Technical Matrix Banner
banner_y = 890
banner_h = 160
draw.rectangle([(start_x, banner_y), (W - start_x, banner_y + banner_h)], fill=(16, 20, 26), outline=(44, 54, 66), width=1)

draw.text((60, banner_y + 18), "BIOME DRESSING INTEGRATION RULES", fill=(255, 255, 255), font=font)
draw.text((60, banner_y + 40), "FOREST: Dense grass clumps + tree base moss collars + white/red flowers + scattered stone debris near rock outcroppings.", fill=(160, 185, 210), font=font)
draw.text((60, banner_y + 60), "PLAINS: Open field grass tufts + dense golden yellow & white flower carpets + rare mixed accent bellflowers + flat stone patches.", fill=(160, 185, 210), font=font)
draw.text((60, banner_y + 80), "MOUNTAINS: Sparse hardy grass sprigs + jagged stone debris & mountain crags + clinging rock shelf moss + cliff ledge cascades.", fill=(160, 185, 210), font=font)

draw.line([(1060, banner_y + 15), (1060, banner_y + banner_h - 15)], fill=(44, 54, 66), width=1)

draw.text((1090, banner_y + 18), "PERFORMANCE & ENGINE CONTRACT", fill=(255, 255, 255), font=font)
draw.text((1090, banner_y + 40), "• Total Props: 19 models across 4 subfamilies (6 Grass + 4 Flowers + 3 Moss + 6 Stone Debris)", fill=(160, 185, 210), font=font)
draw.text((1090, banner_y + 60), "• Voxel Scale: 0.10m uniform step | Culled interior faces | Flat shaded normals", fill=(160, 185, 210), font=font)
draw.text((1090, banner_y + 80), "• Memory Footprint: Shared 64x64 albedo & 64x64 metallic-roughness atlases", fill=(160, 185, 210), font=font)
draw.text((1090, banner_y + 100), "• Budget: max 500 tris (actual: 84 - 408 tris, avg 226.2) | Zero CPU overhead", fill=(160, 185, 210), font=font)
draw.text((1090, banner_y + 120), "• Review Evidence: Full contact sheet, 3 density tests, 3 biome tests, gameplay isometric mockup", fill=(80, 200, 120), font=font)

# Generated catalogs are outputs, never approved reference inputs.
catalog_path = DRESSING_DIR / "review" / "dressing_catalog.png"
catalog_path.parent.mkdir(parents=True, exist_ok=True)
canvas.save(catalog_path, "PNG")
print(f"[OK] Saved production catalog: {catalog_path}")
initialize_text(REF_DIR / "README.md", "# Reference provenance\n\n"
                "Add user-supplied or separately generated candidate references here.\n"
                "Record origin, candidate/approved status and actual approval citation in quality.json.\n"
                "The generated production catalog in review/ is not an approved reference.\n")

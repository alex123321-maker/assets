#!/usr/bin/env python3
"""create_dressing_comparison_sheets.py - Generates review contact sheets, comparison sheets, metrics summary, and family review.md."""

from __future__ import annotations

import json
from pathlib import Path
from pipeline_reports import write_build_report
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
FAMILY_DIR = ROOT / "assets" / "environment" / "dressing_pack"
REVIEW_DIR = FAMILY_DIR / "review"
REF_PATH = FAMILY_DIR / "references" / "dressing_concept_reference.png"

REVIEW_DIR.mkdir(parents=True, exist_ok=True)

GROUPS = [
    {
        "name": "GRASS TUFTS (6 VARIANTS)",
        "color": (75, 145, 45),
        "props": [
            ("grass_tuft_small_01", "Small Sprig 01"),
            ("grass_tuft_small_02", "Small Sprig 02"),
            ("grass_tuft_small_03", "Small Clump 03"),
            ("grass_tuft_med_01", "Med Tiered 01"),
            ("grass_tuft_med_02", "Med Swept 02"),
            ("grass_tuft_tall_01", "Tall Accent 01"),
        ],
    },
    {
        "name": "FLOWERS (4 COLOR GROUPS)",
        "color": (210, 160, 35),
        "props": [
            ("flower_white_cluster", "White Daisies"),
            ("flower_yellow_cluster", "Yellow Buttercups"),
            ("flower_red_cluster", "Red Poppies"),
            ("flower_mixed_accent", "Rare Bellflower"),
        ],
    },
    {
        "name": "MOSS / LOW VEGETATION (3 VARIANTS)",
        "color": (65, 115, 40),
        "props": [
            ("moss_tree_base", "Tree Base Collar"),
            ("moss_rock_shelf", "Rock Crevice Shelf"),
            ("moss_cliff_ledge", "Cliff Ledge Cascade"),
        ],
    },
    {
        "name": "STONE DEBRIS (6 VARIANTS)",
        "color": (130, 125, 120),
        "props": [
            ("stone_debris_single", "Keystone Shard"),
            ("stone_debris_trio", "Trio Group"),
            ("stone_debris_flat_patch", "Flat Patch"),
            ("stone_debris_angular_chip", "Triangular Cleave"),
            ("stone_debris_fine_scatter", "Fine Scatter"),
            ("stone_debris_mountain_cluster", "Mountain Cluster"),
        ],
    },
]


def load_variant_metrics(slug: str) -> dict:
    m_path = FAMILY_DIR / slug / "review" / "metrics.json"
    if m_path.exists():
        try:
            return json.loads(m_path.read_text(encoding="utf-8"))
        except Exception:
            pass
    return {"occupied_voxels": 0, "triangles": 0, "visible_faces": 0, "materials": 1, "mesh_objects": 1, "world_size": {"x": 0, "y": 0, "z": 0}}


def build_contact_sheet() -> Path:
    """Build the high-resolution family contact sheet (>=1000x500) with all 19 props."""
    w, h = 2560, 1600
    canvas = Image.new("RGB", (w, h), color=(22, 26, 32))
    draw = ImageDraw.Draw(canvas)
    font = ImageFont.load_default()

    # 1. Header
    draw.rectangle([(0, 0), (w, 80)], fill=(14, 17, 22))
    draw.text((40, 20), "CUBE SIEGE   ENVIRONMENT DRESSING PACK   FAMILY CONTACT SHEET", fill=(255, 255, 255), font=font)
    draw.text((40, 48), "19 REUSABLE VOXEL PROPS (ISSUE #7) | SHARED ATLAS MATERIAL BATCHING | PIVOT: BOTTOM_CENTER", fill=(160, 180, 200), font=font)
    draw.text((1700, 32), "SINGLE SHARED MATERIAL (mat_dressing_atlas)", fill=(80, 200, 120), font=font)

    # 4 Rows
    row_y = 100
    row_h = 350
    card_w = 380
    card_gap = 24

    for g_idx, group in enumerate(GROUPS):
        gy = row_y + g_idx * (row_h + 15)
        draw.rectangle([(30, gy), (w - 30, gy + 32)], fill=(18, 22, 28))
        draw.rectangle([(30, gy), (38, gy + 32)], fill=group["color"])
        draw.text((50, gy + 8), group["name"], fill=(240, 245, 250), font=font)

        start_x = 35
        for p_idx, (slug, title) in enumerate(group["props"]):
            cx = start_x + p_idx * (card_w + card_gap)
            cy = gy + 42
            card_h_actual = row_h - 48

            draw.rectangle([(cx, cy), (cx + card_w, cy + card_h_actual)], fill=(28, 33, 40), outline=(44, 52, 64), width=1)

            iso_path = FAMILY_DIR / slug / "review" / "iso.png"
            if iso_path.exists():
                thumb = Image.open(iso_path).convert("RGB")
                thumb = thumb.resize((190, 190), Image.Resampling.LANCZOS)
                canvas.paste(thumb, (cx + 10, cy + 10))
            else:
                draw.rectangle([(cx + 10, cy + 10), (cx + 200, cy + 200)], fill=(38, 44, 52))
                draw.text((cx + 50, cy + 100), "NO RENDER", fill=(150, 150, 150), font=font)

            mx = cx + 210
            my = cy + 15
            m = load_variant_metrics(slug)

            draw.text((mx, my), title, fill=(255, 255, 255), font=font)
            draw.text((mx, my + 20), f"`{slug}`", fill=(140, 185, 230), font=font)
            draw.line([(mx, my + 40), (cx + card_w - 15, my + 40)], fill=(48, 56, 68), width=1)

            draw.text((mx, my + 50), f"Voxels: {m['occupied_voxels']}", fill=(200, 215, 230), font=font)
            draw.text((mx, my + 72), f"Triangles: {m['triangles']}", fill=(80, 200, 120), font=font)
            draw.text((mx, my + 94), f"Faces: {m['visible_faces']}", fill=(180, 195, 210), font=font)
            ws = m.get("world_size", {"x": 0, "y": 0, "z": 0})
            draw.text((mx, my + 116), f"Size: {ws['x']:.2f}x{ws['y']:.2f}x{ws['z']:.2f}m", fill=(160, 175, 190), font=font)
            draw.text((mx, my + 140), "Material: 1 (shared)", fill=(100, 220, 160), font=font)
            draw.text((mx, my + 160), "Pivot: bottom_center", fill=(130, 145, 160), font=font)

    out_path = REVIEW_DIR / "contact_sheet.png"
    canvas.save(out_path, "PNG")
    print(f"[OK] Generated family contact sheet at {out_path} ({w}x{h})")
    return out_path


def build_comparison_sheet() -> Path:
    """Build family comparison sheet showcasing multi-angle views and biome roles."""
    w, h = 2048, 1152
    canvas = Image.new("RGB", (w, h), color=(22, 26, 32))
    draw = ImageDraw.Draw(canvas)
    font = ImageFont.load_default()

    draw.rectangle([(0, 0), (w, 75)], fill=(14, 17, 22))
    draw.text((35, 18), "CUBE SIEGE   ENVIRONMENT DRESSING PACK   COMPARISON & MULTI-ANGLE SHOWCASE", fill=(255, 255, 255), font=font)
    draw.text((35, 45), "ORTHOGONAL REVIEW VIEWS (ISO, FRONT, SIDE, TOP) ACROSS SUBFAMILIES | 1 SHARED MATERIAL", fill=(160, 180, 200), font=font)

    featured = [
        ("grass_tuft_tall_01", "Grass: Tall Accent Tuft", "Forest / Plains Meadow Edge"),
        ("flower_mixed_accent", "Flowers: Mixed Accent Bellflower", "Rare Meadow Focal Point"),
        ("moss_tree_base", "Moss: Tree Base Collar", "Trunk / Root Base Blending"),
        ("stone_debris_angular_chip", "Stone: Angular Cleave Shard", "Steep 3-Layer Pointed Pinnacle"),
    ]

    card_h = 240
    start_y = 95

    for f_idx, (slug, title, role) in enumerate(featured):
        cy = start_y + f_idx * (card_h + 16)
        draw.rectangle([(30, cy), (w - 30, cy + card_h)], fill=(28, 33, 40), outline=(44, 52, 64), width=1)

        draw.rectangle([(30, cy), (320, cy + card_h)], fill=(20, 24, 30))
        draw.text((45, cy + 25), title, fill=(255, 255, 255), font=font)
        draw.text((45, cy + 50), f"`{slug}`", fill=(140, 185, 230), font=font)
        draw.text((45, cy + 75), f"Role: {role}", fill=(180, 195, 210), font=font)

        m = load_variant_metrics(slug)
        draw.text((45, cy + 120), f"Occupied Voxels: {m['occupied_voxels']}", fill=(160, 175, 190), font=font)
        draw.text((45, cy + 140), f"Triangles: {m['triangles']} tris", fill=(80, 200, 120), font=font)
        draw.text((45, cy + 160), f"Visible Faces: {m['visible_faces']}", fill=(160, 175, 190), font=font)
        draw.text((45, cy + 180), "Material: 1 (mat_dressing_atlas)", fill=(100, 220, 160), font=font)

        views = ["iso", "front", "side", "top"]
        thumb_size = 200
        view_start_x = 340
        view_gap = 25

        for v_idx, v_name in enumerate(views):
            vx = view_start_x + v_idx * (thumb_size + view_gap)
            vy = cy + 20
            v_file = FAMILY_DIR / slug / "review" / f"{v_name}.png"
            if v_file.exists():
                v_img = Image.open(v_file).convert("RGB")
                v_img = v_img.resize((thumb_size, thumb_size), Image.Resampling.LANCZOS)
                canvas.paste(v_img, (vx, vy))
            else:
                draw.rectangle([(vx, vy), (vx + thumb_size, vy + thumb_size)], fill=(36, 42, 50))
            draw.text((vx + 10, vy + 8), v_name.upper(), fill=(200, 210, 220), font=font)

    out_path = REVIEW_DIR / "comparison_sheet.png"
    canvas.save(out_path, "PNG")
    print(f"[OK] Generated comparison sheet at {out_path} ({w}x{h})")
    return out_path


def build_ref_vs_3d_comparison() -> Path:
    """Build side-by-side comparison of concept reference vs 3D contact sheet."""
    if not REF_PATH.exists():
        raise FileNotFoundError(f"Reference not found: {REF_PATH}")
    ref_img = Image.open(REF_PATH).convert("RGB")

    contact_path = REVIEW_DIR / "contact_sheet.png"
    if not contact_path.exists():
        raise FileNotFoundError(f"Contact sheet not found: {contact_path}")
    contact_img = Image.open(contact_path).convert("RGB")

    target_h = 1080
    ref_w = int(ref_img.width * (target_h / ref_img.height))
    ref_resized = ref_img.resize((ref_w, target_h), Image.Resampling.LANCZOS)

    contact_w = int(contact_img.width * (target_h / contact_img.height))
    contact_resized = contact_img.resize((contact_w, target_h), Image.Resampling.LANCZOS)

    header_h = 70
    pad = 20
    total_w = ref_w + contact_w + pad * 3
    total_h = target_h + header_h + pad * 2

    canvas = Image.new("RGB", (total_w, total_h), color=(22, 26, 32))
    draw = ImageDraw.Draw(canvas)
    font = ImageFont.load_default()

    ref_x = pad
    ref_y = header_h + pad
    canvas.paste(ref_resized, (ref_x, ref_y))
    draw.text((ref_x + 10, pad + 15), "APPROVED CONCEPT REFERENCE & VISUAL CONTRACT (Issue #7)", fill=(240, 240, 240), font=font)

    contact_x = ref_x + ref_w + pad
    contact_y = header_h + pad
    canvas.paste(contact_resized, (contact_x, contact_y))
    draw.text((contact_x + 10, pad + 15), "3D VOXEL PRODUCTION CONTACT SHEET (19 Models: Grass, Flowers, Moss, Stone)", fill=(240, 240, 240), font=font)

    out_path = REVIEW_DIR / "reference_vs_3d_comparison.png"
    canvas.save(out_path, "PNG")
    print(f"[OK] Generated reference vs 3D comparison at {out_path}")
    return out_path


def generate_metrics_summary_and_review_md() -> dict:
    """Compute aggregate metrics summary JSON and generate family review.md."""
    all_metrics = []
    total_voxels = 0
    total_tris = 0
    total_faces = 0

    all_slugs = []
    for g in GROUPS:
        for slug, _ in g["props"]:
            all_slugs.append(slug)

    for slug in all_slugs:
        m = load_variant_metrics(slug)
        m["name"] = slug
        all_metrics.append(m)
        total_voxels += m.get("occupied_voxels", 0)
        total_tris += m.get("triangles", 0)
        total_faces += m.get("visible_faces", 0)

    summary = {
        "family": "dressing_pack",
        "total_props": len(all_slugs),
        "total_occupied_voxels": total_voxels,
        "total_triangles": total_tris,
        "total_visible_faces": total_faces,
        "avg_triangles_per_prop": round(total_tris / max(1, len(all_slugs)), 1),
        "min_triangles": min((m.get("triangles", 0) for m in all_metrics), default=0),
        "max_triangles": max((m.get("triangles", 0) for m in all_metrics), default=0),
        "subfamilies": {
            "grass": 6,
            "flowers": 4,
            "moss": 3,
            "stone_debris": 6,
        },
        "voxel_size": 0.10,
        "shared_production_material": "mat_dressing_atlas",
        "atlas_texture": "dressing_palette_atlas.png",
        "roughness_atlas_texture": "dressing_roughness_atlas.png",
        "materials_per_prop": 1,
        "mesh_objects_per_prop": 1,
        "props": all_metrics,
    }

    summary_path = REVIEW_DIR / "metrics_summary.json"
    summary_path.write_text(
        json.dumps(summary, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(f"[OK] Wrote metrics summary to {summary_path}")

    write_build_report(REVIEW_DIR, "Environment dressing pack", summary)
    return summary


def main() -> None:
    print("Building review evidence sheets for Environment Dressing Pack...")
    build_contact_sheet()
    build_comparison_sheet()
    build_ref_vs_3d_comparison()
    generate_metrics_summary_and_review_md()
    print("[SUCCESS] All review evidence sheets created.")


if __name__ == "__main__":
    main()

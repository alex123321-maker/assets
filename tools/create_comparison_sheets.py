#!/usr/bin/env python3
"""Generate side-by-side review comparison sheets against approved concept reference.

Produces:
  1. assets/environment/destructible_rock/review/reference_vs_3d_comparison.png
     - Side-by-side comparison of concept sheet vs 3D family contact sheet
  2. assets/environment/destructible_rock/review/stage_1_comparison.png
     - Enlarged side-by-side comparison of Stage 1 concept rocks vs 3D ISO renders
"""

from __future__ import annotations

from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
FAMILY_DIR = ROOT / "assets" / "environment" / "destructible_rock"
REF_PATH = FAMILY_DIR / "references" / "rock_concept_reference.png"
REVIEW_DIR = FAMILY_DIR / "review"


def create_family_comparison() -> Path:
    ref_img = Image.open(REF_PATH).convert("RGB")
    contact_path = REVIEW_DIR / "contact_sheet.png"
    if not contact_path.exists():
        raise FileNotFoundError(f"Contact sheet not found: {contact_path}")
    contact_img = Image.open(contact_path).convert("RGB")

    # Resize both to equal height for balanced side-by-side view
    target_h = 1080
    ref_w = int(ref_img.width * (target_h / ref_img.height))
    ref_resized = ref_img.resize((ref_w, target_h), Image.Resampling.LANCZOS)

    contact_w = int(contact_img.width * (target_h / contact_img.height))
    contact_resized = contact_img.resize((contact_w, target_h), Image.Resampling.LANCZOS)

    header_h = 70
    pad = 20
    total_w = ref_w + contact_w + pad * 3
    total_h = target_h + header_h + pad * 2

    canvas = Image.new("RGB", (total_w, total_h), color=(32, 36, 42))
    draw = ImageDraw.Draw(canvas)

    # Titles
    font_large = ImageFont.load_default()

    # Left box (Reference)
    ref_x = pad
    ref_y = header_h + pad
    canvas.paste(ref_resized, (ref_x, ref_y))
    draw.text((ref_x + 10, pad + 15), "CONCEPT REFERENCE (approval recorded separately) (Cube Siege Rock Asset Family)", fill=(240, 240, 240), font=font_large)

    # Right box (3D Render)
    contact_x = ref_x + ref_w + pad
    contact_y = header_h + pad
    canvas.paste(contact_resized, (contact_x, contact_y))
    draw.text((contact_x + 10, pad + 15), "3D VOXEL FAMILY PRODUCTION (17 Variants across 5 Stages)", fill=(240, 240, 240), font=font_large)

    out_path = REVIEW_DIR / "reference_vs_3d_comparison.png"
    canvas.save(out_path, quality=95)
    print(f"[OK] Generated: {out_path}")
    return out_path


def create_stage_1_comparison() -> Path:
    ref_img = Image.open(REF_PATH).convert("RGB")

    # Concept crops for 6 Stage 1 rocks
    # Stage 1 column: x ~= 20..260, y ~= 150..520
    crops_box = [
        (15, 200, 155, 345),  # Var 1 (Row 1 Left)
        (155, 200, 315, 345), # Var 2 (Row 1 Right)
        (15, 350, 155, 495),  # Var 3 (Row 2 Left)
        (155, 350, 315, 495), # Var 4 (Row 2 Right)
        (15, 495, 155, 640),  # Var 5 (Row 3 Left)
        (155, 495, 315, 640), # Var 6 (Row 3 Right)
    ]

    var_names = [
        ("stage_1_var_1", "Var 1 - Monolith Crag"),
        ("stage_1_var_2", "Var 2 - Twin Spire"),
        ("stage_1_var_3", "Var 3 - Slanted Wedge"),
        ("stage_1_var_4", "Var 4 - Cantilever Brow"),
        ("stage_1_var_5", "Var 5 - Three-Lobe Butte"),
        ("stage_1_var_6", "Var 6 - Dual Peak Ridge"),
    ]

    tile_size = 360
    pad = 16
    header_h = 60
    label_h = 35

    total_w = pad + 6 * (tile_size + pad)
    total_h = header_h + 2 * (tile_size + label_h + pad) + pad

    canvas = Image.new("RGB", (total_w, total_h), color=(32, 36, 42))
    draw = ImageDraw.Draw(canvas)
    font = ImageFont.load_default()

    draw.text((pad + 10, 18), "STAGE 1 INTACT BOULDERS: CONCEPT REFERENCE vs 3D VOXEL RENDER", fill=(255, 255, 255), font=font)

    for i, (slug, label) in enumerate(var_names):
        col_x = pad + i * (tile_size + pad)

        # Row 1: Concept crop
        c_box = crops_box[i]
        c_img = ref_img.crop(c_box)
        c_resized = c_img.resize((tile_size, tile_size), Image.Resampling.LANCZOS)
        row1_y = header_h + pad
        canvas.paste(c_resized, (col_x, row1_y))
        draw.text((col_x + 8, row1_y + tile_size + 8), f"CONCEPT: {label}", fill=(180, 200, 220), font=font)

        # Row 2: 3D Render
        r_path = FAMILY_DIR / slug / "review" / "iso.png"
        if not r_path.is_file():
            raise FileNotFoundError(f"Missing required review input: {r_path}")
        if r_path.exists():
            r_img = Image.open(r_path).convert("RGB")
            r_resized = r_img.resize((tile_size, tile_size), Image.Resampling.LANCZOS)
            row2_y = row1_y + tile_size + label_h + pad
            canvas.paste(r_resized, (col_x, row2_y))
            draw.text((col_x + 8, row2_y + tile_size + 8), f"3D RENDER: {label}", fill=(220, 240, 180), font=font)

    out_path = REVIEW_DIR / "stage_1_comparison.png"
    canvas.save(out_path, quality=95)
    print(f"[OK] Generated: {out_path}")
    return out_path


def main() -> None:
    print("Generating review comparison sheets...")
    REVIEW_DIR.mkdir(parents=True, exist_ok=True)
    create_family_comparison()
    create_stage_1_comparison()
    print("[ALL DONE] Comparison sheets created successfully.")


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""Generate side-by-side review comparison sheets against approved concept reference for Tree Oak Family.

Produces:
  1. assets/environment/tree_oak/review/reference_vs_3d_comparison.png
     - Side-by-side comparison of concept sheet vs 3D family contact sheet / comparison lineup.
  2. assets/environment/tree_oak/review/variants_concept_vs_3d.png
     - Direct side-by-side comparison of each individual concept tree vs 3D ISO renders.
"""

from __future__ import annotations

from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
FAMILY_DIR = ROOT / "assets" / "environment" / "tree_oak"
REF_PATH = FAMILY_DIR / "references" / "tree_concept_reference.png"
REVIEW_DIR = FAMILY_DIR / "review"


def create_family_comparison() -> Path:
    if not REF_PATH.exists():
        raise FileNotFoundError(f"Concept reference not found: {REF_PATH}")
    ref_img = Image.open(REF_PATH).convert("RGB")

    contact_path = REVIEW_DIR / "comparison_sheet.png"
    if not contact_path.exists():
        contact_path = REVIEW_DIR / "contact_sheet.png"
    if not contact_path.exists():
        raise FileNotFoundError(f"3D render sheet not found in: {REVIEW_DIR}")
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

    font_large = ImageFont.load_default()

    # Left box (Reference)
    ref_x = pad
    ref_y = header_h + pad
    canvas.paste(ref_resized, (ref_x, ref_y))
    draw.text(
        (ref_x + 10, pad + 15),
        "CONCEPT REFERENCE (approval recorded separately) (Cube Siege Oak Tree Family — slots 0..4)",
        fill=(240, 240, 240),
        font=font_large,
    )

    # Right box (3D Production Render)
    contact_x = ref_x + ref_w + pad
    contact_y = header_h + pad
    canvas.paste(contact_resized, (contact_x, contact_y))
    draw.text(
        (contact_x + 10, pad + 15),
        "3D VOXEL RENDER LINEUP (Standard, Tall, Broad, Young, Shrub)",
        fill=(240, 240, 240),
        font=font_large,
    )

    out_path = REVIEW_DIR / "reference_vs_3d_comparison.png"
    canvas.save(out_path, quality=95)
    print(f"[OK] Generated: {out_path}")
    return out_path


def create_variants_comparison() -> Path:
    if not REF_PATH.exists():
        raise FileNotFoundError(f"Concept reference not found: {REF_PATH}")
    ref_img = Image.open(REF_PATH).convert("RGB")

    variant_specs = [
        ("var_0_standard_oak", "Slot 0: Standard Oak", (15, 110, 230, 440)),
        ("var_1_tall_oak", "Slot 1: Tall Oak", (230, 90, 395, 440)),
        ("var_2_broad_oak", "Slot 2: Broad Oak", (390, 130, 675, 440)),
        ("var_3_young_oak", "Slot 3: Young Oak", (680, 230, 805, 440)),
        ("var_4_shrub_oak", "Slot 4: Shrub Oak", (815, 250, 975, 440)),
    ]

    cell_w = 400
    cell_h = 420
    pad = 16
    header_h = 60
    label_h = 30

    total_w = pad + len(variant_specs) * (cell_w + pad)
    total_h = header_h + 2 * (cell_h + label_h + pad) + pad

    canvas = Image.new("RGB", (total_w, total_h), color=(32, 36, 42))
    draw = ImageDraw.Draw(canvas)
    font = ImageFont.load_default()

    draw.text(
        (pad + 10, pad + 10),
        "CUBE SIEGE OAK TREE FAMILY: 5-VARIANT CONCEPT VS 3D ISO COMPARISON",
        fill=(250, 250, 250),
        font=font,
    )

    for col_idx, (slug, label, crop_box) in enumerate(variant_specs):
        x = pad + col_idx * (cell_w + pad)

        # 1. Concept Crop (Row 1)
        y_top = header_h + pad
        draw.text((x + 8, y_top - 22), f"CONCEPT: {label}", fill=(210, 210, 210), font=font)
        crop = ref_img.crop(crop_box)
        # Fit into cell keeping aspect ratio
        crop.thumbnail((cell_w, cell_h), Image.Resampling.LANCZOS)
        cx = x + (cell_w - crop.width) // 2
        cy = y_top + (cell_h - crop.height) // 2
        canvas.paste(crop, (cx, cy))

        # 2. 3D ISO Render (Row 2)
        y_bot = header_h + pad + cell_h + label_h + pad
        draw.text((x + 8, y_bot - 22), f"3D VOXEL: {slug}", fill=(210, 210, 210), font=font)
        iso_path = FAMILY_DIR / slug / "review" / "iso.png"
        if not iso_path.is_file():
            raise FileNotFoundError(f"Missing required review input: {iso_path}")
        if iso_path.exists():
            iso_img = Image.open(iso_path).convert("RGB")
            iso_img.thumbnail((cell_w, cell_h), Image.Resampling.LANCZOS)
            ix = x + (cell_w - iso_img.width) // 2
            iy = y_bot + (cell_h - iso_img.height) // 2
            canvas.paste(iso_img, (ix, iy))

    out_path = REVIEW_DIR / "variants_concept_vs_3d.png"
    canvas.save(out_path, quality=95)
    print(f"[OK] Generated: {out_path}")
    return out_path


def main() -> None:
    REVIEW_DIR.mkdir(parents=True, exist_ok=True)
    create_family_comparison()
    create_variants_comparison()


if __name__ == "__main__":
    main()

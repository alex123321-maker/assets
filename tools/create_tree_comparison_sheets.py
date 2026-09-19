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
        "APPROVED CONCEPT REFERENCE (Cube Siege Oak Tree Family — slots 0..4)",
        fill=(240, 240, 240),
        font=font_large,
    )

    # Right box (3D Production Render)
    contact_x = ref_x + ref_w + pad
    contact_y = header_h + pad
    canvas.paste(contact_resized, (contact_x, contact_y))
    draw.text(
        (contact_x + 10, pad + 15),
        "3D VOXEL PRODUCTION LINEUP (Standard, Tall, Broad, Young, Shrub)",
        fill=(240, 240, 240),
        font=font_large,
    )

    out_path = REVIEW_DIR / "reference_vs_3d_comparison.png"
    canvas.save(out_path, quality=95)
    print(f"[OK] Generated: {out_path}")
    return out_path


def main() -> None:
    REVIEW_DIR.mkdir(parents=True, exist_ok=True)
    create_family_comparison()


if __name__ == "__main__":
    main()

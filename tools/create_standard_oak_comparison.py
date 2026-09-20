#!/usr/bin/env python3
"""Generate side-by-side Before/After comparison for Standard Oak (Issue #14).

Compares:
  - Before: assets/environment/tree_oak/var_0_standard_oak/references/before_iso.png
  - After:  assets/environment/tree_oak/var_0_standard_oak/review/iso.png
Outputs:
  - assets/environment/tree_oak/var_0_standard_oak/review/before_after.png
"""

from __future__ import annotations

import sys
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

REPO_ROOT = Path(__file__).resolve().parent.parent
VAR_DIR = REPO_ROOT / "assets" / "environment" / "tree_oak" / "var_0_standard_oak"
BEFORE_PATH = VAR_DIR / "references" / "before_iso.png"
AFTER_PATH = VAR_DIR / "review" / "iso.png"
OUTPUT_PATH = VAR_DIR / "review" / "before_after.png"


def generate_comparison() -> Path:
    if not BEFORE_PATH.exists():
        raise FileNotFoundError(f"Missing before image: {BEFORE_PATH}")
    if not AFTER_PATH.exists():
        raise FileNotFoundError(f"Missing after image: {AFTER_PATH}")

    before_img = Image.open(BEFORE_PATH).convert("RGB")
    after_img = Image.open(AFTER_PATH).convert("RGB")

    # Render dimensions
    img_w, img_h = before_img.size
    pad = 24
    header_h = 90
    footer_h = 100
    total_w = pad * 3 + img_w * 2
    total_h = header_h + img_h + footer_h + pad

    canvas = Image.new("RGB", (total_w, total_h), color=(18, 20, 24))
    draw = ImageDraw.Draw(canvas)
    font = ImageFont.load_default()

    # Header
    title = "CUBE SIEGE - STANDARD OAK (var_0_standard_oak): BEFORE VS AFTER"
    subtitle = "Identical review camera (ortho), lighting, scale and background | Issue #14 Quality Gate Pilot"
    draw.text((pad, pad), title, fill=(245, 245, 245), font=font)
    draw.text((pad, pad + 24), subtitle, fill=(170, 180, 195), font=font)

    # Left: Before image
    left_x = pad
    img_y = header_h
    canvas.paste(before_img, (left_x, img_y))

    # Right: After image
    right_x = pad * 2 + img_w
    canvas.paste(after_img, (right_x, img_y))

    # Border outlines around panels
    draw.rectangle([left_x - 1, img_y - 1, left_x + img_w, img_y + img_h], outline=(55, 60, 70), width=1)
    draw.rectangle([right_x - 1, img_y - 1, right_x + img_w, img_y + img_h], outline=(65, 110, 75), width=2)

    # Panel Subheaders
    draw.text((left_x + 8, img_y + 8), "BEFORE (Commit 8248bde)", fill=(240, 160, 140), font=font)
    draw.text((right_x + 8, img_y + 8), "AFTER (Revised Standard Oak)", fill=(140, 230, 150), font=font)

    # Footers with detailed observations
    foot_y = img_y + img_h + 12
    draw.text((left_x, foot_y), "[BEFORE OBSERVATIONS]", fill=(240, 160, 140), font=font)
    draw.text((left_x, foot_y + 18), "- Upper masses merge into a vertical pillar / single tall cylinder", fill=(200, 200, 200), font=font)
    draw.text((left_x, foot_y + 34), "- Major boughs obscured beneath low foliage; no visible supports in ISO", fill=(200, 200, 200), font=font)
    draw.text((left_x, foot_y + 50), "- Raw sRGB hex divided by 255 into linear shader (washed out pale green)", fill=(200, 200, 200), font=font)

    draw.text((right_x, foot_y), "[AFTER OBSERVATIONS]", fill=(140, 230, 150), font=font)
    draw.text((right_x, foot_y + 18), "- 5 articulated volumetric lobes with distinct negative space crevices", fill=(200, 200, 200), font=font)
    draw.text((right_x, foot_y + 34), "- Prominent wooden boughs radiating from trunk to visibly cradle canopy", fill=(200, 200, 200), font=font)
    draw.text((right_x, foot_y + 50), "- Exact IEC 61966-2-1 linear PBR palette (#4a2f1b, #3b6b22, #5e932b)", fill=(200, 200, 200), font=font)

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    canvas.save(OUTPUT_PATH, quality=95)
    print(f"[OK] Generated Before/After comparison: {OUTPUT_PATH}")
    return OUTPUT_PATH


if __name__ == "__main__":
    generate_comparison()

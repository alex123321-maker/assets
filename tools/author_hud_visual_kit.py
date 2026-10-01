#!/usr/bin/env python3
"""HUD Visual Kit Authoring & Review Pipeline for Cube Siege.

Builds all icons, frames, status bars, packed atlas, naming map,
Godot 9-patch metadata, and comprehensive review mockups.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from pipeline_reports import write_build_report
from typing import Dict

from PIL import Image, ImageDraw, ImageFont

# Import sub-modules
from hud_frames_builder import (
    render_action_slot,
    render_cooldown_mask,
    render_keycap,
    render_bar,
    render_day_night_panel_frame,
    render_resource_panel_frame,
    render_tooltip_frame,
    GODOT_9PATCH_SLICES,
    get_font,
    hex_to_rgba,
)

REPO_ROOT = Path(__file__).resolve().parent.parent
ASSET_DIR = REPO_ROOT / "assets" / "ui" / "hud_visual_kit"
OUTPUT_DIR = ASSET_DIR / "output"
ICONS_DIR = OUTPUT_DIR / "icons"
FRAMES_DIR = OUTPUT_DIR / "frames"
BARS_DIR = OUTPUT_DIR / "bars"
ATLAS_DIR = OUTPUT_DIR / "atlas"
REVIEW_DIR = ASSET_DIR / "review"
SOURCE_DIR = ASSET_DIR / "source"


ICON_CATALOG: Dict[str, Dict[str, str]] = {
    "resource_wood": {"name": "Дерево", "action": "Ресурс"},
    "resource_stone": {"name": "Камень", "action": "Ресурс"},
    "resource_iron": {"name": "Железо", "action": "Ресурс"},
    "resource_magic_stone": {"name": "Магический камень", "action": "Ресурс"},
    "global_day": {"name": "День", "action": "Фаза суток"},
    "global_night": {"name": "Ночь", "action": "Фаза суток"},
    "global_settings": {"name": "Настройки", "action": "Пауза / настройки"},
    "global_build": {"name": "Строительство", "action": "TAB: режим строительства"},
    "warrior_sword_attack": {"name": "Меч", "action": "ЛКМ: базовая атака"},
    "warrior_cleave": {"name": "Рассечение", "action": "ПКМ: особая атака"},
    "warrior_dash": {"name": "Рывок", "action": "SPACE: рывок"},
    "warrior_parry": {"name": "Парирование", "action": "Q: парирование щитом"},
    "warrior_duel": {"name": "Дуэль", "action": "F: вызов на дуэль"},
    "archer_shot": {"name": "Выстрел", "action": "ЛКМ: базовая атака"},
    "archer_piercing_shot": {"name": "Пробивающий выстрел", "action": "ПКМ: особая атака"},
    "archer_roll": {"name": "Кувырок", "action": "SPACE: уклонение"},
    "archer_decoy": {"name": "Приманка", "action": "Q: приманка"},
    "archer_eagle_eye": {"name": "Орлиный глаз", "action": "F: Eagle Eye"},
    "engineer_hammer": {"name": "Молот", "action": "ЛКМ: базовая атака"},
    "engineer_turret": {"name": "Турель", "action": "ПКМ: особая атака"},
    "engineer_dash": {"name": "Реактивный рывок", "action": "SPACE: рывок"},
    "engineer_mine": {"name": "Мина", "action": "Q: установить / подорвать"},
    "engineer_tactical_nuke": {"name": "Тактический заряд", "action": "F: Tactical Nuke"},
}


def ensure_dirs() -> None:
    for directory in (ICONS_DIR, FRAMES_DIR, BARS_DIR, ATLAS_DIR, REVIEW_DIR, SOURCE_DIR):
        directory.mkdir(parents=True, exist_ok=True)


def _normalized_master(source: Path) -> Image.Image:
    """Load an immutable ImageGen master and fit its full silhouette into a padded square."""
    with Image.open(source) as opened:
        if opened.mode != "RGBA":
            raise ValueError(f"ImageGen master must preserve RGBA alpha: {source.name} ({opened.mode})")
        if opened.width != opened.height:
            raise ValueError(f"ImageGen master must be square: {source.name} ({opened.size})")
        image = opened.copy()
    visible = image.getchannel("A").point(lambda value: 255 if value > 4 else 0)
    bounds = visible.getbbox()
    if bounds is None:
        raise ValueError(f"ImageGen master is fully transparent: {source.name}")
    artwork = image.crop(bounds)
    safe_size = 410  # 80% of the 512px export leaves transparent padding.
    scale = min(safe_size / artwork.width, safe_size / artwork.height)
    size = (max(1, round(artwork.width * scale)), max(1, round(artwork.height * scale)))
    artwork = artwork.resize(size, Image.Resampling.LANCZOS)
    result = Image.new("RGBA", (512, 512), (0, 0, 0, 0))
    result.alpha_composite(artwork, ((512 - size[0]) // 2, (512 - size[1]) // 2))
    return result


def export_icons() -> Dict[str, Image.Image]:
    """Export only the 23 approved ImageGen masters; procedural and SVG paths are disabled."""
    masters_dir = SOURCE_DIR / "imagegen" / "masters"
    expected = {f"{slug}.png" for slug in ICON_CATALOG}
    actual = {path.name for path in masters_dir.glob("*.png")}
    if actual != expected:
        raise ValueError(f"ImageGen master catalog mismatch; missing={sorted(expected-actual)}, unexpected={sorted(actual-expected)}")
    for old in list(ICONS_DIR.glob("*.png")) + list(ICONS_DIR.glob("*.webp")) + list(ICONS_DIR.glob("*.svg")):
        old.unlink()
    print(f"Exporting {len(ICON_CATALOG)} ImageGen masters in multiple resolutions...")
    master_icons: Dict[str, Image.Image] = {}
    for slug in ICON_CATALOG:
        image_512 = _normalized_master(masters_dir / f"{slug}.png")
        master_icons[slug] = image_512
        for size in (256, 128, 64, 32):
            resized = image_512.resize((size, size), Image.Resampling.LANCZOS)
            suffix = "" if size == 256 else f"_{size}"
            resized.save(ICONS_DIR / f"{slug}{suffix}.png", optimize=True)
    print(f"  [PASS] Exported {len(ICON_CATALOG)} ImageGen icons as transparent PNGs (256, 128, 64, 32).")
    return master_icons


def export_naming_map() -> None:
    groups = {
        "resources": ("resource_wood", "resource_stone", "resource_iron", "resource_magic_stone"),
        "global_hud": ("global_day", "global_night", "global_settings", "global_build"),
        "warrior": ("warrior_sword_attack", "warrior_cleave", "warrior_dash", "warrior_parry", "warrior_duel"),
        "archer": ("archer_shot", "archer_piercing_shot", "archer_roll", "archer_decoy", "archer_eagle_eye"),
        "engineer": ("engineer_hammer", "engineer_turret", "engineer_dash", "engineer_mine", "engineer_tactical_nuke"),
    }
    naming_map = {
        category: {slug: {"file": f"{slug}.png", **ICON_CATALOG[slug]} for slug in slugs}
        for category, slugs in groups.items()
    }
    (OUTPUT_DIR / "naming_map.json").write_text(json.dumps(naming_map, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print("  [PASS] 23-entry naming map saved.")


# -------------------------------------------------------------------------
# EXPORT FRAMES & BARS
# -------------------------------------------------------------------------

def export_frames_and_bars() -> None:
    print("Exporting UI frames, action slots, keycaps, and progress bars...")
    # 1. Action slot states (128x128 and 64x64)
    for state in ["normal", "hover", "pressed", "disabled", "cooldown"]:
        f_128 = render_action_slot(state, 128)
        f_128.save(FRAMES_DIR / f"action_slot_{state}.png", optimize=True)
        f_64 = render_action_slot(state, 64)
        f_64.save(FRAMES_DIR / f"action_slot_{state}_64.png", optimize=True)

    # 2. Cooldown mask
    cd_mask = render_cooldown_mask(128)
    cd_mask.save(FRAMES_DIR / "cooldown_mask.png", optimize=True)

    # 3. Keycap frames & badges
    kc_normal = render_keycap("", "normal", 56, 28)
    kc_normal.save(FRAMES_DIR / "keycap_frame_normal.png", optimize=True)
    kc_pressed = render_keycap("", "pressed", 56, 28)
    kc_pressed.save(FRAMES_DIR / "keycap_frame_pressed.png", optimize=True)

    for k in ["LMB", "RMB", "SPACE", "Q", "W", "E", "R", "F", "TAB"]:
        badge = render_keycap(k, "normal", 56, 28)
        badge.save(FRAMES_DIR / f"keycap_{k}.png", optimize=True)

    # 4. Progress Bars
    bar_configs = [
        ("health_bar_bg", render_bar("health", is_fill=False, width=256, height=28)),
        ("health_bar_fill_full", render_bar("health", is_fill=True, width=256, height=28, progress=1.0)),
        ("health_bar_fill_danger", render_bar("health_danger", is_fill=True, width=256, height=28, progress=0.35)),
        ("wave_bar_bg", render_bar("wave", is_fill=False, width=280, height=24)),
        ("wave_bar_fill", render_bar("wave", is_fill=True, width=280, height=24, progress=0.4)),
        ("xp_bar_bg", render_bar("xp", is_fill=False, width=256, height=20)),
        ("xp_bar_fill", render_bar("xp", is_fill=True, width=256, height=20, progress=0.75)),
    ]
    for name, img in bar_configs:
        img.save(BARS_DIR / f"{name}.png", optimize=True)

    # 5. Panels
    dn_panel = render_day_night_panel_frame(420, 110)
    dn_panel.save(FRAMES_DIR / "day_night_panel_frame.png", optimize=True)

    res_panel = render_resource_panel_frame(380, 70)
    res_panel.save(FRAMES_DIR / "resource_panel_frame.png", optimize=True)

    tt_panel = render_tooltip_frame(280, 150)
    tt_panel.save(FRAMES_DIR / "tooltip_frame.png", optimize=True)

    # 6. Slices JSON
    slices_path = OUTPUT_DIR / "hud_slices.json"
    slices_path.write_text(json.dumps(GODOT_9PATCH_SLICES, indent=2), encoding="utf-8")
    print(f"  [PASS] Frames, bars, and 9-patch metadata saved.")



# -------------------------------------------------------------------------
# TEXTURE ATLAS GENERATION
# -------------------------------------------------------------------------

def export_atlas(icons: Dict[str, Image.Image]) -> None:
    print("Packing texture atlas (hud_atlas.png)...")
    # Pack 64x64 icons + frames into a clean 1024x1024 spritesheet
    atlas = Image.new("RGBA", (1024, 1024), (0, 0, 0, 0))
    atlas_map: Dict[str, Dict[str, int]] = {}

    cur_x = 16
    cur_y = 16
    row_height = 0

    # Pack Icons (at 96x96 for crisp atlas resolution)
    for slug in sorted(icons.keys()):
        icon_img = icons[slug].resize((96, 96), Image.Resampling.LANCZOS)
        if cur_x + 96 + 16 > 1024:
            cur_x = 16
            cur_y += row_height + 16
            row_height = 0

        atlas.paste(icon_img, (cur_x, cur_y), icon_img)
        atlas_map[slug] = {"x": cur_x, "y": cur_y, "w": 96, "h": 96}
        cur_x += 96 + 16
        row_height = max(row_height, 96)

    # Next row for frames
    cur_x = 16
    cur_y += row_height + 24
    row_height = 0

    # Pack Action Slots (96x96)
    for state in ["normal", "hover", "pressed", "disabled", "cooldown"]:
        f_img = render_action_slot(state, 96)
        if cur_x + 96 + 16 > 1024:
            cur_x = 16
            cur_y += row_height + 16
            row_height = 0
        atlas.paste(f_img, (cur_x, cur_y), f_img)
        atlas_map[f"slot_{state}"] = {"x": cur_x, "y": cur_y, "w": 96, "h": 96}
        cur_x += 96 + 16
        row_height = max(row_height, 96)

    # Next row for Keycaps
    cur_x = 16
    cur_y += row_height + 24
    row_height = 0
    for k in ["LMB", "RMB", "SPACE", "Q", "W", "E", "R", "F", "TAB"]:
        badge = render_keycap(k, "normal", 56, 28)
        if cur_x + 56 + 12 > 1024:
            cur_x = 16
            cur_y += row_height + 12
            row_height = 0
        atlas.paste(badge, (cur_x, cur_y), badge)
        atlas_map[f"keycap_{k}"] = {"x": cur_x, "y": cur_y, "w": 56, "h": 28}
        cur_x += 56 + 12
        row_height = max(row_height, 28)

    atlas.save(ATLAS_DIR / "hud_atlas.png", optimize=True)
    (ATLAS_DIR / "hud_atlas.json").write_text(json.dumps(atlas_map, indent=2), encoding="utf-8")
    print(f"  [PASS] Texture atlas packed ({len(atlas_map)} elements).")


# -------------------------------------------------------------------------
# REVIEW EVIDENCE MOCKUPS
# -------------------------------------------------------------------------

def build_review_evidence(icons: Dict[str, Image.Image]) -> None:
    """Build review sheets from saved ImageGen masters and permitted UI frame assets."""
    font_title = get_font(24)
    font_heading = get_font(17)
    font_label = get_font(12)
    font_bold = get_font(14)
    categories = [
        ("RESOURCES", ["resource_wood", "resource_stone", "resource_iron", "resource_magic_stone"]),
        ("GLOBAL HUD", ["global_day", "global_night", "global_settings"]),
        ("BUILD", ["global_build"]),
        ("WARRIOR", ["warrior_sword_attack", "warrior_cleave", "warrior_dash", "warrior_parry", "warrior_duel"]),
        ("ARCHER", ["archer_shot", "archer_piercing_shot", "archer_roll", "archer_decoy", "archer_eagle_eye"]),
        ("ENGINEER", ["engineer_hammer", "engineer_turret", "engineer_dash", "engineer_mine", "engineer_tactical_nuke"]),
    ]

    contact = Image.new("RGBA", (1540, 840), hex_to_rgba("#0B111A"))
    draw = ImageDraw.Draw(contact)
    draw.text((36, 22), "CUBE SIEGE — IMAGEGEN HUD ICONS", fill=hex_to_rgba("#F8FAFC"), font=font_title)
    draw.text((36, 56), "Issue #52 · 23 unique masters · technical PNG exports · no procedural or SVG icons",
              fill=hex_to_rgba("#94A3B8"), font=font_bold)
    y = 98
    for category, slugs in categories:
        draw.text((36, y), category, fill=hex_to_rgba("#38BDF8"), font=font_heading)
        y += 27
        for index, slug in enumerate(slugs):
            x = 36 + index * 300
            frame = render_action_slot("normal", 82)
            contact.alpha_composite(frame, (x, y))
            icon = icons[slug].resize((62, 62), Image.Resampling.LANCZOS)
            contact.alpha_composite(icon, (x + 10, y + 10))
            draw.text((x + 98, y + 7), ICON_CATALOG[slug]["name"], fill=hex_to_rgba("#F1F5F9"), font=font_bold)
            draw.text((x + 98, y + 29), slug, fill=hex_to_rgba("#64748B"), font=font_label)
            draw.text((x + 98, y + 49), ICON_CATALOG[slug]["action"], fill=hex_to_rgba("#94A3B8"), font=font_label)
        y += 95
    contact.save(REVIEW_DIR / "contact_sheet.png", optimize=True)

    def readability_sheet(size: int, filename: str) -> None:
        columns, cell_w, cell_h = 8, 132, 104
        rows = (len(ICON_CATALOG) + columns - 1) // columns
        sheet = Image.new("RGBA", (columns * cell_w + 40, 88 + rows * cell_h), hex_to_rgba("#0B111A"))
        canvas = ImageDraw.Draw(sheet)
        canvas.text((20, 18), f"HUD IMAGEGEN ICONS — {size}px READABILITY", fill=hex_to_rgba("#F8FAFC"), font=font_heading)
        canvas.text((20, 46), "Transparent PNG exports shown at target display size", fill=hex_to_rgba("#94A3B8"), font=font_label)
        for index, slug in enumerate(ICON_CATALOG):
            col, row = index % columns, index // columns
            x, y = 20 + col * cell_w, 80 + row * cell_h
            frame_size = size + 12
            frame = render_action_slot("normal", frame_size)
            sheet.alpha_composite(frame, (x + (cell_w - frame_size) // 2, y))
            icon = icons[slug].resize((size, size), Image.Resampling.LANCZOS)
            sheet.alpha_composite(icon, (x + (cell_w - size) // 2, y + 6))
            canvas.text((x + 2, y + frame_size + 4), slug[:19], fill=hex_to_rgba("#CBD5E1"), font=font_label)
        sheet.save(REVIEW_DIR / filename, optimize=True)

    readability_sheet(64, "readability_64px.png")
    readability_sheet(32, "readability_32px.png")

    def render_class_strip(class_name: str, slugs: list[str], keys: list[str], filename: str) -> None:
        width, height = 800, 200
        strip = Image.new("RGBA", (width, height), hex_to_rgba("#0B111A"))
        canvas = ImageDraw.Draw(strip)
        canvas.text((28, 18), f"{class_name.upper()} — ACTION BAR STRIP", fill=hex_to_rgba("#F8FAFC"), font=font_heading)
        for index, slug in enumerate(slugs):
            x = 28 + index * 122
            frame = render_action_slot("normal", 70)
            strip.alpha_composite(frame, (x + 8, 48))
            icon = icons[slug].resize((52, 52), Image.Resampling.LANCZOS)
            strip.alpha_composite(icon, (x + 17, 57))
            key = render_keycap(keys[index], "normal", 52, 24)
            strip.alpha_composite(key, (x + 17, 121))
            display_names = {
                "archer_piercing_shot": "Пробивающий\nвыстрел",
                "engineer_dash": "Реактивный\nрывок",
                "engineer_tactical_nuke": "Тактический\nзаряд",
            }
            label = display_names.get(slug, ICON_CATALOG[slug]["name"])
            bounds = canvas.multiline_textbbox((0, 0), label, font=font_label, align="center", spacing=1)
            label_x = x + max(0, (122 - (bounds[2] - bounds[0])) // 2)
            canvas.multiline_text((label_x, 153), label, fill=hex_to_rgba("#CBD5E1"), font=font_label, align="center", spacing=1)
        strip.save(REVIEW_DIR / filename, optimize=True)

    for class_name, prefix, filename, keys in (
        ("Warrior", "warrior", "mockup_warrior_hud.png", ["ЛКМ", "ПКМ", "SPACE", "Q", "F"]),
        ("Archer", "archer", "mockup_archer_hud.png", ["ЛКМ", "ПКМ", "SPACE", "Q", "F"]),
        ("Engineer", "engineer", "mockup_engineer_hud.png", ["ЛКМ", "ПКМ", "SPACE", "Q", "F"]),
    ):
        slugs = [slug for slug in ICON_CATALOG if slug.startswith(prefix + "_")]
        render_class_strip(class_name, slugs, keys, filename)

    global_sheet = Image.new("RGBA", (720, 190), hex_to_rgba("#0B111A"))
    canvas = ImageDraw.Draw(global_sheet)
    canvas.text((28, 18), "DAY / NIGHT / SETTINGS / BUILD COMPONENT ART", fill=hex_to_rgba("#F8FAFC"), font=font_heading)
    for index, slug in enumerate(("global_day", "global_night", "global_settings", "global_build")):
        icon = icons[slug].resize((72, 72), Image.Resampling.LANCZOS)
        global_sheet.alpha_composite(icon, (45 + index * 165, 62))
        canvas.text((40 + index * 165, 142), ICON_CATALOG[slug]["name"], fill=hex_to_rgba("#CBD5E1"), font=font_label)
    global_sheet.save(REVIEW_DIR / "mockup_day_night_panel.png", optimize=True)

    resource_sheet = Image.new("RGBA", (720, 190), hex_to_rgba("#0B111A"))
    canvas = ImageDraw.Draw(resource_sheet)
    canvas.text((28, 18), "RESOURCE ICON + COUNTER LAYOUT STUDY", fill=hex_to_rgba("#F8FAFC"), font=font_heading)
    for index, slug in enumerate(("resource_wood", "resource_stone", "resource_iron", "resource_magic_stone")):
        x = 24 + index * 170
        canvas.rounded_rectangle((x, 58, x + 154, 132), radius=9,
                                 fill=hex_to_rgba("#111B28"), outline=hex_to_rgba("#30465F"), width=2)
        icon = icons[slug].resize((50, 50), Image.Resampling.LANCZOS)
        resource_sheet.alpha_composite(icon, (x + 10, 70))
        canvas.text((x + 70, 82), "999", fill=hex_to_rgba("#F8FAFC"), font=font_bold)
    resource_sheet.save(REVIEW_DIR / "mockup_resource_panel.png", optimize=True)


# -------------------------------------------------------------------------
# METRICS & REVIEW DOCUMENTATION
# -------------------------------------------------------------------------

def export_metrics_and_review(icons: Dict[str, Image.Image]) -> None:
    print("Generating metrics.json and build_report.md...")
    # Gather metrics
    icon_count = len(icons)
    total_pngs = len(list(ICONS_DIR.glob("*.png")))
    total_frames = len(list(FRAMES_DIR.glob("*.png")))
    total_bars = len(list(BARS_DIR.glob("*.png")))

    metrics = {
        "kit_name": "hud_visual_kit",
        "total_unique_icons": icon_count,
        "categories": {
            "resource": 4,
            "global_hud": 3,
            "build": 1,
            "warrior": 5,
            "archer": 5,
            "engineer": 5,
        },
        "resolutions_provided": [256, 128, 64, 32],
        "total_icon_files": total_pngs,
        "total_frame_files": total_frames,
        "total_bar_files": total_bars,
        "atlas": {
            "dimensions": "1024x1024",
            "file": "output/atlas/hud_atlas.png",
            "metadata": "output/atlas/hud_atlas.json",
        },
        "godot_integration": {
            "ninepatch_slices_file": "output/hud_slices.json",
            "slices_count": len(GODOT_9PATCH_SLICES),
        },
        "review_evidence": {
            "contact_sheet": "review/contact_sheet.png",
            "readability_64px": "review/readability_64px.png",
            "readability_32px": "review/readability_32px.png",
            "mockup_warrior_hud": "review/mockup_warrior_hud.png",
            "mockup_archer_hud": "review/mockup_archer_hud.png",
            "mockup_engineer_hud": "review/mockup_engineer_hud.png",
            "mockup_day_night_panel": "review/mockup_day_night_panel.png",
            "mockup_resource_panel": "review/mockup_resource_panel.png",
        },
        "visual_review_status": "recorded in review/visual_review.json",
        "engine_verification_status": "not_checked; see the game runtime review for Issue #52",
    }

    metrics_path = REVIEW_DIR / "metrics.json"
    metrics_path.write_text(json.dumps(metrics, indent=2), encoding="utf-8")

    write_build_report(REVIEW_DIR, "HUD visual kit", metrics)


# -------------------------------------------------------------------------
# MAIN
# -------------------------------------------------------------------------

def main() -> int:
    ensure_dirs()
    icons = export_icons()
    export_frames_and_bars()
    export_naming_map()
    export_atlas(icons)
    build_review_evidence(icons)
    export_metrics_and_review(icons)
    print("\n[SUCCESS] HUD Visual Kit build pipeline completed cleanly.")
    return 0


if __name__ == "__main__":
    sys.exit(main())

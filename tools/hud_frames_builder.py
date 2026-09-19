#!/usr/bin/env python3
"""HUD Frames & UI Elements Builder for Cube Siege UI Kit.

Generates reusable action slot states, keycaps, progress bar frames,
day/night header, resource container, and Godot 9-patch slice metadata.
"""

from __future__ import annotations

import math
from typing import Dict, Tuple
from PIL import Image, ImageDraw, ImageFilter, ImageFont


def hex_to_rgba(hex_code: str, alpha: int = 255) -> Tuple[int, int, int, int]:
    hex_code = hex_code.lstrip("#")
    return (int(hex_code[0:2], 16), int(hex_code[2:4], 16), int(hex_code[4:6], 16), alpha)


def get_font(size: int = 16) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    for font_path in ["C:/Windows/Fonts/segoeuib.ttf", "C:/Windows/Fonts/arialbd.ttf", "C:/Windows/Fonts/arial.ttf"]:
        try:
            return ImageFont.truetype(font_path, size)
        except Exception:
            continue
    return ImageFont.load_default()


# -------------------------------------------------------------------------
# ACTION SLOT FRAMES (5 STATES)
# -------------------------------------------------------------------------

def render_action_slot(state: str = "normal", size: int = 128) -> Image.Image:
    """Render square action slot frame (normal, hover, pressed, disabled, cooldown)."""
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    scale = size / 128.0
    draw = ImageDraw.Draw(img)

    f_dark = hex_to_rgba("#090D14")
    f_body = hex_to_rgba("#131C28")
    f_border = hex_to_rgba("#26384E")
    f_rim = hex_to_rgba("#3B5370")
    f_inner = hex_to_rgba("#0C131D")

    glow_color = None
    if state == "hover":
        glow_color = hex_to_rgba("#38BDF8", 80)
        f_rim = hex_to_rgba("#38BDF8")
        f_border = hex_to_rgba("#0284C7")
    elif state in ("pressed", "selected"):
        glow_color = hex_to_rgba("#F59E0B", 90)
        f_rim = hex_to_rgba("#FBBF24")
        f_border = hex_to_rgba("#D97706")
        f_inner = hex_to_rgba("#172033")
    elif state == "disabled":
        f_body = hex_to_rgba("#0F141C")
        f_border = hex_to_rgba("#1E2530")
        f_rim = hex_to_rgba("#2B3442")
        f_inner = hex_to_rgba("#080B10")

    # Outer bloom if highlighted
    if glow_color:
        glow_layer = Image.new("RGBA", (size, size), (0, 0, 0, 0))
        gdraw = ImageDraw.Draw(glow_layer)
        pad = int(8 * scale)
        gdraw.rounded_rectangle([pad, pad, size - pad, size - pad], radius=int(12 * scale), fill=glow_color)
        blurred = glow_layer.filter(ImageFilter.GaussianBlur(int(6 * scale)))
        img.alpha_composite(blurred)
        img.alpha_composite(blurred)

    # Main outer rounded beveled frame
    m = int(6 * scale)
    draw.rounded_rectangle([m, m, size - m, size - m], radius=int(10 * scale), fill=f_body, outline=f_border, width=int(4 * scale))

    # Outer top-left highlight rim
    draw.rounded_rectangle([m + 2*scale, m + 2*scale, size - m - 2*scale, size - m - 2*scale], radius=int(8 * scale), outline=f_rim, width=int(2 * scale))

    # Inner recessed slot well
    in_m = int(14 * scale)
    draw.rounded_rectangle([in_m, in_m, size - in_m, size - in_m], radius=int(6 * scale), fill=f_inner, outline=f_dark, width=int(3 * scale))

    # Corner Rivets / Accent notches
    rivets = [
        (m + 6*scale, m + 6*scale),
        (size - m - 6*scale, m + 6*scale),
        (m + 6*scale, size - m - 6*scale),
        (size - m - 6*scale, size - m - 6*scale),
    ]
    for rx, ry in rivets:
        draw.ellipse([rx - 2*scale, ry - 2*scale, rx + 2*scale, ry + 2*scale], fill=f_rim)

    # Cooldown overlay state
    if state == "cooldown":
        cd_layer = Image.new("RGBA", (size, size), (0, 0, 0, 0))
        cddraw = ImageDraw.Draw(cd_layer)
        # Semi-transparent dark wash over inner well
        cddraw.rounded_rectangle([in_m, in_m, size - in_m, size - in_m], radius=int(6 * scale), fill=(0, 0, 0, 160))
        # Radial sweep arc (e.g. 240 degrees left)
        cx, cy = size / 2.0, size / 2.0
        r_sweep = (size / 2.0) - in_m
        cddraw.pieslice([cx - r_sweep, cy - r_sweep, cx + r_sweep, cy + r_sweep], start=-90, end=150, fill=(15, 23, 42, 180))
        cddraw.line([(cx, cy), (cx + r_sweep * math.cos(math.radians(150)), cy + r_sweep * math.sin(math.radians(150)))], fill=(56, 189, 248, 220), width=int(3*scale))
        img.alpha_composite(cd_layer)

    return img


# -------------------------------------------------------------------------
# COOLDOWN RADIAL MASK REFERENCE
# -------------------------------------------------------------------------

def render_cooldown_mask(size: int = 128) -> Image.Image:
    """Render a smooth radial countdown sweep mask (0 to 360 deg) for Godot shaders."""
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    scale = size / 128.0
    draw = ImageDraw.Draw(img)
    cx, cy = size / 2.0, size / 2.0
    r = (size / 2.0) - 10 * scale
    draw.pieslice([cx - r, cy - r, cx + r, cy + r], start=-90, end=180, fill=(0, 0, 0, 180))
    draw.line([(cx, cy), (cx, cy - r)], fill=(255, 255, 255, 255), width=int(2*scale))
    draw.line([(cx, cy), (cx, cy + r)], fill=(56, 189, 248, 255), width=int(3*scale))
    return img


# -------------------------------------------------------------------------
# KEYCAP FRAMES & BADGES
# -------------------------------------------------------------------------

def render_keycap(text: str = "", state: str = "normal", width: int = 56, height: int = 28) -> Image.Image:
    """Render metallic beveled keycap badge (e.g. LMB, RMB, SPACE, Q, F, TAB)."""
    img = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    k_bg = hex_to_rgba("#0F172A")
    k_border = hex_to_rgba("#334155")
    k_rim = hex_to_rgba("#64748B")
    k_text = hex_to_rgba("#F8FAFC")

    if state == "pressed":
        k_bg = hex_to_rgba("#1E293B")
        k_border = hex_to_rgba("#F59E0B")
        k_rim = hex_to_rgba("#FBBF24")
        k_text = hex_to_rgba("#FEF08A")

    # Keycap body
    draw.rounded_rectangle([2, 2, width - 2, height - 2], radius=4, fill=k_bg, outline=k_border, width=2)
    # Upper specular bevel
    draw.line([(5, 4), (width - 5, 4)], fill=k_rim, width=1)

    # Key label text
    if text:
        font_size = 14 if len(text) <= 2 else (11 if len(text) <= 3 else 9)
        font = get_font(font_size)
        bbox = draw.textbbox((0, 0), text, font=font)
        tw = bbox[2] - bbox[0]
        th = bbox[3] - bbox[1]
        tx = (width - tw) / 2.0
        ty = (height - th) / 2.0 - 1
        # Text drop shadow
        draw.text((tx + 1, ty + 1), text, fill=(0, 0, 0, 220), font=font)
        draw.text((tx, ty), text, fill=k_text, font=font)

    return img


# -------------------------------------------------------------------------
# STATUS & PROGRESS BARS (HEALTH, WAVE, XP)
# -------------------------------------------------------------------------

def render_bar(bar_type: str = "health", is_fill: bool = False, width: int = 256, height: int = 28, progress: float = 1.0) -> Image.Image:
    """Render progress bar background frame or filled track."""
    img = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    b_dark = hex_to_rgba("#090D14")
    b_border = hex_to_rgba("#334155")
    b_well = hex_to_rgba("#0C131D")

    if not is_fill:
        # Background frame
        draw.rounded_rectangle([2, 2, width - 2, height - 2], radius=6, fill=b_well, outline=b_border, width=3)
        # Inner recessed shadow
        draw.rounded_rectangle([5, 5, width - 5, height - 5], radius=4, fill=b_dark)
        return img

    # Fill track
    pad = 5
    fill_w = max(4, int((width - pad * 2) * progress))

    if bar_type == "health":
        f_top = hex_to_rgba("#34D399")
        f_mid = hex_to_rgba("#10B981")
        f_bottom = hex_to_rgba("#059669")
    elif bar_type == "health_danger":
        f_top = hex_to_rgba("#F87171")
        f_mid = hex_to_rgba("#EF4444")
        f_bottom = hex_to_rgba("#B91C1C")
    elif bar_type == "wave":
        f_top = hex_to_rgba("#FB7185")
        f_mid = hex_to_rgba("#E11D48")
        f_bottom = hex_to_rgba("#9F1239")
    elif bar_type == "xp":
        f_top = hex_to_rgba("#38BDF8")
        f_mid = hex_to_rgba("#0284C7")
        f_bottom = hex_to_rgba("#0369A1")
    else:
        f_top = hex_to_rgba("#FBBF24")
        f_mid = hex_to_rgba("#F59E0B")
        f_bottom = hex_to_rgba("#D97706")

    # Render fill gradient
    fill_img = Image.new("RGBA", (fill_w, height - pad * 2), (0, 0, 0, 0))
    fdraw = ImageDraw.Draw(fill_img)
    fh = height - pad * 2
    for y in range(fh):
        t = y / float(fh)
        if t < 0.35:
            c = f_top
        elif t < 0.7:
            c = f_mid
        else:
            c = f_bottom
        fdraw.line([(0, y), (fill_w, y)], fill=c)

    # Upper specular gloss line
    fdraw.line([(0, 1), (fill_w, 1)], fill=(255, 255, 255, 180), width=1)
    img.paste(fill_img, (pad, pad))

    return img


# -------------------------------------------------------------------------
# COMPACT TOP-CENTER DAY / NIGHT PANEL FRAME
# -------------------------------------------------------------------------

def render_day_night_panel_frame(width: int = 480, height: int = 130) -> Image.Image:
    """Render ornate top-center Day/Night header frame matching the reference."""
    img = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    p_bg = hex_to_rgba("#0D1522")
    p_border = hex_to_rgba("#223348")
    p_rim = hex_to_rgba("#4B6584")
    p_gold = hex_to_rgba("#D4AF37")
    p_dark = hex_to_rgba("#070B11")

    # Main arched banner body
    banner_pts = [
        (30, 12),
        (width - 30, 12),
        (width - 12, 38),
        (width - 24, 72),
        (width - 70, 72),
        (width - 85, 122),
        (85, 122),
        (70, 72),
        (24, 72),
        (12, 38),
    ]
    draw.polygon(banner_pts, fill=p_bg, outline=p_border, width=3)
    # Inner rim line
    draw.line([(35, 16), (width - 35, 16)], fill=p_rim, width=2)

    # Central Timer Aperture Frame
    cx = width / 2.0
    cy = 42.0
    tw, th = 116.0, 38.0
    t_box = [cx - tw/2, cy - th/2, cx + tw/2, cy + th/2]
    draw.rounded_rectangle(t_box, radius=6, fill=p_dark, outline=p_gold, width=2)

    # Left (Sun) Wing bracket & Right (Moon) Wing bracket
    draw.ellipse([52, 24, 88, 60], fill=p_dark, outline=p_border, width=2)
    draw.ellipse([width - 88, 24, width - 52, 60], fill=p_dark, outline=p_border, width=2)

    # Bottom Wave Track Mount Bracket
    bx1, bx2 = 90, width - 90
    by1, by2 = 82, 114
    draw.rounded_rectangle([bx1, by1, bx2, by2], radius=6, fill=p_dark, outline=p_border, width=2)

    return img


# -------------------------------------------------------------------------
# RESOURCE ROW PANEL CONTAINER FRAME
# -------------------------------------------------------------------------

def render_resource_panel_frame(width: int = 460, height: int = 80) -> Image.Image:
    """Render horizontal pill-shaped dark container for resources."""
    img = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    r_bg = hex_to_rgba("#0E1624")
    r_border = hex_to_rgba("#23364C")
    r_rim = hex_to_rgba("#435E7D")
    r_dark = hex_to_rgba("#080D14")

    # Rounded pill container
    draw.rounded_rectangle([4, 4, width - 4, height - 4], radius=10, fill=r_bg, outline=r_border, width=3)
    # Top highlight
    draw.line([(14, 8), (width - 14, 8)], fill=r_rim, width=1)

    # Hero portrait well on left
    draw.rounded_rectangle([12, 12, 68, height - 12], radius=8, fill=r_dark, outline=r_border, width=2)

    # 4 Resource Slot wells evenly spaced across remainder
    start_x = 80
    slot_w = (width - start_x - 16) // 4 - 6
    for i in range(4):
        sx = start_x + i * (slot_w + 6)
        draw.rounded_rectangle([sx, 12, sx + slot_w, height - 12], radius=6, fill=r_dark, outline=hex_to_rgba("#1C2B3D"), width=2)

    return img


# -------------------------------------------------------------------------
# TOOLTIP CONTAINER FRAME
# -------------------------------------------------------------------------

def render_tooltip_frame(width: int = 280, height: int = 150) -> Image.Image:
    """Render dark slate tooltip frame with metallic beveled corners."""
    img = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    t_bg = hex_to_rgba("#0C131E")
    t_border = hex_to_rgba("#26394F")
    t_gold = hex_to_rgba("#D4AF37")

    # Body
    draw.rounded_rectangle([4, 4, width - 4, height - 4], radius=8, fill=t_bg, outline=t_border, width=3)

    # Ornate gold corner notches
    c_len = 16
    corners = [
        [(8, 8 + c_len), (8, 8), (8 + c_len, 8)],
        [(width - 8 - c_len, 8), (width - 8, 8), (width - 8, 8 + c_len)],
        [(8, height - 8 - c_len), (8, height - 8), (8 + c_len, height - 8)],
        [(width - 8 - c_len, height - 8), (width - 8, height - 8), (width - 8, height - 8 - c_len)],
    ]
    for pts in corners:
        draw.line(pts, fill=t_gold, width=2)

    return img


# -------------------------------------------------------------------------
# GODOT 9-PATCH SLICE METADATA
# -------------------------------------------------------------------------

GODOT_9PATCH_SLICES: Dict[str, Dict[str, int]] = {
    "action_slot_normal.png": {"margin_left": 16, "margin_top": 16, "margin_right": 16, "margin_bottom": 16},
    "action_slot_hover.png": {"margin_left": 16, "margin_top": 16, "margin_right": 16, "margin_bottom": 16},
    "action_slot_pressed.png": {"margin_left": 16, "margin_top": 16, "margin_right": 16, "margin_bottom": 16},
    "action_slot_disabled.png": {"margin_left": 16, "margin_top": 16, "margin_right": 16, "margin_bottom": 16},
    "action_slot_cooldown.png": {"margin_left": 16, "margin_top": 16, "margin_right": 16, "margin_bottom": 16},
    "keycap_frame_normal.png": {"margin_left": 6, "margin_top": 6, "margin_right": 6, "margin_bottom": 6},
    "keycap_frame_pressed.png": {"margin_left": 6, "margin_top": 6, "margin_right": 6, "margin_bottom": 6},
    "health_bar_bg.png": {"margin_left": 8, "margin_top": 6, "margin_right": 8, "margin_bottom": 6},
    "health_bar_fill_full.png": {"margin_left": 4, "margin_top": 4, "margin_right": 4, "margin_bottom": 4},
    "health_bar_fill_danger.png": {"margin_left": 4, "margin_top": 4, "margin_right": 4, "margin_bottom": 4},
    "wave_bar_bg.png": {"margin_left": 8, "margin_top": 6, "margin_right": 8, "margin_bottom": 6},
    "wave_bar_fill.png": {"margin_left": 4, "margin_top": 4, "margin_right": 4, "margin_bottom": 4},
    "xp_bar_bg.png": {"margin_left": 8, "margin_top": 6, "margin_right": 8, "margin_bottom": 6},
    "xp_bar_fill.png": {"margin_left": 4, "margin_top": 4, "margin_right": 4, "margin_bottom": 4},
    "resource_panel_bg.png": {"margin_left": 20, "margin_top": 10, "margin_right": 20, "margin_bottom": 10},
    "tooltip_bg.png": {"margin_left": 18, "margin_top": 18, "margin_right": 18, "margin_bottom": 18},
}

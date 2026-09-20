#!/usr/bin/env python3
"""HUD Icons Builder: Procedural & Vector rendering for Cube Siege UI Kit.

Generates 27 crisp, high-readability icons at 512x512 resolution with
multi-layered shading, specular highlights, glows, and clean silhouettes.
"""

from __future__ import annotations

import math
from typing import Callable, Dict, List, Tuple
from PIL import Image, ImageDraw, ImageFilter


def create_canvas(size: int = 512) -> Image.Image:
    """Create a transparent RGBA canvas."""
    return Image.new("RGBA", (size, size), (0, 0, 0, 0))


def hex_to_rgba(hex_code: str, alpha: int = 255) -> Tuple[int, int, int, int]:
    """Convert hex color string to RGBA tuple."""
    hex_code = hex_code.lstrip("#")
    r = int(hex_code[0:2], 16)
    g = int(hex_code[2:4], 16)
    b = int(hex_code[4:6], 16)
    return (r, g, b, alpha)


def draw_glow(
    img: Image.Image,
    draw_fn: Callable[[ImageDraw.ImageDraw], None],
    color: Tuple[int, int, int, int],
    radius: int = 15,
    intensity: int = 2,
) -> None:
    """Draw a soft bloom/glow under an element."""
    glow_layer = Image.new("RGBA", img.size, (0, 0, 0, 0))
    gdraw = ImageDraw.Draw(glow_layer)
    draw_fn(gdraw)
    blurred = glow_layer.filter(ImageFilter.GaussianBlur(radius))
    for _ in range(intensity):
        img.alpha_composite(blurred)


# -------------------------------------------------------------------------
# RESOURCE ICONS (4)
# -------------------------------------------------------------------------

def render_resource_wood(size: int = 512) -> Image.Image:
    """Wood: Stack of 3 chopped logs with growth rings and bark."""
    img = create_canvas(size)
    scale = size / 512.0
    draw = ImageDraw.Draw(img)

    bark_dark = hex_to_rgba("#4A2508")
    bark_mid = hex_to_rgba("#7A3E10")
    wood_inner = hex_to_rgba("#D29A5B")
    wood_ring = hex_to_rgba("#B87D3F")
    wood_highlight = hex_to_rgba("#F1C588")

    def draw_log(cx: float, cy: float, rx: float, ry: float, length: float, angle_deg: float):
        # Cylindrical body
        dx = length * math.cos(math.radians(angle_deg))
        dy = length * math.sin(math.radians(angle_deg))
        p1 = (cx - rx, cy)
        p2 = (cx + rx, cy)
        p3 = (cx + rx + dx, cy + dy)
        p4 = (cx - rx + dx, cy + dy)
        draw.polygon([p1, p2, p3, p4], fill=bark_mid, outline=bark_dark, width=int(4 * scale))
        # Top bark highlight line
        draw.line([p1, (p1[0] + dx, p1[1] + dy)], fill=bark_dark, width=int(6 * scale))
        # End cap face (cross section with growth rings)
        end_box = [cx - rx, cy - ry, cx + rx, cy + ry]
        draw.ellipse(end_box, fill=wood_inner, outline=bark_dark, width=int(5 * scale))
        # Rings
        draw.ellipse([cx - rx * 0.7, cy - ry * 0.7, cx + rx * 0.7, cy + ry * 0.7], outline=wood_ring, width=int(3 * scale))
        draw.ellipse([cx - rx * 0.4, cy - ry * 0.4, cx + rx * 0.4, cy + ry * 0.4], outline=wood_ring, width=int(3 * scale))
        draw.ellipse([cx - rx * 0.15, cy - ry * 0.15, cx + rx * 0.15, cy + ry * 0.15], fill=bark_dark)
        # Specular glint
        draw.arc([cx - rx * 0.9, cy - ry * 0.9, cx + rx * 0.9, cy + ry * 0.9], start=200, end=340, fill=wood_highlight, width=int(3 * scale))

    # Glow layer
    draw_glow(img, lambda d: d.ellipse([100*scale, 100*scale, 412*scale, 412*scale], fill=(200, 130, 50, 60)), (200, 130, 50, 60), radius=20)
    
    # Bottom Left Log
    draw_log(170 * scale, 310 * scale, 65 * scale, 45 * scale, 140 * scale, -25)
    # Bottom Right Log
    draw_log(290 * scale, 330 * scale, 60 * scale, 42 * scale, 130 * scale, -30)
    # Top Center Log
    draw_log(230 * scale, 210 * scale, 70 * scale, 48 * scale, 150 * scale, -28)

    return img


def render_resource_stone(size: int = 512) -> Image.Image:
    """Stone: Angular chiseled granite boulder cluster."""
    img = create_canvas(size)
    scale = size / 512.0
    draw = ImageDraw.Draw(img)

    s_dark = hex_to_rgba("#334155")
    s_mid = hex_to_rgba("#64748B")
    s_light = hex_to_rgba("#94A3B8")
    s_bright = hex_to_rgba("#CBD5E1")
    s_glow = hex_to_rgba("#38BDF8", 40)

    # Ambient back glow
    draw_glow(img, lambda d: d.ellipse([100*scale, 120*scale, 412*scale, 410*scale], fill=s_glow), s_glow, radius=25)

    # Facets for main rock
    main_facets = [
        # Base/Dark shadow facets
        ([(120, 380), (256, 440), (392, 380), (330, 320), (180, 320)], s_dark),
        # Mid left facet
        ([(120, 380), (180, 320), (210, 210), (110, 260)], hex_to_rgba("#475569")),
        # Center facet
        ([(180, 320), (330, 320), (290, 190), (210, 210)], s_mid),
        # Right shadow facet
        ([(330, 320), (392, 380), (410, 270), (340, 210)], hex_to_rgba("#475569")),
        # Top-left bright facet
        ([(110, 260), (210, 210), (256, 120), (160, 150)], s_light),
        # Top-right facet
        ([(210, 210), (290, 190), (340, 210), (256, 120)], s_bright),
    ]

    for poly, col in main_facets:
        pts = [(x * scale, y * scale) for x, y in poly]
        draw.polygon(pts, fill=col, outline=s_dark, width=int(4 * scale))

    # Specular ridge lines
    ridges = [
        [(256, 120), (210, 210)],
        [(210, 210), (180, 320)],
        [(256, 120), (290, 190)],
        [(290, 190), (330, 320)],
    ]
    for r in ridges:
        pts = [(x * scale, y * scale) for x, y in r]
        draw.line(pts, fill=hex_to_rgba("#F1F5F9"), width=int(5 * scale))

    # Small foreground pebble
    peb_pts = [(80 * scale, 390 * scale), (140 * scale, 360 * scale), (160 * scale, 420 * scale), (100 * scale, 430 * scale)]
    draw.polygon(peb_pts, fill=s_mid, outline=s_dark, width=int(3 * scale))

    return img


def render_resource_iron(size: int = 512) -> Image.Image:
    """Iron: Stack of polished metallic forged ingots with specular shine."""
    img = create_canvas(size)
    scale = size / 512.0
    draw = ImageDraw.Draw(img)

    i_shadow = hex_to_rgba("#1E293B")
    i_mid = hex_to_rgba("#64748B")
    i_light = hex_to_rgba("#94A3B8")
    i_bright = hex_to_rgba("#E2E8F0")
    i_cyan = hex_to_rgba("#38BDF8")

    draw_glow(img, lambda d: d.ellipse([100*scale, 140*scale, 412*scale, 400*scale], fill=hex_to_rgba("#38BDF8", 50)), (56, 189, 248, 50), radius=25)

    def draw_ingot(ox: float, oy: float, w: float, h: float, depth: float):
        # Bottom Ingot
        f_tl = (ox + 40 * scale, oy)
        f_tr = (ox + w - 40 * scale, oy)
        f_br = (ox + w, oy + h)
        f_bl = (ox, oy + h)

        t_tl = (f_tl[0] + depth * 0.7, f_tl[1] - depth * 0.5)
        t_tr = (f_tr[0] + depth * 0.7, f_tr[1] - depth * 0.5)
        r_br = (f_br[0] + depth * 0.7, f_br[1] - depth * 0.5)

        # Top face
        draw.polygon([f_tl, f_tr, t_tr, t_tl], fill=i_bright, outline=i_shadow, width=int(4 * scale))
        # Right face
        draw.polygon([f_tr, f_br, r_br, t_tr], fill=i_mid, outline=i_shadow, width=int(4 * scale))
        # Front face
        draw.polygon([f_tl, f_tr, f_br, f_bl], fill=i_light, outline=i_shadow, width=int(4 * scale))

        # Hallmark stamp in center
        stamp_box = [ox + w*0.35, oy + h*0.25, ox + w*0.65, oy + h*0.75]
        draw.rectangle(stamp_box, outline=i_shadow, width=int(3 * scale), fill=i_mid)

        # Specular sheen line
        draw.line([f_tl, (f_tr[0] - 20*scale, f_tl[1])], fill=hex_to_rgba("#FFFFFF"), width=int(4 * scale))

    # Bottom Ingot
    draw_ingot(110 * scale, 280 * scale, 260 * scale, 90 * scale, 60 * scale)
    # Top Ingot
    draw_ingot(150 * scale, 170 * scale, 240 * scale, 85 * scale, 55 * scale)

    # Sparkling glint at top-right
    glint_c = (370 * scale, 140 * scale)
    draw.line([(glint_c[0]-25*scale, glint_c[1]), (glint_c[0]+25*scale, glint_c[1])], fill=(255, 255, 255, 255), width=int(5*scale))
    draw.line([(glint_c[0], glint_c[1]-25*scale), (glint_c[0], glint_c[1]+25*scale)], fill=(255, 255, 255, 255), width=int(5*scale))

    return img


def render_resource_magic_stone(size: int = 512) -> Image.Image:
    """Magic Stone: Luminous violet and cyan crystal cluster."""
    img = create_canvas(size)
    scale = size / 512.0
    draw = ImageDraw.Draw(img)

    c_glow = hex_to_rgba("#A855F7", 90)
    c_deep = hex_to_rgba("#581C87")
    c_mid = hex_to_rgba("#9333EA")
    c_light = hex_to_rgba("#C084FC")
    c_cyan = hex_to_rgba("#38BDF8")
    c_core = hex_to_rgba("#F472B6")
    c_white = hex_to_rgba("#FFFFFF")

    # Vibrant multi-colored bloom
    draw_glow(img, lambda d: d.ellipse([80*scale, 60*scale, 432*scale, 440*scale], fill=c_glow), c_glow, radius=35, intensity=3)
    draw_glow(img, lambda d: d.ellipse([150*scale, 100*scale, 360*scale, 380*scale], fill=hex_to_rgba("#38BDF8", 80)), c_cyan, radius=20)

    def draw_crystal(tip: Tuple[float, float], base_l: Tuple[float, float], base_r: Tuple[float, float], base_b: Tuple[float, float], mid_c: Tuple[float, float]):
        # Left facet
        draw.polygon([tip, base_l, base_b, mid_c], fill=c_mid, outline=c_deep, width=int(3 * scale))
        # Right facet
        draw.polygon([tip, mid_c, base_b, base_r], fill=c_deep, outline=c_deep, width=int(3 * scale))
        # Highlight front crest
        draw.polygon([tip, mid_c, (base_l[0]*0.5+base_r[0]*0.5, base_b[1])], fill=c_light)
        # Specular crest line
        draw.line([tip, mid_c], fill=c_cyan, width=int(4 * scale))

    # Left Shard
    draw_crystal((150*scale, 210*scale), (100*scale, 360*scale), (190*scale, 370*scale), (145*scale, 400*scale), (150*scale, 330*scale))
    # Right Shard
    draw_crystal((360*scale, 230*scale), (310*scale, 380*scale), (400*scale, 360*scale), (365*scale, 410*scale), (360*scale, 340*scale))
    # Tall Center Spire
    draw_crystal((256*scale, 90*scale), (170*scale, 380*scale), (342*scale, 380*scale), (256*scale, 430*scale), (256*scale, 340*scale))

    # Internal energy core line
    draw.line([(256*scale, 100*scale), (256*scale, 320*scale)], fill=c_white, width=int(5 * scale))

    # Floating magical sparkles
    sparks = [(170, 140), (330, 160), (220, 240), (290, 280), (120, 280), (380, 300)]
    for sx, sy in sparks:
        spt = (sx * scale, sy * scale)
        r = 6 * scale
        draw.ellipse([spt[0]-r, spt[1]-r, spt[0]+r, spt[1]+r], fill=c_white)

    return img


# -------------------------------------------------------------------------
# GLOBAL HUD ICONS (4)
# -------------------------------------------------------------------------

def render_global_day(size: int = 512) -> Image.Image:
    """Day: Radiant golden sun emblem with geometric stylized corona rays."""
    img = create_canvas(size)
    scale = size / 512.0
    draw = ImageDraw.Draw(img)

    g_gold = hex_to_rgba("#F59E0B")
    g_bright = hex_to_rgba("#FBBF24")
    g_light = hex_to_rgba("#FEF08A")
    g_dark = hex_to_rgba("#B45309")

    # Warm sun glow
    draw_glow(img, lambda d: d.ellipse([80*scale, 80*scale, 432*scale, 432*scale], fill=hex_to_rgba("#F59E0B", 100)), g_gold, radius=35, intensity=3)

    cx, cy = 256 * scale, 256 * scale
    num_rays = 12
    for i in range(num_rays):
        angle = i * (360.0 / num_rays)
        rad = math.radians(angle)
        rad_w = math.radians(angle + 90)
        is_cardinal = (i % 3 == 0)
        ray_len = (185 if is_cardinal else 150) * scale
        inner_r = 95 * scale
        tip = (cx + ray_len * math.cos(rad), cy + ray_len * math.sin(rad))
        w = (20 if is_cardinal else 14) * scale
        b1 = (cx + inner_r * math.cos(rad) + w * math.cos(rad_w), cy + inner_r * math.sin(rad) + w * math.sin(rad_w))
        b2 = (cx + inner_r * math.cos(rad) - w * math.cos(rad_w), cy + inner_r * math.sin(rad) - w * math.sin(rad_w))
        draw.polygon([tip, b1, (cx + (inner_r - 10*scale) * math.cos(rad), cy + (inner_r - 10*scale) * math.sin(rad)), b2],
                     fill=g_bright if is_cardinal else g_gold, outline=g_dark, width=int(3 * scale))

    # Central Sun Disc
    r_core = 85 * scale
    draw.ellipse([cx - r_core, cy - r_core, cx + r_core, cy + r_core], fill=g_bright, outline=g_dark, width=int(6 * scale))
    r_inner = 65 * scale
    draw.ellipse([cx - r_inner, cy - r_inner, cx + r_inner, cy + r_inner], fill=g_light)
    draw.ellipse([cx - r_inner*0.4, cy - r_inner*0.7, cx + r_inner*0.4, cy], fill=(255, 255, 255, 180))

    return img


def render_global_night(size: int = 512) -> Image.Image:
    """Night: Celestial cyan crescent moon with star glints."""
    img = create_canvas(size)
    scale = size / 512.0

    n_cyan = hex_to_rgba("#38BDF8")
    n_bright = hex_to_rgba("#BAE6FD")
    n_deep = hex_to_rgba("#0284C7")
    n_glow = hex_to_rgba("#38BDF8", 80)

    draw_glow(img, lambda d: d.ellipse([90*scale, 90*scale, 422*scale, 422*scale], fill=n_glow), n_glow, radius=30, intensity=3)

    # Outer moon disc
    moon_layer = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    mdraw = ImageDraw.Draw(moon_layer)
    cx, cy = 240 * scale, 256 * scale
    r_outer = 145 * scale
    mdraw.ellipse([cx - r_outer, cy - r_outer, cx + r_outer, cy + r_outer], fill=n_cyan)
    # Inner shadow cutout mask
    cx_cut = cx + 55 * scale
    cy_cut = cy - 20 * scale
    r_cut = 135 * scale
    mdraw.ellipse([cx_cut - r_cut, cy_cut - r_cut, cx_cut + r_cut, cy_cut + r_cut], fill=(0, 0, 0, 0))
    img.alpha_composite(moon_layer)

    draw = ImageDraw.Draw(img)
    # Outer rim highlight
    draw.arc([cx - r_outer, cy - r_outer, cx + r_outer, cy + r_outer], start=90, end=270, fill=n_bright, width=int(6 * scale))

    # Star glints
    stars = [(340, 160, 24), (380, 260, 16), (320, 340, 18)]
    for sx, sy, sr in stars:
        scx, scy = sx * scale, sy * scale
        srad = sr * scale
        draw.polygon([(scx, scy - srad), (scx + srad*0.3, scy), (scx, scy + srad), (scx - srad*0.3, scy)], fill=n_bright)
        draw.polygon([(scx - srad, scy), (scx, scy + srad*0.3), (scx + srad, scy), (scx, scy - srad*0.3)], fill=n_bright)

    return img


def render_global_settings(size: int = 512) -> Image.Image:
    """Settings: Precision mechanical cog / gear with beveled teeth and axle."""
    img = create_canvas(size)
    scale = size / 512.0
    draw = ImageDraw.Draw(img)

    s_dark = hex_to_rgba("#1E293B")
    s_mid = hex_to_rgba("#475569")
    s_light = hex_to_rgba("#94A3B8")
    s_bright = hex_to_rgba("#E2E8F0")

    draw_glow(img, lambda d: d.ellipse([100*scale, 100*scale, 412*scale, 412*scale], fill=(71, 85, 105, 70)), (71, 85, 105, 70), radius=20)

    cx, cy = 256 * scale, 256 * scale
    num_teeth = 8
    poly_pts = []
    r_outer = 175 * scale
    r_root = 135 * scale

    for i in range(num_teeth):
        base_deg = i * (360.0 / num_teeth)
        for d_deg, r in [(-12, r_root), (-8, r_outer), (8, r_outer), (12, r_root)]:
            ang = math.radians(base_deg + d_deg)
            poly_pts.append((cx + r * math.cos(ang), cy + r * math.sin(ang)))

    draw.polygon(poly_pts, fill=s_mid, outline=s_dark, width=int(6 * scale))

    # Inner beveled rim
    r_rim = 110 * scale
    draw.ellipse([cx - r_rim, cy - r_rim, cx + r_rim, cy + r_rim], fill=s_light, outline=s_dark, width=int(5 * scale))

    # Axle hole
    r_axle = 55 * scale
    draw.ellipse([cx - r_axle, cy - r_axle, cx + r_axle, cy + r_axle], fill=s_dark, outline=s_mid, width=int(4 * scale))
    r_core = 30 * scale
    draw.ellipse([cx - r_core, cy - r_core, cx + r_core, cy + r_core], fill=s_bright)

    # Rivet bolts
    for i in range(4):
        ang = math.radians(i * 90 + 45)
        rx = cx + 85 * scale * math.cos(ang)
        ry = cy + 85 * scale * math.sin(ang)
        draw.ellipse([rx - 8*scale, ry - 8*scale, rx + 8*scale, ry + 8*scale], fill=s_bright, outline=s_dark, width=int(2*scale))

    return img


def render_global_build(size: int = 512) -> Image.Image:
    """Build: Crossed architect's hammer and ruler / blueprint hammer."""
    img = create_canvas(size)
    scale = size / 512.0
    draw = ImageDraw.Draw(img)

    b_gold = hex_to_rgba("#F59E0B")
    b_dark = hex_to_rgba("#78350F")
    b_steel = hex_to_rgba("#CBD5E1")
    b_shadow = hex_to_rgba("#0F172A")
    b_handle = hex_to_rgba("#92400E")

    draw_glow(img, lambda d: d.ellipse([100*scale, 100*scale, 412*scale, 412*scale], fill=hex_to_rgba("#F59E0B", 60)), b_gold, radius=25)

    # Drafting Square (Ruler angled -45 deg)
    ruler_pts = [
        (130 * scale, 390 * scale),
        (370 * scale, 150 * scale),
        (410 * scale, 190 * scale),
        (170 * scale, 430 * scale),
    ]
    draw.polygon(ruler_pts, fill=b_steel, outline=b_shadow, width=int(4 * scale))
    # Ruler tick marks
    for i in range(7):
        t = i / 6.0
        x1 = 150*scale + t * 220*scale
        y1 = 410*scale - t * 220*scale
        draw.line([(x1, y1), (x1 + 16*scale, y1 + 16*scale)], fill=b_shadow, width=int(3 * scale))

    # Heavy Forged Hammer (angled +45 deg)
    # Handle
    h_start = (140 * scale, 160 * scale)
    h_end = (380 * scale, 400 * scale)
    draw.line([h_start, h_end], fill=b_handle, width=int(26 * scale))
    draw.line([h_start, h_end], fill=b_dark, width=int(6 * scale))

    # Hammer Head
    hx, hy = 180 * scale, 200 * scale
    head_box = [
        (hx - 80*scale, hy - 40*scale),
        (hx + 30*scale, hy - 110*scale),
        (hx + 80*scale, hy - 60*scale),
        (hx - 30*scale, hy + 10*scale),
    ]
    draw.polygon(head_box, fill=b_gold, outline=b_shadow, width=int(5 * scale))
    # Hammer Face highlight
    draw.polygon([(hx - 80*scale, hy - 40*scale), (hx - 40*scale, hy - 80*scale), (hx - 20*scale, hy - 60*scale), (hx - 60*scale, hy - 20*scale)], fill=hex_to_rgba("#FEF08A"))

    return img


# -------------------------------------------------------------------------
# WARRIOR ABILITY ICONS (5)
# -------------------------------------------------------------------------

def render_warrior_sword_attack(size: int = 512) -> Image.Image:
    """Warrior LMB: Gleaming broadsword delivering a swift cutting slash."""
    img = create_canvas(size)
    scale = size / 512.0
    draw = ImageDraw.Draw(img)

    w_red = hex_to_rgba("#EF4444")
    w_orange = hex_to_rgba("#F97316")
    w_blade = hex_to_rgba("#E2E8F0")
    w_gold = hex_to_rgba("#F59E0B")
    w_dark = hex_to_rgba("#1E293B")

    # Slash Trail
    draw_glow(img, lambda d: d.arc([70*scale, 70*scale, 442*scale, 442*scale], start=120, end=330, fill=w_red, width=int(32*scale)), w_red, radius=25, intensity=3)
    draw.arc([80*scale, 80*scale, 432*scale, 432*scale], start=130, end=320, fill=w_orange, width=int(18*scale))
    draw.arc([80*scale, 80*scale, 432*scale, 432*scale], start=150, end=300, fill=hex_to_rgba("#FEF08A"), width=int(8*scale))

    # Diagonal Broadsword (Top-Left to Bottom-Right)
    # Blade
    b_tip = (370 * scale, 120 * scale)
    b_guard = (180 * scale, 310 * scale)
    b_l = (165 * scale, 295 * scale)
    b_r = (195 * scale, 325 * scale)

    draw.polygon([b_tip, b_r, (180*scale, 320*scale), b_l], fill=w_blade, outline=w_dark, width=int(4 * scale))
    # Blade centerline
    draw.line([b_tip, (180*scale, 310*scale)], fill=hex_to_rgba("#38BDF8"), width=int(4 * scale))
    # Specular edge
    draw.line([b_tip, b_l], fill=hex_to_rgba("#FFFFFF"), width=int(5 * scale))

    # Crossguard
    g_l = (130 * scale, 270 * scale)
    g_r = (230 * scale, 370 * scale)
    draw.line([g_l, g_r], fill=w_gold, width=int(16 * scale))

    # Grip & Pommel
    p_end = (120 * scale, 370 * scale)
    draw.line([b_guard, p_end], fill=hex_to_rgba("#78350F"), width=int(12 * scale))
    draw.ellipse([p_end[0]-14*scale, p_end[1]-14*scale, p_end[0]+14*scale, p_end[1]+14*scale], fill=w_gold, outline=w_dark, width=int(3*scale))

    return img


def render_warrior_cleave(size: int = 512) -> Image.Image:
    """Warrior RMB: Blazing fiery whirlwind / circular cleave slash arc."""
    img = create_canvas(size)
    scale = size / 512.0
    draw = ImageDraw.Draw(img)

    f_red = hex_to_rgba("#EA580C")
    f_orange = hex_to_rgba("#F97316")
    f_gold = hex_to_rgba("#FBBF24")
    f_white = hex_to_rgba("#FFFBEB")

    draw_glow(img, lambda d: d.arc([70*scale, 70*scale, 442*scale, 442*scale], start=30, end=330, fill=f_red, width=int(45*scale)), f_red, radius=30, intensity=3)

    cx, cy = 256 * scale, 256 * scale
    # Double crescent fiery vortex
    for r, w, col in [(160*scale, 28*scale, f_orange), (140*scale, 20*scale, f_gold), (120*scale, 10*scale, f_white)]:
        draw.arc([cx - r, cy - r, cx + r, cy + r], start=45, end=300, fill=col, width=int(w))
        draw.arc([cx - r*0.75, cy - r*0.75, cx + r*0.75, cy + r*0.75], start=180, end=420, fill=col, width=int(w*0.7))

    # Flying ember particles
    embers = [(110, 160), (380, 140), (410, 290), (140, 380), (280, 420), (320, 110)]
    for ex, ey in embers:
        ecx, ecy = ex * scale, ey * scale
        er = 7 * scale
        draw.ellipse([ecx - er, ecy - er, ecx + er, ecy + er], fill=f_white)

    return img


def render_warrior_dash(size: int = 512) -> Image.Image:
    """Warrior Space: Charging armored boots with dynamic velocity streaks."""
    img = create_canvas(size)
    scale = size / 512.0
    draw = ImageDraw.Draw(img)

    d_red = hex_to_rgba("#EF4444")
    d_orange = hex_to_rgba("#F97316")
    d_gold = hex_to_rgba("#FBBF24")
    d_armor = hex_to_rgba("#CBD5E1")
    d_dark = hex_to_rgba("#0F172A")

    draw_glow(img, lambda d: d.line([(80*scale, 256*scale), (340*scale, 256*scale)], fill=d_orange, width=int(50*scale)), d_orange, radius=25)

    # Supersonic speed lines behind
    speed_lines = [
        (60, 180, 220, 180, 10),
        (40, 240, 260, 240, 16),
        (50, 300, 240, 300, 14),
        (80, 360, 200, 360, 8),
    ]
    for x1, y1, x2, y2, w in speed_lines:
        draw.line([(x1*scale, y1*scale), (x2*scale, y2*scale)], fill=d_gold, width=int(w * scale))

    # Armored Boot Silhouette rushing Right
    # Greave / Shin
    boot_pts = [
        (220 * scale, 150 * scale),
        (290 * scale, 180 * scale),
        (290 * scale, 280 * scale),
        (390 * scale, 340 * scale),
        (380 * scale, 380 * scale),
        (240 * scale, 380 * scale),
        (200 * scale, 280 * scale),
    ]
    draw.polygon(boot_pts, fill=d_armor, outline=d_dark, width=int(6 * scale))

    # Armor plating segments
    draw.line([(210*scale, 210*scale), (290*scale, 230*scale)], fill=d_gold, width=int(5 * scale))
    draw.line([(200*scale, 280*scale), (300*scale, 300*scale)], fill=d_gold, width=int(5 * scale))

    # Winged ankle fin
    fin_pts = [(160 * scale, 240 * scale), (220 * scale, 230 * scale), (190 * scale, 290 * scale)]
    draw.polygon(fin_pts, fill=d_orange, outline=d_dark, width=int(4 * scale))

    return img


def render_warrior_parry(size: int = 512) -> Image.Image:
    """Warrior Q: Crossed blade and heater shield deflecting with brilliant sparks."""
    img = create_canvas(size)
    scale = size / 512.0
    draw = ImageDraw.Draw(img)

    p_shield = hex_to_rgba("#1E3A8A")
    p_rim = hex_to_rgba("#F59E0B")
    p_blade = hex_to_rgba("#E2E8F0")
    p_cyan = hex_to_rgba("#38BDF8")
    p_white = hex_to_rgba("#FFFFFF")
    p_dark = hex_to_rgba("#0F172A")

    draw_glow(img, lambda d: d.ellipse([140*scale, 140*scale, 372*scale, 372*scale], fill=hex_to_rgba("#38BDF8", 110)), p_cyan, radius=30, intensity=3)

    # Heater Shield
    s_top_l = (150 * scale, 150 * scale)
    s_top_r = (330 * scale, 150 * scale)
    s_mid_l = (130 * scale, 280 * scale)
    s_mid_r = (350 * scale, 280 * scale)
    s_tip = (240 * scale, 420 * scale)
    shield_pts = [s_top_l, s_top_r, s_mid_r, s_tip, s_mid_l]
    draw.polygon(shield_pts, fill=p_shield, outline=p_rim, width=int(10 * scale))
    # Inner emblem on shield
    draw.line([(240*scale, 160*scale), s_tip], fill=p_rim, width=int(6 * scale))

    # Deflecting Blade across front
    b_start = (380 * scale, 130 * scale)
    b_end = (120 * scale, 390 * scale)
    draw.line([b_start, b_end], fill=p_blade, width=int(18 * scale))
    draw.line([b_start, b_end], fill=p_white, width=int(6 * scale))

    # Starburst impact point
    ix, iy = 260 * scale, 250 * scale
    for ang in range(0, 360, 45):
        rad = math.radians(ang)
        r = 65 * scale
        draw.line([(ix, iy), (ix + r * math.cos(rad), iy + r * math.sin(rad))], fill=p_white, width=int(5 * scale))

    return img


def render_warrior_duel(size: int = 512) -> Image.Image:
    """Warrior F: Crossed flaming blades beneath a crowned battle crest."""
    img = create_canvas(size)
    scale = size / 512.0
    draw = ImageDraw.Draw(img)

    d_red = hex_to_rgba("#DC2626")
    d_gold = hex_to_rgba("#FBBF24")
    d_white = hex_to_rgba("#FEF2F2")
    d_dark = hex_to_rgba("#18181B")

    draw_glow(img, lambda d: d.ellipse([90*scale, 90*scale, 422*scale, 422*scale], fill=hex_to_rgba("#DC2626", 90)), d_red, radius=30, intensity=3)

    # Crossed Swords
    # Sword 1: Top-Left to Bottom-Right
    draw.line([(120*scale, 130*scale), (390*scale, 400*scale)], fill=hex_to_rgba("#E2E8F0"), width=int(16 * scale))
    draw.line([(120*scale, 130*scale), (390*scale, 400*scale)], fill=d_white, width=int(5 * scale))
    # Sword 2: Top-Right to Bottom-Left
    draw.line([(390*scale, 130*scale), (120*scale, 400*scale)], fill=hex_to_rgba("#CBD5E1"), width=int(16 * scale))
    draw.line([(390*scale, 130*scale), (120*scale, 400*scale)], fill=d_white, width=int(5 * scale))

    # Crown of Battle at Top Center
    crown_pts = [
        (170 * scale, 170 * scale),
        (190 * scale, 100 * scale),
        (225 * scale, 130 * scale),
        (256 * scale, 80 * scale),
        (287 * scale, 130 * scale),
        (322 * scale, 100 * scale),
        (342 * scale, 170 * scale),
    ]
    draw.polygon(crown_pts, fill=d_gold, outline=d_dark, width=int(5 * scale))

    # Flaming aura arcs
    draw.arc([160*scale, 200*scale, 352*scale, 392*scale], start=20, end=160, fill=d_gold, width=int(12*scale))

    return img


# -------------------------------------------------------------------------
# ARCHER ABILITY ICONS (5)
# -------------------------------------------------------------------------

def render_archer_shot(size: int = 512) -> Image.Image:
    """Archer LMB: Drawn recurve bow unleashing a swift flight arrow."""
    img = create_canvas(size)
    scale = size / 512.0
    draw = ImageDraw.Draw(img)

    a_cyan = hex_to_rgba("#38BDF8")
    a_wood = hex_to_rgba("#92400E")
    a_white = hex_to_rgba("#FFFFFF")
    a_dark = hex_to_rgba("#0C4A6E")

    draw_glow(img, lambda d: d.line([(140*scale, 370*scale), (380*scale, 130*scale)], fill=a_cyan, width=int(30*scale)), a_cyan, radius=25)

    # Recurve Bow Arc
    draw.arc([100*scale, 100*scale, 380*scale, 380*scale], start=100, end=260, fill=a_wood, width=int(16*scale))
    # Bowstring
    draw.line([(140*scale, 140*scale), (210*scale, 290*scale)], fill=hex_to_rgba("#E2E8F0"), width=int(3*scale))
    draw.line([(210*scale, 290*scale), (140*scale, 360*scale)], fill=hex_to_rgba("#E2E8F0"), width=int(3*scale))

    # Loose Flight Arrow (heading to top-right)
    a_tip = (400 * scale, 110 * scale)
    a_tail = (190 * scale, 320 * scale)
    draw.line([a_tail, a_tip], fill=a_white, width=int(8 * scale))

    # Arrowhead
    ah_pts = [a_tip, (a_tip[0]-35*scale, a_tip[1]+10*scale), (a_tip[0]-10*scale, a_tip[1]+35*scale)]
    draw.polygon(ah_pts, fill=a_cyan, outline=a_dark, width=int(3 * scale))

    # Cyan velocity trail
    draw.line([(170*scale, 340*scale), (320*scale, 190*scale)], fill=hex_to_rgba("#38BDF8", 120), width=int(18*scale))

    return img


def render_archer_piercing_shot(size: int = 512) -> Image.Image:
    """Archer RMB: Triple luminous cyan arrows piercing through sonic shockwaves."""
    img = create_canvas(size)
    scale = size / 512.0
    draw = ImageDraw.Draw(img)

    p_cyan = hex_to_rgba("#00E5FF")
    p_blue = hex_to_rgba("#0284C7")
    p_white = hex_to_rgba("#E0F7FA")

    draw_glow(img, lambda d: d.ellipse([100*scale, 80*scale, 430*scale, 430*scale], fill=hex_to_rgba("#00E5FF", 90)), p_cyan, radius=30, intensity=3)

    # Concentric penetrating shockwave rings
    for rx, ry, r in [(280, 230, 90), (330, 180, 60), (370, 140, 40)]:
        cx, cy = rx * scale, ry * scale
        draw.ellipse([cx - r*scale, cy - r*scale, cx + r*scale, cy + r*scale], outline=p_cyan, width=int(5*scale))

    # Triple Luminous Arrows
    offsets = [(-35, 35), (0, 0), (35, -35)]
    for ox, oy in offsets:
        start = ((110 + ox) * scale, (380 + oy) * scale)
        tip = ((380 + ox) * scale, (110 + oy) * scale)
        draw.line([start, tip], fill=p_cyan, width=int(10 * scale))
        draw.line([start, tip], fill=p_white, width=int(4 * scale))
        # Arrowhead
        h_pts = [tip, (tip[0]-25*scale, tip[1]+8*scale), (tip[0]-8*scale, tip[1]+25*scale)]
        draw.polygon(h_pts, fill=p_white, outline=p_blue, width=int(2 * scale))

    return img


def render_archer_roll(size: int = 512) -> Image.Image:
    """Archer Space: Acrobatic evasive roll with swirling wind vortices."""
    img = create_canvas(size)
    scale = size / 512.0
    draw = ImageDraw.Draw(img)

    r_cyan = hex_to_rgba("#38BDF8")
    r_light = hex_to_rgba("#BAE6FD")
    r_white = hex_to_rgba("#FFFFFF")

    draw_glow(img, lambda d: d.ellipse([90*scale, 90*scale, 422*scale, 422*scale], fill=hex_to_rgba("#38BDF8", 80)), r_cyan, radius=25)

    cx, cy = 256 * scale, 256 * scale
    # Aerodynamic spiral wind vortex
    for deg in range(0, 540, 15):
        rad = math.radians(deg)
        dist = (40 + deg * 0.24) * scale
        px = cx + dist * math.cos(rad)
        py = cy + dist * math.sin(rad)
        rad_next = math.radians(deg + 15)
        dist_next = (40 + (deg + 15) * 0.24) * scale
        px_next = cx + dist_next * math.cos(rad_next)
        py_next = cy + dist_next * math.sin(rad_next)
        draw.line([(px, py), (px_next, py_next)], fill=r_cyan if deg < 360 else r_white, width=int((6 + deg*0.02) * scale))

    # Evasive Arrow feather spinning in center
    draw.polygon([(cx - 20*scale, cy - 60*scale), (cx + 20*scale, cy - 30*scale), (cx, cy + 50*scale)], fill=r_light, outline=hex_to_rgba("#0284C7"), width=int(3*scale))

    return img


def render_archer_decoy(size: int = 512) -> Image.Image:
    """Archer Q: Translucent holographic illusion decoy silhouette."""
    img = create_canvas(size)
    scale = size / 512.0
    draw = ImageDraw.Draw(img)

    h_purple = hex_to_rgba("#818CF8")
    h_cyan = hex_to_rgba("#38BDF8")
    h_white = hex_to_rgba("#E0E7FF")

    draw_glow(img, lambda d: d.ellipse([110*scale, 90*scale, 402*scale, 422*scale], fill=hex_to_rgba("#818CF8", 80)), h_purple, radius=25)

    # Phantom Cloaked Archer Head & Hood
    hood_pts = [
        (256 * scale, 100 * scale),
        (320 * scale, 170 * scale),
        (300 * scale, 260 * scale),
        (212 * scale, 260 * scale),
        (192 * scale, 170 * scale),
    ]
    draw.polygon(hood_pts, fill=hex_to_rgba("#4338CA", 160), outline=h_cyan, width=int(4 * scale))

    # Cloak Shoulders
    cloak_pts = [
        (192 * scale, 260 * scale),
        (320 * scale, 260 * scale),
        (380 * scale, 400 * scale),
        (132 * scale, 400 * scale),
    ]
    draw.polygon(cloak_pts, fill=hex_to_rgba("#312E81", 140), outline=h_purple, width=int(4 * scale))

    # Scanlines across hologram
    for y in range(120, 390, 18):
        draw.line([(140*scale, y*scale), (370*scale, y*scale)], fill=hex_to_rgba("#38BDF8", 80), width=int(2*scale))

    # Glowing phantom eyes
    draw.ellipse([230*scale, 180*scale, 245*scale, 190*scale], fill=h_white)
    draw.ellipse([267*scale, 180*scale, 282*scale, 190*scale], fill=h_white)

    return img


def render_archer_sniper(size: int = 512) -> Image.Image:
    """Archer F: Precision high-tech sniper reticle locked onto lethal target."""
    img = create_canvas(size)
    scale = size / 512.0
    draw = ImageDraw.Draw(img)

    s_cyan = hex_to_rgba("#22D3EE")
    s_red = hex_to_rgba("#F43F5E")
    s_white = hex_to_rgba("#FFFFFF")
    s_dark = hex_to_rgba("#083344")

    draw_glow(img, lambda d: d.ellipse([90*scale, 90*scale, 422*scale, 422*scale], fill=hex_to_rgba("#22D3EE", 80)), s_cyan, radius=25)

    cx, cy = 256 * scale, 256 * scale
    # Outer Crosshair Ring with tick marks
    r_ring = 150 * scale
    draw.ellipse([cx - r_ring, cy - r_ring, cx + r_ring, cy + r_ring], outline=s_cyan, width=int(6 * scale))

    # 4 Cardinal Reticle Lines with range ticks
    draw.line([(cx - 180*scale, cy), (cx - 40*scale, cy)], fill=s_cyan, width=int(4 * scale))
    draw.line([(cx + 40*scale, cy), (cx + 180*scale, cy)], fill=s_cyan, width=int(4 * scale))
    draw.line([(cx, cy - 180*scale), (cx, cy - 40*scale)], fill=s_cyan, width=int(4 * scale))
    draw.line([(cx, cy + 40*scale), (cx, cy + 180*scale)], fill=s_cyan, width=int(4 * scale))

    # Inner Target Ring
    r_inner = 70 * scale
    draw.ellipse([cx - r_inner, cy - r_inner, cx + r_inner, cy + r_inner], outline=s_red, width=int(4 * scale))

    # Center Bullseye dot
    draw.ellipse([cx - 12*scale, cy - 12*scale, cx + 12*scale, cy + 12*scale], fill=s_red, outline=s_white, width=int(2*scale))

    # Triangle range corners
    for ang in [45, 135, 225, 315]:
        rad = math.radians(ang)
        tx = cx + 115 * scale * math.cos(rad)
        ty = cy + 115 * scale * math.sin(rad)
        draw.ellipse([tx-6*scale, ty-6*scale, tx+6*scale, ty+6*scale], fill=s_cyan)

    return img


# -------------------------------------------------------------------------
# ENGINEER ABILITY ICONS (5)
# -------------------------------------------------------------------------

def render_engineer_hammer(size: int = 512) -> Image.Image:
    """Engineer LMB: Industrial hydraulic power-hammer striking with electric sparks."""
    img = create_canvas(size)
    scale = size / 512.0
    draw = ImageDraw.Draw(img)

    e_orange = hex_to_rgba("#F59E0B")
    e_steel = hex_to_rgba("#E2E8F0")
    e_dark = hex_to_rgba("#1E293B")
    e_blue = hex_to_rgba("#38BDF8")

    draw_glow(img, lambda d: d.ellipse([100*scale, 100*scale, 412*scale, 412*scale], fill=hex_to_rgba("#38BDF8", 70)), e_blue, radius=25)

    # Steel & Brass Hydraulic Mallet Head
    # Impact face striking down towards bottom-left
    hx, hy = 230 * scale, 240 * scale
    head_poly = [
        (130 * scale, 230 * scale),
        (250 * scale, 110 * scale),
        (330 * scale, 190 * scale),
        (210 * scale, 310 * scale),
    ]
    draw.polygon(head_poly, fill=e_steel, outline=e_dark, width=int(6 * scale))
    # Brass reinforcement band
    band_poly = [
        (180 * scale, 180 * scale),
        (230 * scale, 130 * scale),
        (280 * scale, 180 * scale),
        (230 * scale, 230 * scale),
    ]
    draw.polygon(band_poly, fill=e_orange, outline=e_dark, width=int(4 * scale))

    # Heavy Pneumatic Shaft extending to top-right
    draw.line([(280*scale, 150*scale), (410*scale, 40*scale)], fill=hex_to_rgba("#475569"), width=int(22 * scale))
    draw.line([(280*scale, 150*scale), (410*scale, 40*scale)], fill=e_orange, width=int(6 * scale))

    # Electric impact sparks at anvil contact
    impact_sparks = [(120, 250), (90, 310), (140, 340), (70, 220), (180, 360)]
    for sx, sy in impact_sparks:
        draw.line([(130*scale, 230*scale), (sx*scale, sy*scale)], fill=e_blue, width=int(4*scale))

    return img


def render_engineer_turret(size: int = 512) -> Image.Image:
    """Engineer RMB: Deployable automated sentry turret with twin autocannons."""
    img = create_canvas(size)
    scale = size / 512.0
    draw = ImageDraw.Draw(img)

    t_metal = hex_to_rgba("#64748B")
    t_light = hex_to_rgba("#94A3B8")
    t_dark = hex_to_rgba("#0F172A")
    t_cyan = hex_to_rgba("#0EA5E9")
    t_orange = hex_to_rgba("#F59E0B")

    draw_glow(img, lambda d: d.ellipse([100*scale, 100*scale, 412*scale, 412*scale], fill=hex_to_rgba("#0EA5E9", 70)), t_cyan, radius=25)

    # Tripod Legs
    draw.line([(256*scale, 330*scale), (130*scale, 410*scale)], fill=t_dark, width=int(14 * scale))
    draw.line([(256*scale, 330*scale), (382*scale, 410*scale)], fill=t_dark, width=int(14 * scale))
    draw.line([(256*scale, 330*scale), (256*scale, 430*scale)], fill=t_metal, width=int(12 * scale))

    # Turret Body Base / Swivel Mount
    draw.ellipse([200*scale, 300*scale, 312*scale, 360*scale], fill=t_metal, outline=t_dark, width=int(5*scale))

    # Armored Chassis Dome
    dome_pts = [
        (190 * scale, 310 * scale),
        (220 * scale, 210 * scale),
        (292 * scale, 210 * scale),
        (322 * scale, 310 * scale),
    ]
    draw.polygon(dome_pts, fill=t_light, outline=t_dark, width=int(5 * scale))

    # Twin Autocannon Barrels (aimed left/up)
    # Barrel 1
    draw.line([(230*scale, 230*scale), (120*scale, 160*scale)], fill=t_dark, width=int(16 * scale))
    draw.line([(120*scale, 160*scale), (105*scale, 150*scale)], fill=t_orange, width=int(14 * scale))
    # Barrel 2
    draw.line([(270*scale, 250*scale), (160*scale, 180*scale)], fill=t_dark, width=int(16 * scale))
    draw.line([(160*scale, 180*scale), (145*scale, 170*scale)], fill=t_orange, width=int(14 * scale))

    # Glowing Optical Sensor Eye
    draw.ellipse([240*scale, 230*scale, 272*scale, 262*scale], fill=t_cyan, outline=hex_to_rgba("#FFFFFF"), width=int(2*scale))

    return img


def render_engineer_dash(size: int = 512) -> Image.Image:
    """Engineer Space: Rocket thruster booster burst with fire exhaust cones."""
    img = create_canvas(size)
    scale = size / 512.0
    draw = ImageDraw.Draw(img)

    r_steel = hex_to_rgba("#475569")
    r_dark = hex_to_rgba("#0F172A")
    r_flame = hex_to_rgba("#F97316")
    r_yellow = hex_to_rgba("#FBBF24")
    r_core = hex_to_rgba("#FEF08A")

    draw_glow(img, lambda d: d.polygon([(110*scale, 400*scale), (256*scale, 250*scale), (402*scale, 400*scale)], fill=hex_to_rgba("#F97316", 100)), r_flame, radius=30, intensity=3)

    # Twin Jet Thruster Nozzles
    for nx in [190, 322]:
        cx = nx * scale
        # Nozzle cone
        nozzle_pts = [
            (cx - 35*scale, 200*scale),
            (cx + 35*scale, 200*scale),
            (cx + 45*scale, 260*scale),
            (cx - 45*scale, 260*scale),
        ]
        draw.polygon(nozzle_pts, fill=r_steel, outline=r_dark, width=int(4 * scale))
        # Rocket Exhaust Flame Plume
        flame_pts = [
            (cx - 38*scale, 260*scale),
            (cx, 420*scale),
            (cx + 38*scale, 260*scale),
        ]
        draw.polygon(flame_pts, fill=r_flame)
        # Inner Yellow Flame Core
        draw.polygon([(cx - 20*scale, 260*scale), (cx, 370*scale), (cx + 20*scale, 260*scale)], fill=r_yellow)
        draw.polygon([(cx - 10*scale, 260*scale), (cx, 320*scale), (cx + 10*scale, 260*scale)], fill=r_core)

    # Backpack frame connector
    draw.rectangle([170*scale, 150*scale, 342*scale, 200*scale], fill=hex_to_rgba("#94A3B8"), outline=r_dark, width=int(4*scale))

    return img


def render_engineer_mine(size: int = 512) -> Image.Image:
    """Engineer Q: Spiked hex landmine with hazard chevrons and warning LED."""
    img = create_canvas(size)
    scale = size / 512.0
    draw = ImageDraw.Draw(img)

    m_body = hex_to_rgba("#334155")
    m_dark = hex_to_rgba("#0F172A")
    m_yellow = hex_to_rgba("#FBBF24")
    m_red = hex_to_rgba("#EF4444")
    m_white = hex_to_rgba("#FFFFFF")

    draw_glow(img, lambda d: d.ellipse([180*scale, 180*scale, 332*scale, 332*scale], fill=hex_to_rgba("#EF4444", 100)), m_red, radius=25, intensity=3)

    cx, cy = 256 * scale, 256 * scale
    # Spiked Ground Anchor Prongs (6 points)
    for i in range(6):
        ang = math.radians(i * 60 + 30)
        px = cx + 180 * scale * math.cos(ang)
        py = cy + 180 * scale * math.sin(ang)
        draw.line([(cx, cy), (px, py)], fill=m_dark, width=int(22 * scale))

    # Hexagonal Mine Body
    hex_pts = []
    r_hex = 140 * scale
    for i in range(6):
        ang = math.radians(i * 60)
        hex_pts.append((cx + r_hex * math.cos(ang), cy + r_hex * math.sin(ang)))
    draw.polygon(hex_pts, fill=m_body, outline=m_dark, width=int(6 * scale))

    # Hazard Chevron Ring
    draw.ellipse([cx - 95*scale, cy - 95*scale, cx + 95*scale, cy + 95*scale], fill=m_dark, outline=m_yellow, width=int(8*scale))

    # Pulsing Red Trigger Sensor Dome
    r_core = 55 * scale
    draw.ellipse([cx - r_core, cy - r_core, cx + r_core, cy + r_core], fill=m_red, outline=m_white, width=int(3*scale))
    draw.ellipse([cx - r_core*0.4, cy - r_core*0.6, cx + r_core*0.2, cy - r_core*0.1], fill=m_white)

    return img


def render_engineer_overclock(size: int = 512) -> Image.Image:
    """Engineer F: Surging overcharged clockwork gear with lightning arcs."""
    img = create_canvas(size)
    scale = size / 512.0
    draw = ImageDraw.Draw(img)

    o_gold = hex_to_rgba("#F59E0B")
    o_blue = hex_to_rgba("#38BDF8")
    o_dark = hex_to_rgba("#1E293B")
    o_white = hex_to_rgba("#FFFFFF")

    draw_glow(img, lambda d: d.ellipse([80*scale, 80*scale, 432*scale, 432*scale], fill=hex_to_rgba("#38BDF8", 100)), o_blue, radius=30, intensity=3)

    cx, cy = 256 * scale, 256 * scale
    # Overclocked Clockwork Gear
    num_teeth = 10
    poly_pts = []
    r_outer = 160 * scale
    r_root = 125 * scale
    for i in range(num_teeth):
        base_deg = i * (360.0 / num_teeth)
        for d_deg, r in [(-10, r_root), (-6, r_outer), (6, r_outer), (10, r_root)]:
            ang = math.radians(base_deg + d_deg)
            poly_pts.append((cx + r * math.cos(ang), cy + r * math.sin(ang)))
    draw.polygon(poly_pts, fill=o_gold, outline=o_dark, width=int(6 * scale))

    # Inner Core
    draw.ellipse([cx - 85*scale, cy - 85*scale, cx + 85*scale, cy + 85*scale], fill=o_dark, outline=o_gold, width=int(6*scale))

    # Electric Lightning Bolts bursting across
    lightning_bolts = [
        [(100, 120), (180, 200), (220, 180), (260, 260), (380, 360)],
        [(400, 130), (320, 210), (280, 240), (240, 320), (130, 390)],
    ]
    for bolt in lightning_bolts:
        b_pts = [(x * scale, y * scale) for x, y in bolt]
        draw.line(b_pts, fill=o_blue, width=int(12 * scale))
        draw.line(b_pts, fill=o_white, width=int(4 * scale))

    # Center Overheat Indicator
    draw.ellipse([cx - 30*scale, cy - 30*scale, cx + 30*scale, cy + 30*scale], fill=hex_to_rgba("#EF4444"), outline=o_white, width=int(3*scale))

    return img


# -------------------------------------------------------------------------
# AUXILIARY & HUD ELEMENTS (4)
# -------------------------------------------------------------------------

def render_hud_skull_wave(size: int = 512) -> Image.Image:
    """Wave/Boss Skull: Fearsome horned demonic skull with glowing crimson eyes."""
    img = create_canvas(size)
    scale = size / 512.0
    draw = ImageDraw.Draw(img)

    s_red = hex_to_rgba("#EF4444")
    s_dark = hex_to_rgba("#450A0A")
    s_bone = hex_to_rgba("#FEE2E2")
    s_deep = hex_to_rgba("#1C1917")

    draw_glow(img, lambda d: d.ellipse([100*scale, 100*scale, 412*scale, 412*scale], fill=hex_to_rgba("#EF4444", 90)), s_red, radius=30, intensity=3)

    # Skull Cranium
    cranium_pts = [
        (160 * scale, 240 * scale),
        (170 * scale, 150 * scale),
        (256 * scale, 110 * scale),
        (342 * scale, 150 * scale),
        (352 * scale, 240 * scale),
        (312 * scale, 310 * scale),
        (200 * scale, 310 * scale),
    ]
    draw.polygon(cranium_pts, fill=s_bone, outline=s_deep, width=int(6 * scale))

    # Upper Jaw & Teeth
    jaw_pts = [
        (205 * scale, 310 * scale),
        (307 * scale, 310 * scale),
        (292 * scale, 380 * scale),
        (220 * scale, 380 * scale),
    ]
    draw.polygon(jaw_pts, fill=s_bone, outline=s_deep, width=int(6 * scale))

    # Teeth slits
    for tx in [238, 256, 274]:
        draw.line([(tx*scale, 330*scale), (tx*scale, 380*scale)], fill=s_deep, width=int(5*scale))

    # Glowing Red Eye Sockets
    draw.polygon([(195*scale, 220*scale), (235*scale, 240*scale), (205*scale, 265*scale)], fill=s_red, outline=s_deep, width=int(3*scale))
    draw.polygon([(317*scale, 220*scale), (277*scale, 240*scale), (307*scale, 265*scale)], fill=s_red, outline=s_deep, width=int(3*scale))

    # Nasal cavity
    draw.polygon([(256*scale, 270*scale), (248*scale, 295*scale), (264*scale, 295*scale)], fill=s_deep)

    return img


def render_hud_health_cross(size: int = 512) -> Image.Image:
    """Health Cross: Luminous emerald vitality cross with soft healing flare."""
    img = create_canvas(size)
    scale = size / 512.0
    draw = ImageDraw.Draw(img)

    h_green = hex_to_rgba("#10B981")
    h_bright = hex_to_rgba("#34D399")
    h_white = hex_to_rgba("#ECFDF5")
    h_dark = hex_to_rgba("#064E3B")

    draw_glow(img, lambda d: d.ellipse([80*scale, 80*scale, 432*scale, 432*scale], fill=hex_to_rgba("#10B981", 90)), h_green, radius=30, intensity=3)

    cx, cy = 256 * scale, 256 * scale
    w = 55 * scale
    l = 150 * scale

    # Cross polygon
    cross_pts = [
        (cx - w, cy - l),
        (cx + w, cy - l),
        (cx + w, cy - w),
        (cx + l, cy - w),
        (cx + l, cy + w),
        (cx + w, cy + w),
        (cx + w, cy + l),
        (cx - w, cy + l),
        (cx - w, cy + w),
        (cx - l, cy + w),
        (cx - l, cy - w),
        (cx - w, cy - w),
    ]
    draw.polygon(cross_pts, fill=h_green, outline=h_dark, width=int(8 * scale))

    # Beveled Inner Cross
    w_in = 35 * scale
    l_in = 130 * scale
    cross_in = [
        (cx - w_in, cy - l_in),
        (cx + w_in, cy - l_in),
        (cx + w_in, cy - w_in),
        (cx + l_in, cy - w_in),
        (cx + l_in, cy + w_in),
        (cx + w_in, cy + w_in),
        (cx + w_in, cy + l_in),
        (cx - w_in, cy + l_in),
        (cx - w_in, cy + w_in),
        (cx - l_in, cy + w_in),
        (cx - l_in, cy - w_in),
        (cx - w_in, cy - w_in),
    ]
    draw.polygon(cross_in, fill=h_bright)
    draw.line([(cx, cy - l_in*0.8), (cx, cy + l_in*0.8)], fill=h_white, width=int(6*scale))
    draw.line([(cx - l_in*0.8, cy), (cx + l_in*0.8, cy)], fill=h_white, width=int(6*scale))

    return img


def render_hud_armor_shield(size: int = 512) -> Image.Image:
    """Armor Shield: Fortified steel kite shield with damage-reduction crest."""
    img = create_canvas(size)
    scale = size / 512.0
    draw = ImageDraw.Draw(img)

    s_blue = hex_to_rgba("#3B82F6")
    s_light = hex_to_rgba("#93C5FD")
    s_steel = hex_to_rgba("#E2E8F0")
    s_dark = hex_to_rgba("#0F172A")

    draw_glow(img, lambda d: d.ellipse([100*scale, 90*scale, 412*scale, 422*scale], fill=hex_to_rgba("#3B82F6", 70)), s_blue, radius=25)

    # Kite Shield Base
    shield_pts = [
        (150 * scale, 120 * scale),
        (362 * scale, 120 * scale),
        (372 * scale, 260 * scale),
        (256 * scale, 420 * scale),
        (140 * scale, 260 * scale),
    ]
    draw.polygon(shield_pts, fill=s_blue, outline=s_steel, width=int(12 * scale))

    # Inner chevron division
    draw.polygon([(256*scale, 130*scale), (355*scale, 255*scale), (256*scale, 400*scale)], fill=hex_to_rgba("#1D4ED8"))

    # Steel rim studs / rivets
    rivets = [(165, 140), (256, 135), (347, 140), (360, 250), (256, 405), (152, 250)]
    for rx, ry in rivets:
        draw.ellipse([(rx-6)*scale, (ry-6)*scale, (rx+6)*scale, (ry+6)*scale], fill=s_steel, outline=s_dark, width=int(2*scale))

    return img


def render_hud_target_range(size: int = 512) -> Image.Image:
    """Target Range: Concentric target rings with marksman range indicators."""
    img = create_canvas(size)
    scale = size / 512.0
    draw = ImageDraw.Draw(img)

    t_amber = hex_to_rgba("#F59E0B")
    t_bright = hex_to_rgba("#FDE68A")
    t_dark = hex_to_rgba("#78350F")

    draw_glow(img, lambda d: d.ellipse([90*scale, 90*scale, 422*scale, 422*scale], fill=hex_to_rgba("#F59E0B", 70)), t_amber, radius=25)

    cx, cy = 256 * scale, 256 * scale
    for r in [160, 110, 60]:
        r_sc = r * scale
        draw.ellipse([cx - r_sc, cy - r_sc, cx + r_sc, cy + r_sc], outline=t_amber, width=int(6 * scale))

    # Center Bullseye
    draw.ellipse([cx - 20*scale, cy - 20*scale, cx + 20*scale, cy + 20*scale], fill=t_amber, outline=t_bright, width=int(3*scale))

    # 4 Quadrant Ticks
    for ang in range(0, 360, 90):
        rad = math.radians(ang)
        x1 = cx + 80 * scale * math.cos(rad)
        y1 = cy + 80 * scale * math.sin(rad)
        x2 = cx + 180 * scale * math.cos(rad)
        y2 = cy + 180 * scale * math.sin(rad)
        draw.line([(x1, y1), (x2, y2)], fill=t_bright, width=int(5 * scale))

    return img


# -------------------------------------------------------------------------
# REGISTRY OF ALL 27 ICONS
# -------------------------------------------------------------------------

ICON_BUILDERS: Dict[str, Dict[str, any]] = {
    # Resources (4)
    "resource_wood": {
        "fn": render_resource_wood,
        "name": "Wood",
        "category": "resource",
        "action": "Resource: Chopped Wood Logs",
    },
    "resource_stone": {
        "fn": render_resource_stone,
        "name": "Stone",
        "category": "resource",
        "action": "Resource: Granite Stone Blocks",
    },
    "resource_iron": {
        "fn": render_resource_iron,
        "name": "Iron",
        "category": "resource",
        "action": "Resource: Forged Iron Ingot",
    },
    "resource_magic_stone": {
        "fn": render_resource_magic_stone,
        "name": "Magic Stone",
        "category": "resource",
        "action": "Resource: Glowing Mana Crystal",
    },

    # Global HUD (4)
    "global_day": {
        "fn": render_global_day,
        "name": "Day Indicator",
        "category": "global",
        "action": "HUD: Daytime Phase Indicator",
    },
    "global_night": {
        "fn": render_global_night,
        "name": "Night Indicator",
        "category": "global",
        "action": "HUD: Night Phase Indicator",
    },
    "global_settings": {
        "fn": render_global_settings,
        "name": "Settings",
        "category": "global",
        "action": "HUD: Settings / Pause Menu",
    },
    "global_build": {
        "fn": render_global_build,
        "name": "Build Mode",
        "category": "global",
        "action": "HUD: Build Mode (TAB Slot)",
    },

    # Warrior (5)
    "warrior_sword_attack": {
        "fn": render_warrior_sword_attack,
        "name": "Sword Attack",
        "category": "warrior",
        "action": "Warrior LMB: Basic Sword Slash",
    },
    "warrior_cleave": {
        "fn": render_warrior_cleave,
        "name": "Whirlwind Cleave",
        "category": "warrior",
        "action": "Warrior RMB: Sweeping Cleave",
    },
    "warrior_dash": {
        "fn": render_warrior_dash,
        "name": "Battle Dash",
        "category": "warrior",
        "action": "Warrior Space: Combat Dash",
    },
    "warrior_parry": {
        "fn": render_warrior_parry,
        "name": "Deflection Parry",
        "category": "warrior",
        "action": "Warrior Q: Shield Parry",
    },
    "warrior_duel": {
        "fn": render_warrior_duel,
        "name": "Duel of Honor",
        "category": "warrior",
        "action": "Warrior F: Ultimate Duel Challenge",
    },

    # Archer (5)
    "archer_shot": {
        "fn": render_archer_shot,
        "name": "Bow Shot",
        "category": "archer",
        "action": "Archer LMB: Standard Loose Arrow",
    },
    "archer_piercing_shot": {
        "fn": render_archer_piercing_shot,
        "name": "Piercing Drill",
        "category": "archer",
        "action": "Archer RMB: Tri-Arrow Piercing Shot",
    },
    "archer_roll": {
        "fn": render_archer_roll,
        "name": "Tumble Roll",
        "category": "archer",
        "action": "Archer Space: Evasive Roll",
    },
    "archer_decoy": {
        "fn": render_archer_decoy,
        "name": "Holo Decoy",
        "category": "archer",
        "action": "Archer Q: Illusion Clone",
    },
    "archer_sniper": {
        "fn": render_archer_sniper,
        "name": "Precision Sniper",
        "category": "archer",
        "action": "Archer F: Lethal Sniper Stance",
    },

    # Engineer (5)
    "engineer_hammer": {
        "fn": render_engineer_hammer,
        "name": "Power Hammer",
        "category": "engineer",
        "action": "Engineer LMB: Power Hammer Strike",
    },
    "engineer_turret": {
        "fn": render_engineer_turret,
        "name": "Deploy Turret",
        "category": "engineer",
        "action": "Engineer RMB: Sentry Turret",
    },
    "engineer_dash": {
        "fn": render_engineer_dash,
        "name": "Rocket Thruster",
        "category": "engineer",
        "action": "Engineer Space: Rocket Thruster Jump",
    },
    "engineer_mine": {
        "fn": render_engineer_mine,
        "name": "Proximity Mine",
        "category": "engineer",
        "action": "Engineer Q: Spiked Landmine",
    },
    "engineer_overclock": {
        "fn": render_engineer_overclock,
        "name": "Overclock Surge",
        "category": "engineer",
        "action": "Engineer F: Clockwork Overclock",
    },

    # Auxiliary & HUD elements (4)
    "hud_skull_wave": {
        "fn": render_hud_skull_wave,
        "name": "Wave Skull",
        "category": "auxiliary",
        "action": "HUD: Wave Threat Indicator",
    },
    "hud_health_cross": {
        "fn": render_hud_health_cross,
        "name": "Vitality Cross",
        "category": "auxiliary",
        "action": "HUD: Vitality / Healing",
    },
    "hud_armor_shield": {
        "fn": render_hud_armor_shield,
        "name": "Defense Shield",
        "category": "auxiliary",
        "action": "HUD: Armor / Defense",
    },
    "hud_target_range": {
        "fn": render_hud_target_range,
        "name": "Target Range",
        "category": "auxiliary",
        "action": "HUD: Range Reticle",
    },
}

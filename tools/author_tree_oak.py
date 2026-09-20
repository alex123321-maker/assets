#!/usr/bin/env python3
"""
tools/author_tree_oak.py

Generates the canonical voxel source, manifests, and requests for the
production tree oak family (5 variants, slots 0..4) for Cube Siege:
  0: tree_oak_var_0_standard (Standard Oak)
  1: tree_oak_var_1_tall     (Tall Oak)
  2: tree_oak_var_2_broad    (Broad Oak)
  3: tree_oak_var_3_young    (Young Small Oak)
  4: tree_oak_var_4_shrub    (Shrub / Bush Oak)

Pipeline: voxel_static, 0.15m voxel size, shared 3-material palette (W, D, L).
"""

from __future__ import annotations

import json
import math
from pathlib import Path
from pipeline_reports import initialize_text, write_build_report

REPO_ROOT = Path(__file__).resolve().parent.parent
FAMILY_DIR = REPO_ROOT / "assets" / "environment" / "tree_oak"

VOXEL_SIZE = 0.15

# Rich stylized oak palette calibrated for strong contrast against grass terrain
# Hex values converted to canonical IEC 61966-2-1 linear base_color for glTF PBR
SHARED_MATERIALS = {
    "W": {
        "name": "wood_bark",
        "base_color": [0.0667, 0.0278, 0.0105, 1.0],  # Warm dark timber bark (#4a2f1b)
        "roughness": 0.92,
        "metallic": 0.0,
    },
    "D": {
        "name": "foliage_base",
        "base_color": [0.0435, 0.1444, 0.0157, 1.0],  # Rich forest green (#3b6b22)
        "roughness": 0.88,
        "metallic": 0.0,
    },
    "L": {
        "name": "foliage_accent",
        "base_color": [0.1118, 0.2917, 0.0238, 1.0],  # Sunlit golden-green highlight (#5e932b)
        "roughness": 0.82,
        "metallic": 0.0,
    },
}


class VoxelGrid:
    def __init__(self, width: int, height: int, depth: int):
        self.width = width
        self.height = height
        self.depth = depth
        # grid[y][z][x]
        self.grid = [
            [["." for _ in range(width)] for _ in range(depth)]
            for _ in range(height)
        ]

    def in_bounds(self, x: int, y: int, z: int) -> bool:
        return 0 <= x < self.width and 0 <= y < self.height and 0 <= z < self.depth

    def set(self, x: int, y: int, z: int, token: str) -> None:
        if self.in_bounds(x, y, z):
            self.grid[y][z][x] = token

    def get(self, x: int, y: int, z: int) -> str:
        if self.in_bounds(x, y, z):
            return self.grid[y][z][x]
        return "."

    def fill_cylinder(
        self,
        cx: float,
        cz: float,
        y0: int,
        y1: int,
        r0: float,
        r1: float,
        token: str,
        cx1: float | None = None,
        cz1: float | None = None,
    ) -> None:
        if cx1 is None:
            cx1 = cx
        if cz1 is None:
            cz1 = cz
        dy = max(1, y1 - y0)
        for y in range(y0, y1 + 1):
            t = (y - y0) / dy
            cur_cx = cx + (cx1 - cx) * t
            cur_cz = cz + (cz1 - cz) * t
            cur_r = r0 + (r1 - r0) * t
            r_sq = cur_r * cur_r
            min_x = int(math.floor(cur_cx - cur_r))
            max_x = int(math.ceil(cur_cx + cur_r))
            min_z = int(math.floor(cur_cz - cur_r))
            max_z = int(math.ceil(cur_cz + cur_r))
            for z in range(min_z, max_z + 1):
                for x in range(min_x, max_x + 1):
                    dx = x - cur_cx
                    dz = z - cur_cz
                    if dx * dx + dz * dz <= r_sq + 0.15:
                        self.set(x, y, z, token)

    def draw_line_wood(
        self,
        x0: float,
        y0: float,
        z0: float,
        x1: float,
        y1: float,
        z1: float,
        radius: float = 0.8,
    ) -> None:
        dist = math.sqrt((x1 - x0) ** 2 + (y1 - y0) ** 2 + (z1 - z0) ** 2)
        steps = max(1, int(dist * 3.5))
        for s in range(steps + 1):
            t = s / steps
            px = x0 + (x1 - x0) * t
            py = y0 + (y1 - y0) * t
            pz = z0 + (z1 - z0) * t
            r = radius
            min_x = int(math.floor(px - r))
            max_x = int(math.ceil(px + r))
            min_y = int(math.floor(py - r))
            max_y = int(math.ceil(py + r))
            min_z = int(math.floor(pz - r))
            max_z = int(math.ceil(pz + r))
            for y in range(min_y, max_y + 1):
                for z in range(min_z, max_z + 1):
                    for x in range(min_x, max_x + 1):
                        dx = x - px
                        dy = y - py
                        dz = z - pz
                        if dx * dx + dy * dy + dz * dz <= r * r + 0.15:
                            self.set(x, y, z, "W")

    def fill_foliage_cluster(
        self,
        cx: float,
        cy: float,
        cz: float,
        rx: float,
        ry: float,
        rz: float,
        accent_top_ratio: float = 0.50,
        flat_bottom: bool = True,
    ) -> None:
        """Fills a stylized organic cubic cluster with base foliage and sunlit highlights."""
        min_x = int(math.floor(cx - rx))
        max_x = int(math.ceil(cx + rx))
        min_y = int(math.floor(cy - ry))
        max_y = int(math.ceil(cy + ry))
        min_z = int(math.floor(cz - rz))
        max_z = int(math.ceil(cz + rz))

        for y in range(min_y, max_y + 1):
            norm_y = (y - cy) / ry if ry > 0 else 0.0
            if abs(norm_y) > 1.0:
                continue
            # Flatten lower shelf slightly if requested (like real oak cloud pads)
            if flat_bottom and norm_y < -0.85:
                continue

            for z in range(min_z, max_z + 1):
                norm_z = (z - cz) / rz if rz > 0 else 0.0
                if abs(norm_z) > 1.0:
                    continue
                for x in range(min_x, max_x + 1):
                    norm_x = (x - cx) / rx if rx > 0 else 0.0
                    if abs(norm_x) > 1.0:
                        continue

                    # Superellipsoid distance for slightly blocky cubic puff feel
                    dist_sq = norm_x * norm_x + norm_y * norm_y + norm_z * norm_z
                    if dist_sq <= 1.05:
                        # Never overwrite trunk/branch wood
                        if self.get(x, y, z) == "W":
                            continue

                        # Accent token for sunlit top terraces and sun-facing edges (+X and -Z in Blender)
                        is_top_terrace = norm_y >= accent_top_ratio
                        is_sunlit_shoulder = (norm_y >= 0.15) and (dist_sq >= 0.70) and (norm_x > 0.25 or norm_z < -0.25)
                        if is_top_terrace or is_sunlit_shoulder:
                            self.set(x, y, z, "L")
                        else:
                            self.set(x, y, z, "D")

    def fill_blocky_pad(
        self,
        pcx: float,
        pcy: float,
        pcz: float,
        prx: float,
        pry: float,
        prz: float,
        p: float = 2.8,
        accent_top_ratio: float = 0.40,
        flat_bottom: bool = True,
    ) -> None:
        """Fills a superquadric blocky organic cloud pad with crisp stepped terraces."""
        min_x = int(math.floor(pcx - prx))
        max_x = int(math.ceil(pcx + prx))
        min_y = int(math.floor(pcy - pry))
        max_y = int(math.ceil(pcy + pry))
        min_z = int(math.floor(pcz - prz))
        max_z = int(math.ceil(pcz + prz))

        for y in range(min_y, max_y + 1):
            norm_y = (y - pcy) / pry if pry > 0 else 0.0
            if abs(norm_y) > 1.0:
                continue
            if flat_bottom and norm_y < -0.82:
                continue
            for z in range(min_z, max_z + 1):
                norm_z = (z - pcz) / prz if prz > 0 else 0.0
                if abs(norm_z) > 1.0:
                    continue
                for x in range(min_x, max_x + 1):
                    norm_x = (x - pcx) / prx if prx > 0 else 0.0
                    if abs(norm_x) > 1.0:
                        continue

                    val = (abs(norm_x) ** p) + (abs(norm_y) ** p) + (abs(norm_z) ** p)
                    if val <= 1.05:
                        if self.get(x, y, z) == "W":
                            continue
                        is_top = norm_y >= accent_top_ratio
                        is_sun_shoulder = (norm_y >= 0.1) and (norm_x > 0.25 or norm_z < -0.25) and (val >= 0.65)
                        if is_top or is_sun_shoulder:
                            self.set(x, y, z, "L")
                        else:
                            self.set(x, y, z, "D")

    def carve_box(self, x0: int, x1: int, y0: int, y1: int, z0: int, z1: int) -> None:
        for y in range(y0, y1 + 1):
            for z in range(z0, z1 + 1):
                for x in range(x0, x1 + 1):
                    if self.get(x, y, z) != "W":
                        self.set(x, y, z, ".")

    def remove_floating_voxels(self) -> int:
        visited = [
            [[False for _ in range(self.width)] for _ in range(self.depth)]
            for _ in range(self.height)
        ]
        queue: list[tuple[int, int, int]] = []

        # Ground seeds at y=0
        for z in range(self.depth):
            for x in range(self.width):
                if self.grid[0][z][x] != ".":
                    visited[0][z][x] = True
                    queue.append((x, 0, z))

        while queue:
            cx, cy, cz = queue.pop()
            for dx, dy, dz in (
                (1, 0, 0),
                (-1, 0, 0),
                (0, 1, 0),
                (0, -1, 0),
                (0, 0, 1),
                (0, 0, -1),
            ):
                nx, ny, nz = cx + dx, cy + dy, cz + dz
                if self.in_bounds(nx, ny, nz) and not visited[ny][nz][nx]:
                    if self.grid[ny][nz][nx] != ".":
                        visited[ny][nz][nx] = True
                        queue.append((nx, ny, nz))

        removed = 0
        for y in range(self.height):
            for z in range(self.depth):
                for x in range(self.width):
                    if self.grid[y][z][x] != "." and not visited[y][z][x]:
                        self.grid[y][z][x] = "."
                        removed += 1
        return removed

    def to_json_layers(self) -> list[dict]:
        layers = []
        for y in range(self.height):
            rows = ["".join(self.grid[y][z]) for z in range(self.depth)]
            if any(any(c != "." for c in r) for r in rows):
                layers.append({"y": y, "rows": rows})
        return layers


# -------------------------------------------------------------------------
# VARIANT IMPLEMENTATIONS
# -------------------------------------------------------------------------


def build_standard_oak() -> VoxelGrid:
    """
    Standard Oak (Slot 0):
    Balanced adult oak matching tree_concept_reference.png:
    - Root collar with 4 strong spreading buttress roots at ground (z=0)
    - Sturdy vertical trunk splitting at y=7..8 into visible major supporting boughs
    - Visible supporting wooden branches under canopy in ISO, FRONT, SIDE
    - 5 broad, distinctly articulated cloud masses (4 cardinal pods + elevated summit dome)
    - Unmistakable multi-mass silhouette with deep corner cuts and terrace step notches
    - Sunlit accent highlights on top terraces of each lobe
    Height: 27 layers (4.05m, ~4.2m archetype).
    Width: 18x18 grid (2.70m x 2.70m).
    """
    w, h, d = 18, 27, 18
    g = VoxelGrid(w, h, d)
    cx, cz = 8.5, 8.5

    # 1. Sturdy Buttress Root Flare (y=0..3)
    g.fill_cylinder(cx, cz, 0, 1, r0=2.9, r1=2.2, token="W")
    g.fill_cylinder(cx, cz, 1, 3, r0=2.2, r1=1.7, token="W")

    # Cardinal roots spreading into ground
    g.draw_line_wood(cx - 3.5, 0, cz, cx - 0.7, 2.2, cz, radius=1.1)
    g.draw_line_wood(cx + 3.5, 0, cz, cx + 0.7, 2.2, cz, radius=1.1)
    g.draw_line_wood(cx, 0, cz + 3.5, cx, 2.2, cz + 0.7, radius=1.1)
    g.draw_line_wood(cx, 0, cz - 3.5, cx, 2.2, cz - 0.8, radius=1.1)

    # Diagonal root spurs for natural asymmetry
    g.draw_line_wood(cx - 2.5, 0, cz + 2.4, cx - 0.6, 1.8, cz + 0.6, radius=0.9)
    g.draw_line_wood(cx + 2.5, 0, cz - 2.3, cx + 0.6, 1.8, cz - 0.6, radius=0.9)
    g.draw_line_wood(cx + 2.2, 0, cz + 2.5, cx + 0.5, 1.8, cz + 0.6, radius=0.85)
    g.draw_line_wood(cx - 2.3, 0, cz - 2.4, cx - 0.5, 1.8, cz - 0.6, radius=0.85)

    # 2. Main Trunk Body (y=3..8, sturdy ~0.5m thick trunk)
    g.fill_cylinder(cx, cz, 3, 5, r0=1.7, r1=1.6, token="W", cx1=cx + 0.1, cz1=cz + 0.1)
    g.fill_cylinder(cx + 0.1, cz + 0.1, 5, 8, r0=1.6, r1=1.9, token="W", cx1=cx, cz1=cz)

    # 3. Major Visible Supporting Boughs (y=7..13)
    # West / Left Bough:
    g.draw_line_wood(cx - 0.3, 7.5, cz, cx - 4.2, 11.8, cz - 0.2, radius=1.0)
    g.draw_line_wood(cx - 4.2, 11.8, cz - 0.2, cx - 5.0, 13.0, cz - 0.2, radius=0.7)

    # East / Right Bough:
    g.draw_line_wood(cx + 0.3, 8.0, cz, cx + 4.2, 12.5, cz + 0.3, radius=1.0)
    g.draw_line_wood(cx + 4.2, 12.5, cz + 0.3, cx + 5.0, 13.8, cz + 0.3, radius=0.7)

    # Front / South Bough (prominently visible in ISO facing viewer):
    g.draw_line_wood(cx, 7.2, cz + 0.3, cx + 0.3, 11.0, cz + 4.0, radius=1.0)
    g.draw_line_wood(cx + 0.3, 11.0, cz + 4.0, cx + 0.4, 12.5, cz + 4.8, radius=0.7)

    # Back / North Bough:
    g.draw_line_wood(cx, 8.0, cz - 0.3, cx - 0.3, 12.2, cz - 4.0, radius=0.95)
    g.draw_line_wood(cx - 0.3, 12.2, cz - 4.0, cx - 0.4, 13.5, cz - 4.8, radius=0.7)

    # Central Trunk Core (reaching up into summit dome):
    g.draw_line_wood(cx, 7.5, cz, cx, 17.5, cz, radius=1.1)

    # 4. Five Broad Lush Articulated Cloud Pods
    # Pod 1: West / Left Shoulder (y=11..18, broad horizontal pad)
    g.fill_blocky_pad(cx - 4.4, 14.8, cz - 0.2, prx=3.8, pry=3.2, prz=3.5, p=2.8, flat_bottom=True)

    # Pod 2: East / Right Shoulder (y=12..19, slightly higher for organic asymmetry)
    g.fill_blocky_pad(cx + 4.4, 15.8, cz + 0.3, prx=3.8, pry=3.2, prz=3.5, p=2.8, flat_bottom=True)

    # Pod 3: Front / South Lobe (y=10.5..17.5, lower forward mass, leaves branches visible)
    g.fill_blocky_pad(cx + 0.3, 13.8, cz + 4.2, prx=3.6, pry=3.0, prz=3.8, p=2.8, flat_bottom=True)

    # Pod 4: Back / North Lobe (y=12..19, rear mass)
    g.fill_blocky_pad(cx - 0.3, 15.5, cz - 4.2, prx=3.6, pry=3.2, prz=3.8, p=2.8, flat_bottom=True)

    # Pod 5: Broad Central Summit Dome (y=17..24, connects the 4 perimeter pads seamlessly)
    g.fill_blocky_pad(cx, 20.2, cz, prx=4.2, pry=3.2, prz=4.2, p=2.8, flat_bottom=False)

    # Summit Crest highlight pad (y=23..26.5, top cap, brings height to 27 layers = 4.05m)
    g.fill_blocky_pad(cx, 24.5, cz, prx=2.7, pry=1.8, prz=2.7, p=2.4, accent_top_ratio=0.15, flat_bottom=False)

    # 5. Carve deep negative space notches to ensure unmistakable multi-mass silhouette
    # Deep corner air cuts (4-leaf clover cross in TOP view):
    g.carve_box(1, 4, 10, 23, 1, 4)
    g.carve_box(1, 4, 10, 23, 13, 16)
    g.carve_box(13, 16, 10, 23, 1, 4)
    g.carve_box(13, 16, 10, 23, 13, 16)

    # Pronounced terrace step valleys between outer shoulders and summit dome
    g.carve_box(int(cx - 3.0), int(cx - 1.5), 17, 21, int(cz - 2.2), int(cz + 2.2))
    g.carve_box(int(cx + 1.5), int(cx + 3.0), 18, 22, int(cz - 2.2), int(cz + 2.2))
    g.carve_box(int(cx - 2.2), int(cx + 2.2), 16, 20, int(cz + 1.5), int(cz + 3.0))
    g.carve_box(int(cx - 2.2), int(cx + 2.2), 17, 21, int(cz - 3.0), int(cz - 1.5))

    g.remove_floating_voxels()
    return g


def build_tall_oak() -> VoxelGrid:
    """
    Tall Oak (Slot 1):
    Columnar fastigiate oak. Stately vertical presence, high crown with clear organic
    asymmetry between eastern and western shoulders, sweeping trunk, and visible boughs.
    Height: 34 layers (5.1m).
    Width: 15x15 grid (2.25m x 2.25m).
    """
    w, h, d = 15, 34, 15
    g = VoxelGrid(w, h, d)
    cx, cz = 7.0, 7.0

    # 1. Asymmetric Root Flare (y=0..2)
    g.fill_cylinder(cx, cz, 0, 2, r0=2.3, r1=1.5, token="W")
    # Primary strong buttress root southwest
    g.draw_line_wood(cx - 3.2, 0, cz + 1.4, cx, 2, cz, radius=0.85)
    # Secondary root east-northeast
    g.draw_line_wood(cx + 2.8, 0, cz - 0.8, cx, 2, cz, radius=0.8)
    # Shorter anchor north-northwest
    g.draw_line_wood(cx - 1.2, 0, cz - 2.5, cx, 2, cz, radius=0.75)
    # Ground toe southeast
    g.draw_line_wood(cx + 1.6, 0, cz + 2.2, cx, 2, cz, radius=0.7)

    # 2. Sweeping Organic Trunk (y=2..24)
    # Sweeps slightly southeast to northwest as it ascends
    g.fill_cylinder(cx, cz, 2, 7, r0=1.5, r1=1.3, token="W", cx1=cx - 0.3, cz1=cz + 0.4)
    g.fill_cylinder(cx - 0.3, cz + 0.4, 7, 13, r0=1.3, r1=1.1, token="W", cx1=cx - 0.6, cz1=cz + 0.6)
    g.fill_cylinder(cx - 0.6, cz + 0.6, 13, 19, r0=1.1, r1=0.9, token="W", cx1=cx - 0.1, cz1=cz - 0.1)
    g.fill_cylinder(cx - 0.1, cz - 0.1, 19, 25, r0=0.9, r1=0.7, token="W", cx1=cx + 0.1, cz1=cz - 0.2)

    # 3. Asymmetric Framework of Visible Boughs
    # Bough A: Lower East / North-East bough emerging at y=10..15
    g.draw_line_wood(cx - 0.4, 10, cz + 0.5, cx + 2.8, 14, cz - 1.8, radius=0.85)
    g.draw_line_wood(cx + 2.8, 14, cz - 1.8, cx + 4.2, 17, cz - 2.4, radius=0.6)

    # Bough B: Mid-tier West / South-West bough emerging higher at y=15..21
    g.draw_line_wood(cx - 0.5, 15, cz + 0.4, cx - 3.2, 19, cz + 2.2, radius=0.8)
    g.draw_line_wood(cx - 3.2, 19, cz + 2.2, cx - 4.4, 23, cz + 2.8, radius=0.55)

    # Bough C: Upper spire fork at y=23..29
    g.draw_line_wood(cx - 0.1, 23, cz - 0.1, cx - 0.6, 28, cz + 0.4, radius=0.6)
    g.draw_line_wood(cx - 0.1, 23, cz - 0.1, cx + 0.7, 27, cz - 0.5, radius=0.55)

    # 4. Foliage: 4 Asymmetric Volumetric Masses
    # Mass A: Lower East Shoulder (y=12..21) - hangs lower on the east flank
    g.fill_foliage_cluster(cx + 2.8, 16.0, cz - 1.8, rx=3.6, ry=4.2, rz=3.6, accent_top_ratio=0.50)

    # Mass B: Mid-tier West Shoulder (y=18..27) - sits higher on the opposing southwest flank
    g.fill_foliage_cluster(cx - 3.2, 22.5, cz + 2.2, rx=3.5, ry=4.6, rz=3.6, accent_top_ratio=0.50)

    # Mass C: Connecting North/Central Fill (y=16..24)
    g.fill_foliage_cluster(cx + 0.4, 20.0, cz - 1.6, rx=3.0, ry=4.0, rz=3.0, accent_top_ratio=0.45)

    # Mass D: Upper Spire Pinnacle (y=24..33) - stately narrow spire apex
    g.fill_foliage_cluster(cx - 0.2, 28.5, cz + 0.2, rx=2.8, ry=4.8, rz=2.8, accent_top_ratio=0.55)

    # Apex accent cap at summit (y=31..33)
    g.fill_foliage_cluster(cx - 0.2, 32.0, cz + 0.2, rx=1.7, ry=1.7, rz=1.7, accent_top_ratio=0.35)

    # Carve negative space under the boughs to ensure visible branches and undercut read
    g.carve_box(int(cx + 0.5), int(cx + 2.5), 11, 14, int(cz - 1.0), int(cz + 1.0))
    g.carve_box(int(cx - 3.5), int(cx - 1.5), 16, 18, int(cz + 0.5), int(cz + 2.0))

    g.remove_floating_voxels()
    return g


def build_broad_oak() -> VoxelGrid:
    """
    Broad Oak (Slot 2):
    Ancient, expansive plains oak with a massive gnarled trunk and heavy spreading boughs
    supporting a wide, multi-lobed horizontal umbrella canopy.
    Height: 24 layers (3.6m).
    Width: 24x24 grid (3.6m x 3.6m).
    """
    w, h, d = 24, 24, 24
    g = VoxelGrid(w, h, d)
    cx, cz = 11.5, 11.5

    # 1. Massive Ancient Root Flare (y=0..3)
    g.fill_cylinder(cx, cz, 0, 3, r0=4.0, r1=2.7, token="W")
    g.draw_line_wood(cx - 4.6, 0, cz - 1.0, cx, 3, cz, radius=1.4)
    g.draw_line_wood(cx + 4.6, 0, cz + 1.0, cx, 3, cz, radius=1.4)
    g.draw_line_wood(cx - 1.0, 0, cz - 4.6, cx, 3, cz, radius=1.4)
    g.draw_line_wood(cx + 1.0, 0, cz + 4.6, cx, 3, cz, radius=1.4)
    g.draw_line_wood(cx + 3.2, 0, cz - 3.2, cx, 3, cz, radius=1.1)
    g.draw_line_wood(cx - 3.2, 0, cz + 3.2, cx, 3, cz, radius=1.1)

    # 2. Thick Gnarled Trunk (y=3..8, ~1.2m tall, very stout)
    g.fill_cylinder(cx, cz, 3, 8, r0=2.5, r1=2.1, token="W", cx1=cx + 0.2, cz1=cz - 0.2)

    # 3. Four Massive Sprawling Horizontal Boughs (clearly visible framing the canopy!)
    # Bough 1: West sprawling arm (reaches X=3..5)
    g.draw_line_wood(cx, 7, cz, cx - 4.8, 10, cz - 0.8, radius=1.3)
    g.draw_line_wood(cx - 4.8, 10, cz - 0.8, cx - 7.5, 12, cz - 1.2, radius=0.9)
    g.draw_line_wood(cx - 4.8, 10, cz - 0.8, cx - 6.8, 13, cz + 2.2, radius=0.7)

    # Bough 2: South-East sprawling arm (reaches X=19, Z=19)
    g.draw_line_wood(cx, 7, cz, cx + 4.6, 10, cz + 4.4, radius=1.3)
    g.draw_line_wood(cx + 4.6, 10, cz + 4.4, cx + 7.8, 12, cz + 6.6, radius=0.9)
    g.draw_line_wood(cx + 4.6, 10, cz + 4.4, cx + 6.8, 13, cz + 2.0, radius=0.7)

    # Bough 3: North-East sprawling arm (reaches X=18, Z=4)
    g.draw_line_wood(cx, 7, cz, cx + 4.2, 10, cz - 4.4, radius=1.2)
    g.draw_line_wood(cx + 4.2, 10, cz - 4.4, cx + 7.2, 12, cz - 6.4, radius=0.85)

    # Bough 4: Center-North fork holding central dome
    g.draw_line_wood(cx, 7, cz, cx - 0.6, 12, cz + 0.4, radius=1.2)
    g.draw_line_wood(cx - 0.6, 12, cz + 0.4, cx - 0.8, 16, cz - 0.2, radius=0.8)

    # 4. Foliage: 4 Wide Horizontal Cloud Masses
    # Flank Cloud West (y=9..17)
    g.fill_foliage_cluster(cx - 6.2, 13.0, cz - 0.4, rx=4.8, ry=3.6, rz=4.6, accent_top_ratio=0.45)

    # Flank Cloud South-East (y=9..17)
    g.fill_foliage_cluster(cx + 5.8, 12.8, cz + 5.2, rx=4.6, ry=3.4, rz=4.8, accent_top_ratio=0.45)

    # Flank Cloud North-East (y=10..18)
    g.fill_foliage_cluster(cx + 5.2, 13.5, cz - 4.8, rx=4.4, ry=3.6, rz=4.4, accent_top_ratio=0.45)

    # Flank Cloud South-West (y=9..16)
    g.fill_foliage_cluster(cx - 2.8, 12.5, cz + 5.6, rx=4.0, ry=3.2, rz=3.8, accent_top_ratio=0.45)

    # Central Broad Plateau Summit (y=12..23)
    g.fill_foliage_cluster(cx - 0.2, 17.5, cz + 0.2, rx=6.2, ry=5.2, rz=5.8, accent_top_ratio=0.55)

    # Summit top terrace cap (y=21..23)
    g.fill_foliage_cluster(cx - 0.4, 21.5, cz, rx=4.0, ry=2.2, rz=3.8, accent_top_ratio=0.35)

    g.remove_floating_voxels()
    return g


def build_young_oak() -> VoxelGrid:
    """
    Young Small Oak (Slot 3):
    Juvenile sapling / small tree (~0.6x adult scale).
    Height: 16 layers (2.4m).
    Width: 11x11 grid (1.65m x 1.65m).
    """
    w, h, d = 11, 16, 11
    g = VoxelGrid(w, h, d)
    cx, cz = 5.0, 5.0

    # 1. Root collar (y=0..1)
    g.fill_cylinder(cx, cz, 0, 1, r0=1.5, r1=1.0, token="W")
    g.draw_line_wood(cx - 1.4, 0, cz, cx, 1, cz, radius=0.6)
    g.draw_line_wood(cx + 1.4, 0, cz, cx, 1, cz, radius=0.6)
    g.draw_line_wood(cx, 0, cz - 1.4, cx, 1, cz, radius=0.6)
    g.draw_line_wood(cx, 0, cz + 1.4, cx, 1, cz, radius=0.6)

    # 2. Slender juvenile trunk (y=1..6, ~0.9m tall)
    g.fill_cylinder(cx, cz, 1, 6, r0=0.9, r1=0.7, token="W", cx1=cx + 0.2, cz1=cz - 0.1)

    # 3. Small branching fork (y=5..9)
    g.draw_line_wood(cx + 0.2, 5, cz - 0.1, cx + 1.8, 8, cz + 1.2, radius=0.55)
    g.draw_line_wood(cx + 0.2, 5, cz - 0.1, cx - 1.6, 9, cz - 1.0, radius=0.55)

    # 4. Compact juvenile crown: 2 energetic overlapping masses (y=6..15)
    # Lobe 1 (South-East)
    g.fill_foliage_cluster(cx + 1.0, 9.5, cz + 0.8, rx=2.8, ry=3.0, rz=2.8, accent_top_ratio=0.45)
    # Lobe 2 (North-West summit)
    g.fill_foliage_cluster(cx - 0.8, 12.0, cz - 0.6, rx=3.0, ry=3.4, rz=3.0, accent_top_ratio=0.50)

    g.remove_floating_voxels()
    return g


def build_shrub_oak() -> VoxelGrid:
    """
    Shrub / Bush Oak (Slot 4):
    Low sprawling dwarf oak / bush (~1.35m height).
    Height: 9 layers (1.35m).
    Width: 12x12 grid (1.8m x 1.8m).
    """
    w, h, d = 12, 9, 12
    g = VoxelGrid(w, h, d)
    cx, cz = 5.5, 5.5

    # 1. Multi-stem base (y=0..2)
    g.fill_cylinder(cx, cz, 0, 2, r0=1.8, r1=1.3, token="W")
    g.draw_line_wood(cx - 2.2, 0, cz - 0.6, cx, 1, cz, radius=0.7)
    g.draw_line_wood(cx + 2.2, 0, cz + 0.6, cx, 1, cz, radius=0.7)
    g.draw_line_wood(cx + 0.4, 0, cz - 2.2, cx, 1, cz, radius=0.7)
    g.draw_line_wood(cx - 0.4, 0, cz + 2.2, cx, 1, cz, radius=0.7)

    # Short woody stem spurs visible at ground line
    g.draw_line_wood(cx, 1, cz, cx - 2.4, 3, cz + 1.4, radius=0.55)
    g.draw_line_wood(cx, 1, cz, cx + 2.2, 3, cz - 1.2, radius=0.55)
    g.draw_line_wood(cx, 1, cz, cx + 0.6, 4, cz + 2.2, radius=0.55)

    # 2. Three low sprawling hummocks (y=1..8)
    # Hummock 1 (South-West)
    g.fill_foliage_cluster(cx - 2.0, 3.8, cz + 1.4, rx=3.0, ry=2.4, rz=3.0, accent_top_ratio=0.45)
    # Hummock 2 (North-East)
    g.fill_foliage_cluster(cx + 1.8, 4.2, cz - 1.2, rx=3.2, ry=2.6, rz=3.0, accent_top_ratio=0.45)
    # Hummock 3 (Center-South summit hummock)
    g.fill_foliage_cluster(cx + 0.3, 5.5, cz + 0.9, rx=3.2, ry=2.8, rz=3.2, accent_top_ratio=0.55)

    g.remove_floating_voxels()
    return g


# -------------------------------------------------------------------------
# VARIANT CONFIGURATION TABLE
# -------------------------------------------------------------------------

VARIANTS = [
    {
        "slot": 0,
        "slug": "var_0_standard_oak",
        "title": "Standard Oak",
        "description": "Базовое взрослое дерево с естественным балансом кроны, видимыми сучьями и контрфорсными корнями.",
        "builder": build_standard_oak,
    },
    {
        "slot": 1,
        "slug": "var_1_tall_oak",
        "title": "Tall Oak",
        "description": "Высокий пирамидальный/колоновидный силуэт (5.1м) с длинным стволом и трёхъярусной кроной.",
        "builder": build_tall_oak,
    },
    {
        "slot": 2,
        "slug": "var_2_broad_oak",
        "title": "Broad Oak",
        "description": "Широкая тяжёлая зонтичная крона (3.6м размах) с мощным стволом и 4 раскидистыми сучьями.",
        "builder": build_broad_oak,
    },
    {
        "slot": 3,
        "slug": "var_3_young_oak",
        "title": "Young Oak",
        "description": "Молодое дерево заметно меньшего размера (~2.4м, ~0.6x от взрослого стандарта).",
        "builder": build_young_oak,
    },
    {
        "slot": 4,
        "slug": "var_4_shrub_oak",
        "title": "Shrub / Bush Oak",
        "description": "Низкий кустарниковый дуб (~1.35м) для горных и переходных зон.",
        "builder": build_shrub_oak,
    },
]


def author_all(target_slug: str | None = None) -> None:
    FAMILY_DIR.mkdir(parents=True, exist_ok=True)
    summary = []

    variants_to_build = [v for v in VARIANTS if target_slug is None or target_slug == "all" or v["slug"] == target_slug]
    if not variants_to_build:
        raise ValueError(f"No matching variants found for: {target_slug}")

    for v in variants_to_build:
        slug = v["slug"]
        pkg_dir = FAMILY_DIR / slug
        pkg_dir.mkdir(parents=True, exist_ok=True)
        (pkg_dir / "source").mkdir(parents=True, exist_ok=True)
        (pkg_dir / "output").mkdir(parents=True, exist_ok=True)
        (pkg_dir / "review").mkdir(parents=True, exist_ok=True)

        print(f"Authoring {v['title']} ({slug})...")
        grid = v["builder"]()
        layers = grid.to_json_layers()

        occupied = 0
        mat_counts = {"W": 0, "D": 0, "L": 0}
        for layer in layers:
            for row in layer["rows"]:
                for ch in row:
                    if ch in mat_counts:
                        mat_counts[ch] += 1
                        occupied += 1

        source_data = {
            "version": 1,
            "name": f"tree_oak_{slug}",
            "voxel_size": VOXEL_SIZE,
            "origin": "bottom_center",
            "materials": SHARED_MATERIALS,
            "layers": layers,
        }

        source_file = pkg_dir / "source" / "voxels.json"
        source_file.write_text(
            json.dumps(source_data, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )

        manifest_data = {
            "name": f"tree_oak_{slug}",
            "type": "voxel_static",
            "version": 1,
            "source": "source/voxels.json",
            "outputs": {
                "model": "output/model.glb",
            },
            "review": {
                "required_views": ["iso", "front", "side", "top"],
            },
            "budgets": {
                "max_materials": 3,
                "max_triangles": 5000,
            },
        }
        manifest_file = pkg_dir / "manifest.json"
        manifest_file.write_text(
            json.dumps(manifest_data, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )

        request_md = f"""# Request: {v['title']} (`{slug}`)

## Role in Family
- Slot: {v['slot']}
- Name: {v['title']}
- Description: {v['description']}

## Art Direction & Integration Requirements
- **Integration slot**: `ResourceTree.tree_variation = {v['slot']}` in `alex123321-maker/Cube-Siege`.
- **Silhouette**: Трёхмерная асимметричная воксельная форма; ствол и крупные массы кроны читаются с игровой камеры.
- **Pivot/Origin**: `bottom_center` ствола (y=0 плоский контакт с землей).
- **Voxel Density**: 0.15 м / воксель (согласовано с `destructible_rock`).
- **Shared Palette**:
  - `wood_bark` (`W`): тёмная кора дуба (#4a2f1b), roughness 0.92, metallic 0.0;
  - `foliage_base` (`D`): глубокая насыщенная лесная листва (#3b6b22), roughness 0.88, metallic 0.0;
  - `foliage_accent` (`L`): тёплый золотисто-зелёный акцент для верхних террас и освещённых шапок (#5e932b), roughness 0.82, metallic 0.0.
- **Occlusion**: Компактная область кроны для runtime camera-occlusion fade; без одиночных летающих вокселей.
"""
        initialize_text(pkg_dir / "request.md", request_md)

        info = {
            "slot": v["slot"],
            "slug": slug,
            "title": v["title"],
            "grid": f"{grid.width}x{grid.height}x{grid.depth}",
            "dimensions_m": f"{grid.width * VOXEL_SIZE:.2f} x {grid.height * VOXEL_SIZE:.2f} x {grid.depth * VOXEL_SIZE:.2f}",
            "occupied_voxels": occupied,
            "wood": mat_counts["W"],
            "foliage_base": mat_counts["D"],
            "foliage_accent": mat_counts["L"],
        }
        summary.append(info)
        print(f"  Grid: {info['grid']}, Occupied: {occupied} voxels (W:{info['wood']}, D:{info['foliage_base']}, L:{info['foliage_accent']})")

    if target_slug is None or target_slug == "all":
        # Author Family README.md only when building full family
        family_readme = f"""# Oak Tree Family (Семейство дубовых деревьев)

Семейство статических воксельных ассетов (`voxel_static`) для **Cube Siege**, заменяющее box-placeholder деревья в основном репозитории `alex123321-maker/Cube-Siege` (Issue #5).

## Варианты и сопоставление со слотами ResourceTree

В основном репозитории `ResourceTree.tree_variation` использует индексы `0..4`:

| Слот | Вариант | Папка | Сетка (X×Y×Z) | Габариты (м) | Воксели | Описание силуэта |
|:---:|---|---|:---:|:---:|:---:|---|
| **0** | **Standard Oak** | `var_0_standard_oak` | {summary[0]['grid']} | {summary[0]['dimensions_m']} | {summary[0]['occupied_voxels']} | Базовое взрослое дерево; ствол с контрфорсными корнями, 4 раскидистых сука под кроной, 5 выраженных блочных масс (4 боковых лопасти + приподнятая вершина). |
| **1** | **Tall Oak** | `var_1_tall_oak` | {summary[1]['grid']} | {summary[1]['dimensions_m']} | {summary[1]['occupied_voxels']} | Высокий пирамидальный/колоновидный силуэт (5.1м); трёхъярусная вытянутая крона, читаемые ветви. |
| **2** | **Broad Oak** | `var_2_broad_oak` | {summary[2]['grid']} | {summary[2]['dimensions_m']} | {summary[2]['occupied_voxels']} | Широкая тяжёлая крона (3.6м размах); массивный ствол, 4 раскидистых сука под кроной. |
| **3** | **Young Oak** | `var_3_young_oak` | {summary[3]['grid']} | {summary[3]['dimensions_m']} | {summary[3]['occupied_voxels']} | Молодое дерево (~2.4м); компактная двухдольная крона, тонкий ствол с развилкой. |
| **4** | **Shrub / Bush Oak** | `var_4_shrub_oak` | {summary[4]['grid']} | {summary[4]['dimensions_m']} | {summary[4]['occupied_voxels']} | Низкий кустарниковый дуб (~1.35м); 3 приземистых холмика листвы с прикорневыми ветвями. |

## Палитра материалов (PBR)

Все варианты используют единую палитру из 3 материалов:
1. `wood_bark` (`W`): тёплая тёмная кора дуба (#4a2f1b), roughness 0.92, metallic 0.0;
2. `foliage_base` (`D`): глубокая насыщенная лесная листва (#3b6b22), roughness 0.88, metallic 0.0;
3. `foliage_accent` (`L`): тёплый золотисто-зелёный акцент для верхних террас и освещённых шапок (#5e932b), roughness 0.82, metallic 0.0.

## Структура пакета

```text
assets/environment/tree_oak/
├── README.md
├── references/
│   ├── README.md
│   └── tree_concept_reference.png
├── review/
│   ├── contact_sheet.png
│   ├── comparison_sheet.png
│   ├── reference_vs_3d_comparison.png
│   ├── variants_concept_vs_3d.png
│   ├── gameplay_mockup.png
│   ├── metrics_summary.json
│   └── review.md
├── var_0_standard_oak/
├── var_1_tall_oak/
├── var_2_broad_oak/
├── var_3_young_oak/
└── var_4_shrub_oak/
```
"""
        (FAMILY_DIR / "README.md").write_text(family_readme, encoding="utf-8")
        print(f"\n[DONE] Successfully authored all 5 oak tree variants in {FAMILY_DIR}")
    else:
        print(f"\n[DONE] Successfully authored {target_slug} in {FAMILY_DIR / target_slug}")


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Author voxel source for tree oak variants.")
    parser.add_argument("--variant", default="all", help="Variant slug to author (default: all)")
    args = parser.parse_args()
    author_all(target_slug=args.variant)

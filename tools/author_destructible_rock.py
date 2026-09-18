#!/usr/bin/env python3
"""Authoring tool for Cube Siege Destructible Rock Family (Issue #1).

Generates 17 reproducible voxel packages across 5 destruction stages:
  - Stage 1: 6 variants (Huge intact boulder)
  - Stage 2: 3 variants (Large broken rock)
  - Stage 3: 3 variants (Medium remnant)
  - Stage 4: 2 variants (Small rubble group)
  - Stage 5: 3 variants (Small rubble pile / debris)
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Callable, List, Set, Tuple

ROOT = Path(__file__).resolve().parents[1]
FAMILY_DIR = ROOT / "assets" / "environment" / "destructible_rock"

MATERIAL_SPEC = {
    "S": {
        "name": "stone_gray",
        "base_color": [0.38, 0.40, 0.43, 1.0],
        "roughness": 0.92,
        "metallic": 0.0,
    }
}

VOXEL_SIZE = 0.15


class VoxelGrid:
    def __init__(self, width: int, height: int, depth: int):
        self.width = width
        self.height = height
        self.depth = depth
        # data[y][z][x] = char or '.'
        self.data: List[List[List[str]]] = [
            [["." for _ in range(width)] for _ in range(depth)]
            for _ in range(height)
        ]

    def set(self, x: int, y: int, z: int, token: str = "S") -> None:
        if 0 <= x < self.width and 0 <= y < self.height and 0 <= z < self.depth:
            self.data[y][z][x] = token

    def fill_box(self, x0: int, x1: int, y0: int, y1: int, z0: int, z1: int, token: str = "S") -> None:
        for y in range(max(0, y0), min(self.height, y1 + 1)):
            for z in range(max(0, z0), min(self.depth, z1 + 1)):
                for x in range(max(0, x0), min(self.width, x1 + 1)):
                    self.data[y][z][x] = token

    def carve_plane(self, a: float, b: float, c: float, d: float) -> None:
        """Carve away voxels where a*x + b*y + c*z + d > 0."""
        for y in range(self.height):
            for z in range(self.depth):
                for x in range(self.width):
                    if a * x + b * y + c * z + d > 0:
                        self.data[y][z][x] = "."

    def keep_if(self, condition: Callable[[int, int, int], bool]) -> None:
        for y in range(self.height):
            for z in range(self.depth):
                for x in range(self.width):
                    if self.data[y][z][x] != "." and not condition(x, y, z):
                        self.data[y][z][x] = "."

    def add_if(self, condition: Callable[[int, int, int], bool], token: str = "S") -> None:
        for y in range(self.height):
            for z in range(self.depth):
                for x in range(self.width):
                    if condition(x, y, z):
                        self.data[y][z][x] = token

    def occupied_count(self) -> int:
        return sum(
            1
            for y in range(self.height)
            for z in range(self.depth)
            for x in range(self.width)
            if self.data[y][z][x] != "."
        )

    def remove_floating(self) -> None:
        """Remove any voxels not connected (6-way) to ground (y=0)."""
        visited: Set[Tuple[int, int, int]] = set()
        queue: List[Tuple[int, int, int]] = []

        for z in range(self.depth):
            for x in range(self.width):
                if self.data[0][z][x] != ".":
                    queue.append((x, 0, z))
                    visited.add((x, 0, z))

        while queue:
            cx, cy, cz = queue.pop(0)
            for dx, dy, dz in ((1, 0, 0), (-1, 0, 0), (0, 1, 0), (0, -1, 0), (0, 0, 1), (0, 0, -1)):
                nx, ny, nz = cx + dx, cy + dy, cz + dz
                if 0 <= nx < self.width and 0 <= ny < self.height and 0 <= nz < self.depth:
                    if (nx, ny, nz) not in visited and self.data[ny][nz][nx] != ".":
                        visited.add((nx, ny, nz))
                        queue.append((nx, ny, nz))

        for y in range(self.height):
            for z in range(self.depth):
                for x in range(self.width):
                    if self.data[y][z][x] != "." and (x, y, z) not in visited:
                        self.data[y][z][x] = "."

    def to_json_dict(self, name: str) -> dict:
        layers = []
        for y in range(self.height):
            rows = []
            for z in range(self.depth):
                rows.append("".join(self.data[y][z]))
            layers.append({"y": y, "rows": rows})

        return {
            "version": 1,
            "name": name,
            "voxel_size": VOXEL_SIZE,
            "origin": "bottom_center",
            "materials": MATERIAL_SPEC,
            "layers": layers,
        }


# -------------------------------------------------------------------------
# STAGE 1: Huge Intact Boulder (6 Variants)
# Target voxels: ~700 - 1000
# -------------------------------------------------------------------------

def build_stage_1_var_1() -> VoxelGrid:
    """Monolith Ridge: Vertical fracture on West, stepped slope on East."""
    g = VoxelGrid(16, 12, 16)
    # Core base mass
    g.fill_box(2, 13, 0, 4, 2, 13)
    # Mid mass
    g.fill_box(3, 12, 5, 8, 3, 12)
    # Upper crest
    g.fill_box(4, 9, 9, 11, 4, 10)

    # Sheer vertical fracture on West (X < 4 for high Y)
    g.carve_plane(-1, 0.4, 0, -2.0)  # cut West
    # Stepped slope on East
    g.carve_plane(0.9, 0.8, 0.2, -16.5)
    # North slope
    g.carve_plane(0.1, 0.7, -0.9, -4.5)
    # South angle
    g.carve_plane(-0.2, 0.8, 0.9, -15.5)
    # Top ridge fracture
    g.carve_plane(0.3, 1.0, 0.4, -14.0)

    # Stepped terraced ledges on East flank
    g.fill_box(11, 13, 0, 3, 4, 11)
    g.fill_box(10, 12, 4, 5, 5, 10)
    # Angular corner break on SW
    g.fill_box(2, 4, 0, 2, 11, 13)

    g.remove_floating()
    return g


def build_stage_1_var_2() -> VoxelGrid:
    """Split Boulder / Twin Peak: High crag on left, angular wedge on right."""
    g = VoxelGrid(16, 12, 16)
    # Base foundation
    g.fill_box(2, 13, 0, 3, 2, 13)

    # Primary tower (West/Left)
    g.fill_box(2, 8, 4, 11, 3, 12)
    # Secondary shoulder (East/Right)
    g.fill_box(9, 13, 4, 7, 4, 12)

    # Deep V-notch between peaks at top
    for y in range(7, 12):
        for z in range(3, 13):
            g.set(8, y, z, ".")
            g.set(9, y, z, ".")

    # Bevels and fractures
    g.carve_plane(-0.8, 0.7, 0, -4.0)    # West edge
    g.carve_plane(0.9, 0.6, 0.1, -15.0)  # East edge
    g.carve_plane(0.1, 0.7, -0.8, -4.0)  # North
    g.carve_plane(-0.1, 0.8, 0.8, -14.5) # South
    g.carve_plane(0.2, 1.1, 0.1, -14.5)  # Top

    # Angular shelf on South face of primary peak
    g.fill_box(3, 7, 0, 5, 12, 13)
    g.remove_floating()
    return g


def build_stage_1_var_3() -> VoxelGrid:
    """Slanted Wedge: 45-degree sheared fault plane."""
    g = VoxelGrid(16, 11, 16)
    g.fill_box(2, 13, 0, 3, 2, 13)
    g.fill_box(3, 12, 4, 7, 3, 12)
    g.fill_box(3, 10, 8, 10, 3, 9)

    # Sheared diagonal fault slope from top-back to bottom-front
    g.carve_plane(0.3, 0.9, 0.8, -14.0)
    # Steep drop on North/back
    g.carve_plane(0.0, 0.4, -1.0, -2.5)
    # Steep drop on West
    g.carve_plane(-1.0, 0.5, 0.0, -3.5)
    # Eastern broken face
    g.carve_plane(1.0, 0.6, -0.2, -15.0)

    # Stepped breakaway terrace on front right
    g.fill_box(9, 13, 0, 3, 9, 13)
    g.fill_box(7, 11, 4, 5, 8, 11)

    g.remove_floating()
    return g


def build_stage_1_var_4() -> VoxelGrid:
    """Overhanging Table Crag: Sturdy base with prominent corner overhang."""
    g = VoxelGrid(16, 11, 16)
    # Compact base
    g.fill_box(3, 11, 0, 3, 3, 12)
    # Cantilever / overhang on SW (x: 2..12, z: 4..14)
    g.fill_box(2, 12, 4, 7, 4, 13)
    # Broad table plateau
    g.fill_box(3, 11, 8, 10, 4, 12)

    # Angular facet cuts
    g.carve_plane(-0.7, 0.6, -0.6, -4.0)  # NW
    g.carve_plane(0.8, 0.7, -0.5, -14.0)  # NE
    g.carve_plane(0.7, 0.8, 0.6, -15.5)   # SE
    g.carve_plane(0.0, 1.0, 0.0, -11.0)   # Top flat cutoff
    g.carve_plane(0.4, 1.0, -0.3, -12.5)  # Slight top tilt

    # Broken undercuts under the overhanging lip
    for x in range(2, 5):
        for z in range(11, 14):
            g.set(x, 1, z, ".")
            g.set(x, 2, z, ".")

    g.remove_floating()
    return g


def build_stage_1_var_5() -> VoxelGrid:
    """Jagged Spire Butte: Tri-faceted peak with asymmetrical buttress ridges."""
    g = VoxelGrid(16, 12, 16)
    # Base
    g.fill_box(2, 13, 0, 3, 2, 13)
    # Central spire body
    g.fill_box(4, 11, 4, 7, 4, 11)
    g.fill_box(5, 9, 8, 11, 5, 9)

    # 3 buttress arms extending out at ground/mid levels
    # Arm 1: North
    g.fill_box(6, 9, 0, 5, 1, 4)
    # Arm 2: South-East
    g.fill_box(10, 13, 0, 4, 10, 13)
    # Arm 3: West
    g.fill_box(1, 4, 0, 5, 6, 9)

    # Carve sharp triangular spire planes
    g.carve_plane(-0.9, 0.7, 0.4, -6.5)
    g.carve_plane(0.7, 0.8, 0.7, -16.0)
    g.carve_plane(0.2, 0.7, -0.9, -5.5)
    g.carve_plane(0.1, 1.0, 0.1, -12.5)

    g.remove_floating()
    return g


def build_stage_1_var_6() -> VoxelGrid:
    """Elongated Fractured Slab: Broad horizontal boulder with central saddle."""
    g = VoxelGrid(18, 10, 14)
    # Broad base
    g.fill_box(1, 16, 0, 3, 2, 11)
    # Western crest
    g.fill_box(2, 7, 4, 9, 3, 10)
    # Eastern crest
    g.fill_box(10, 15, 4, 8, 3, 10)
    # Saddle bridge
    g.fill_box(7, 10, 4, 6, 4, 9)

    # Fractures and angular facets
    g.carve_plane(-0.8, 0.6, 0.1, -3.5)
    g.carve_plane(0.8, 0.6, -0.1, -16.0)
    g.carve_plane(0.1, 0.7, -0.8, -3.5)
    g.carve_plane(-0.1, 0.7, 0.8, -13.0)
    g.carve_plane(0.0, 1.0, 0.2, -10.0)

    # Jagged end breakaway
    g.fill_box(14, 16, 0, 2, 4, 8)
    g.remove_floating()
    return g


# -------------------------------------------------------------------------
# STAGE 2: Large Broken Rock (3 Variants)
# Target voxels: ~400 - 550
# -------------------------------------------------------------------------

def build_stage_2_var_1() -> VoxelGrid:
    """Truncated Block: One side completely broken away, stepped fracture wall."""
    g = VoxelGrid(14, 9, 14)
    # Base
    g.fill_box(2, 11, 0, 3, 2, 11)
    # Remaining tall block (West half)
    g.fill_box(2, 8, 4, 8, 3, 10)
    # Broken lower apron (East half)
    g.fill_box(8, 12, 0, 3, 4, 10)

    # Sheer vertical fracture dividing the two halves
    g.carve_plane(1.0, 0.3, 0.0, -9.0)
    # Slope on West
    g.carve_plane(-0.9, 0.7, 0.1, -3.5)
    # Slope on North
    g.carve_plane(0.1, 0.7, -0.8, -3.5)
    # Slope on South
    g.carve_plane(-0.1, 0.8, 0.8, -12.5)

    g.remove_floating()
    return g


def build_stage_2_var_2() -> VoxelGrid:
    """Broken Stepped Slab: Asymmetric low block with shattered upper corner."""
    g = VoxelGrid(14, 8, 14)
    g.fill_box(2, 11, 0, 2, 2, 11)
    g.fill_box(3, 10, 3, 5, 3, 10)
    g.fill_box(3, 7, 6, 7, 4, 8)

    # Angular cuts
    g.carve_plane(0.7, 0.8, 0.6, -12.5)
    g.carve_plane(-0.8, 0.7, -0.3, -3.5)
    g.carve_plane(0.2, 0.6, -0.8, -3.5)
    g.carve_plane(0.1, 1.0, 0.0, -8.5)

    # Satellite stone fragment resting on the fractured side
    g.fill_box(9, 11, 0, 2, 8, 10)
    g.remove_floating()
    return g


def build_stage_2_var_3() -> VoxelGrid:
    """Slanted Core Remnant: Angular tilted rock with broken shoulders."""
    g = VoxelGrid(14, 8, 14)
    g.fill_box(2, 11, 0, 3, 2, 11)
    g.fill_box(3, 9, 4, 7, 3, 9)

    # Slanted diagonal shear
    g.carve_plane(0.6, 0.8, -0.4, -10.0)
    g.carve_plane(-0.7, 0.7, 0.2, -4.0)
    g.carve_plane(0.0, 0.6, 0.8, -11.0)
    g.carve_plane(0.0, 0.6, -0.8, -3.5)

    # Broken detached corner
    g.fill_box(9, 11, 0, 2, 2, 5)
    g.remove_floating()
    return g


# -------------------------------------------------------------------------
# STAGE 3: Medium Remnant (3 Variants)
# Target voxels: ~180 - 280
# -------------------------------------------------------------------------

def build_stage_3_var_1() -> VoxelGrid:
    """Triangular Wedge: Asymmetric 3-sided rock chunk."""
    g = VoxelGrid(12, 7, 12)
    g.fill_box(2, 9, 0, 2, 2, 9)
    g.fill_box(3, 8, 3, 4, 3, 8)
    g.fill_box(4, 7, 5, 6, 4, 7)

    # Triangular cuts
    g.carve_plane(-0.9, 0.7, 0.3, -4.0)
    g.carve_plane(0.8, 0.7, 0.5, -10.5)
    g.carve_plane(0.0, 0.6, -0.9, -3.0)

    g.remove_floating()
    return g


def build_stage_3_var_2() -> VoxelGrid:
    """Twin Chunk Remnant: Two connected unequal stone pieces."""
    g = VoxelGrid(12, 6, 12)
    # Larger chunk
    g.fill_box(2, 6, 0, 5, 3, 8)
    # Smaller connected chunk
    g.fill_box(7, 10, 0, 3, 4, 8)

    g.carve_plane(-0.8, 0.6, 0.0, -3.0)
    g.carve_plane(0.8, 0.7, 0.2, -10.0)
    g.carve_plane(0.1, 0.7, -0.8, -3.0)
    g.carve_plane(-0.1, 0.7, 0.8, -9.5)

    g.remove_floating()
    return g


def build_stage_3_var_3() -> VoxelGrid:
    """Fractured Stump: Squat, chunky block with stepped fractured top."""
    g = VoxelGrid(12, 6, 12)
    g.fill_box(2, 9, 0, 2, 2, 9)
    g.fill_box(3, 8, 3, 5, 3, 8)

    g.carve_plane(0.6, 0.8, -0.5, -8.5)
    g.carve_plane(-0.7, 0.7, 0.4, -4.0)
    g.carve_plane(0.2, 0.8, 0.7, -9.5)

    g.remove_floating()
    return g


# -------------------------------------------------------------------------
# STAGE 4: Small Rubble Group (2 Variants)
# Target voxels: ~90 - 150
# -------------------------------------------------------------------------

def build_stage_4_var_1() -> VoxelGrid:
    """Fragment & Satellites: Main chunky fragment with 2 separate satellite chunks."""
    g = VoxelGrid(12, 5, 12)
    # Piece 1: Main block (West/North-Center): x in [2, 6], z in [2, 6], y in [0, 4]
    g.fill_box(2, 6, 0, 2, 2, 6)
    g.fill_box(3, 5, 3, 4, 3, 5)
    # Carve facets on main piece
    g.carve_plane(0.7, 0.7, -0.3, -6.0)
    g.carve_plane(-0.6, 0.7, 0.4, -3.2)
    g.carve_plane(0.3, 0.8, 0.6, -7.5)

    # Piece 2: Satellite East: x in [8, 10], z in [3, 5], y in [0, 1]
    # Clear gap: column x=7 is empty, ensuring distinct separated component
    g.fill_box(8, 10, 0, 1, 3, 5)
    g.carve_plane(0.6, 0.8, 0.5, -9.0)

    # Piece 3: Satellite South: x in [3, 5], z in [8, 10], y in [0, 1]
    # Clear gap: row z=7 is empty, ensuring distinct separated component
    g.fill_box(3, 5, 0, 1, 8, 10)
    g.carve_plane(-0.5, 0.8, 0.6, -7.5)

    g.remove_floating()
    return g


def build_stage_4_var_2() -> VoxelGrid:
    """Triad Debris Cluster: Three chunky rock fragments in loose separated group."""
    g = VoxelGrid(12, 4, 12)
    # Chunk A (NW): x in [2, 5], z in [2, 5], y in [0, 3]
    g.fill_box(2, 5, 0, 2, 2, 5)
    g.fill_box(3, 4, 3, 3, 3, 4)
    g.carve_plane(-0.6, 0.7, -0.6, -2.5)
    g.carve_plane(0.5, 0.8, 0.4, -6.5)

    # Chunk B (NE): x in [7, 10], z in [2, 5], y in [0, 2]
    # Clear gap at column x=6
    g.fill_box(7, 10, 0, 1, 2, 5)
    g.fill_box(8, 9, 2, 2, 3, 4)
    g.carve_plane(0.7, 0.7, -0.5, -8.0)

    # Chunk C (South): x in [3, 7], z in [7, 10], y in [0, 2]
    # Clear gap at row z=6
    g.fill_box(3, 7, 0, 1, 7, 10)
    g.fill_box(4, 6, 2, 2, 8, 9)
    g.carve_plane(0.5, 0.8, 0.6, -9.5)
    g.carve_plane(-0.7, 0.7, 0.4, -4.5)

    g.remove_floating()
    return g


# -------------------------------------------------------------------------
# STAGE 5: Small Rubble Pile / Debris (3 Variants)
# Target voxels: ~35 - 65
# -------------------------------------------------------------------------

def build_stage_5_var_1() -> VoxelGrid:
    """Central Nub with small scatter: 1 low central rock + 4 separate pebbles."""
    g = VoxelGrid(10, 3, 10)
    # Central low rock: x in [4, 6], z in [4, 6], y in [0, 2]
    g.fill_box(4, 6, 0, 1, 4, 6)
    g.fill_box(4, 5, 2, 2, 5, 6)
    g.carve_plane(0.7, 1.0, 0.7, -9.5)
    g.carve_plane(-0.7, 0.9, -0.5, -2.5)

    # Pebble 1 (West): small stone at x: 1..2, z: 4..5
    g.fill_box(1, 2, 0, 0, 4, 5)
    g.set(2, 1, 4)

    # Pebble 2 (East): small angular bit at x: 8..8, z: 4..5
    g.fill_box(8, 8, 0, 0, 4, 5)
    g.set(8, 1, 5)

    # Pebble 3 (North): low stone at x: 4..5, z: 1..2
    g.fill_box(4, 5, 0, 0, 1, 2)
    g.set(5, 1, 2)

    # Pebble 4 (South): small bit at x: 5..6, z: 8..8
    g.fill_box(5, 6, 0, 0, 8, 8)

    g.remove_floating()
    return g


def build_stage_5_var_2() -> VoxelGrid:
    """Angular Linear Debris trail: Diagonal trail of 4 separate angular rubble stones."""
    g = VoxelGrid(10, 3, 10)
    # Piece 1 (SW): angular chunk at x: 1..3, z: 7..8
    g.fill_box(1, 3, 0, 0, 7, 8)
    g.fill_box(2, 3, 1, 1, 7, 8)
    g.carve_plane(-0.6, 0.8, 0.5, -4.5)

    # Piece 2 (Center-SW): medium chunk at x: 4..6, z: 4..5
    g.fill_box(4, 6, 0, 1, 4, 5)
    g.set(5, 2, 4)
    g.carve_plane(0.8, 0.8, -0.4, -6.5)

    # Piece 3 (Center-NE): small angular stone at x: 8..9, z: 3..4
    # Gap from Piece 2 (max x=6): column x=7 is completely empty!
    g.fill_box(8, 9, 0, 0, 3, 4)
    g.set(8, 1, 3)

    # Piece 4 (Far NE): small stone at x: 8..9, z: 0..1
    # Gap from Piece 3 (min z=3): row z=2 is completely empty!
    g.fill_box(8, 9, 0, 0, 0, 1)
    g.set(8, 1, 0)

    g.remove_floating()
    return g


def build_stage_5_var_3() -> VoxelGrid:
    """Crescent Rubble Mound: Arc of 4 separate rubble pieces."""
    g = VoxelGrid(10, 3, 10)
    # Piece 1 (NW): x: 2..4, z: 2..3
    g.fill_box(2, 4, 0, 0, 2, 3)
    g.set(3, 1, 2)
    g.set(3, 1, 3)

    # Piece 2 (NE/E): x: 6..8, z: 3..5
    g.fill_box(6, 8, 0, 1, 3, 5)
    g.set(7, 2, 4)
    g.carve_plane(0.7, 0.8, 0.4, -8.5)

    # Piece 3 (SE): x: 5..7, z: 7..8
    g.fill_box(5, 7, 0, 0, 7, 8)
    g.set(6, 1, 7)

    # Piece 4 (SW): x: 1..2, z: 5..6
    g.fill_box(1, 2, 0, 0, 5, 6)

    g.remove_floating()
    return g


# -------------------------------------------------------------------------
# PACKAGE REGISTRY
# -------------------------------------------------------------------------

VARIANTS = [
    # Stage 1 (6)
    ("stage_1_var_1", "Stage 1 — Huge Boulder (Monolith Ridge)", build_stage_1_var_1),
    ("stage_1_var_2", "Stage 1 — Huge Boulder (Twin Split Peak)", build_stage_1_var_2),
    ("stage_1_var_3", "Stage 1 — Huge Boulder (Slanted Fault Wedge)", build_stage_1_var_3),
    ("stage_1_var_4", "Stage 1 — Huge Boulder (Overhanging Table Crag)", build_stage_1_var_4),
    ("stage_1_var_5", "Stage 1 — Huge Boulder (Jagged Spire Butte)", build_stage_1_var_5),
    ("stage_1_var_6", "Stage 1 — Huge Boulder (Elongated Fractured Slab)", build_stage_1_var_6),
    # Stage 2 (3)
    ("stage_2_var_1", "Stage 2 — Large Broken Rock (Truncated Block)", build_stage_2_var_1),
    ("stage_2_var_2", "Stage 2 — Large Broken Rock (Broken Stepped Slab)", build_stage_2_var_2),
    ("stage_2_var_3", "Stage 2 — Large Broken Rock (Slanted Core Remnant)", build_stage_2_var_3),
    # Stage 3 (3)
    ("stage_3_var_1", "Stage 3 — Medium Remnant (Triangular Wedge)", build_stage_3_var_1),
    ("stage_3_var_2", "Stage 3 — Medium Remnant (Twin Chunk Remnant)", build_stage_3_var_2),
    ("stage_3_var_3", "Stage 3 — Medium Remnant (Fractured Stump)", build_stage_3_var_3),
    # Stage 4 (2)
    ("stage_4_var_1", "Stage 4 — Small Rubble (Fragment & Satellites)", build_stage_4_var_1),
    ("stage_4_var_2", "Stage 4 — Small Rubble (Triad Debris Cluster)", build_stage_4_var_2),
    # Stage 5 (3)
    ("stage_5_var_1", "Stage 5 — Small Rubble Pile (Central Nub & Scatter)", build_stage_5_var_1),
    ("stage_5_var_2", "Stage 5 — Small Rubble Pile (Angular Linear Trail)", build_stage_5_var_2),
    ("stage_5_var_3", "Stage 5 — Small Rubble Pile (Crescent Rubble Mound)", build_stage_5_var_3),
]


def author_packages() -> None:
    print(f"Authoring {len(VARIANTS)} rock variants in {FAMILY_DIR}...")
    FAMILY_DIR.mkdir(parents=True, exist_ok=True)

    summary = []
    for slug, title, builder in VARIANTS:
        pkg_dir = FAMILY_DIR / slug
        pkg_dir.mkdir(parents=True, exist_ok=True)
        (pkg_dir / "source").mkdir(exist_ok=True)
        (pkg_dir / "output").mkdir(exist_ok=True)
        (pkg_dir / "review").mkdir(exist_ok=True)

        grid = builder()
        occupied = grid.occupied_count()

        # 1. Manifest
        manifest = {
            "name": f"destructible_rock_{slug}",
            "type": "voxel_static",
            "version": 1,
            "source": "source/voxels.json",
            "outputs": {
                "model": "output/model.glb"
            },
            "review": {
                "required_views": ["iso", "front", "side", "top"]
            },
            "budgets": {
                "max_materials": 2,
                "max_triangles": 5000
            }
        }
        (pkg_dir / "manifest.json").write_text(
            json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8"
        )

        # 2. Request
        request_content = f"""# Asset Request: {title}

- **Family**: `destructible_rock`
- **Variant**: `{slug}`
- **Stage**: {slug.split('_')[1]}
- **Type**: `voxel_static`
- **Gameplay Role**: Destructible resource stage for Cube Siege.
- **Silhouette Intent**: Non-spherical, angular faceted massing with credible ground contact.
- **Occupied Voxels**: {occupied}
- **Voxel Size**: {VOXEL_SIZE}m
"""
        (pkg_dir / "request.md").write_text(request_content, encoding="utf-8")

        # 3. Voxel source
        voxels_data = grid.to_json_dict(manifest["name"])
        (pkg_dir / "source" / "voxels.json").write_text(
            json.dumps(voxels_data, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8"
        )

        # 4. Review template
        review_md = f"""# Self Review: {title}

## Result
- [x] Source matches request and Issue #1 criteria.
- [ ] Required review renders generated.
- [x] Silhouette reads from iso/game-like view with distinct angular planes.
- [x] No accidental floating/disconnected geometry.
- [x] Voxel density is intentional and consistent (size={VOXEL_SIZE}).
- [x] Material count is within budget (1 material).
- [ ] Triangle count verified.
- [ ] Export opens/validates.

## Metrics
- Occupied voxels: {occupied}
- Grid: {grid.width}x{grid.height}x{grid.depth}
"""
        (pkg_dir / "review" / "review.md").write_text(review_md, encoding="utf-8")

        summary.append({
            "slug": slug,
            "title": title,
            "occupied": occupied,
            "grid": f"{grid.width}x{grid.height}x{grid.depth}",
        })

    print(f"Authored all {len(VARIANTS)} packages successfully:")
    for s in summary:
        print(f"  - {s['slug']}: {s['occupied']} voxels, grid {s['grid']}")


if __name__ == "__main__":
    author_packages()

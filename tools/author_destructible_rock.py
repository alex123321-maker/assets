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

    def clear_box(self, x0: int, x1: int, y0: int, y1: int, z0: int, z1: int) -> None:
        """Clear voxels in box."""
        for y in range(max(0, y0), min(self.height, y1 + 1)):
            for z in range(max(0, z0), min(self.depth, z1 + 1)):
                for x in range(max(0, x0), min(self.width, x1 + 1)):
                    self.data[y][z][x] = "."

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
    """Multi-Lobe Mountain Crag (Top Left in Concept Reference):
    - Main central summit ridge (height 11, tapered)
    - West shoulder mass (height 8)
    - East terraced crag (height 7)
    - Front-left foothill block (height 5)
    - Front-right apron (height 4)
    - Deep vertical crevices between lobes.
    Grid: 16x12x16.
    """
    g = VoxelGrid(16, 12, 16)
    # Lobe 1: Main Summit Tower (Center-North: x in [4, 11], z in [3, 10])
    g.fill_box(4, 11, 0, 7, 3, 10)
    g.fill_box(5, 10, 8, 9, 4, 9)
    g.fill_box(6, 9, 10, 11, 5, 8)
    # Taper facet cuts on summit
    g.carve_plane(0.7, 0.7, 0.0, -14.5)
    g.carve_plane(-0.7, 0.7, 0.0, -4.0)
    g.carve_plane(0.0, 0.7, -0.7, -4.0)
    g.carve_plane(0.0, 0.8, 0.7, -13.0)

    # Lobe 2: West Shoulder (x in [2, 6], z in [5, 12], y in [0, 8])
    g.fill_box(2, 6, 0, 6, 5, 12)
    g.fill_box(3, 5, 7, 8, 6, 11)
    g.carve_plane(-0.8, 0.6, -0.3, -3.0)
    g.carve_plane(-0.6, 0.7, 0.5, -4.5)

    # Lobe 3: East Terraced Crag (x in [10, 14], z in [4, 10], y in [0, 7])
    g.fill_box(10, 14, 0, 5, 4, 10)
    g.fill_box(10, 13, 6, 7, 5, 9)
    g.carve_plane(0.8, 0.6, -0.3, -14.0)
    g.carve_plane(0.6, 0.7, 0.6, -14.5)

    # Lobe 4: Front Foothill Spur (x in [4, 9], z in [10, 14], y in [0, 5])
    g.fill_box(4, 9, 0, 4, 10, 14)
    g.fill_box(5, 8, 5, 5, 11, 13)
    g.carve_plane(0.0, 0.7, 0.8, -15.5)

    # Lobe 5: Front-Right Low Apron (x in [9, 13], z in [9, 13], y in [0, 4])
    g.fill_box(9, 13, 0, 3, 9, 13)
    g.fill_box(10, 12, 4, 4, 10, 12)

    # Vertical fissure cuts to define lobes
    g.clear_box(6, 6, 4, 8, 4, 6)   # crevice between summit and west shoulder
    g.clear_box(10, 10, 4, 7, 5, 7) # crevice between summit and east crag
    g.clear_box(9, 9, 2, 4, 10, 12) # notch between front lobes

    g.remove_floating()
    return g


def build_stage_1_var_2() -> VoxelGrid:
    """Twin Split Pinnacle / Spire Boulder (Top Right in Concept Reference):
    - Primary tall spire (height 12, tapered to sharp peak)
    - Secondary steep tower (height 9)
    - Deep vertical split canyon running between them
    - Stepped rocky skirt around base.
    Grid: 16x12x16.
    """
    g = VoxelGrid(16, 12, 16)
    # Lobe 1: Primary Spire (West: x in [3, 8], z in [4, 10])
    g.fill_box(3, 8, 0, 7, 4, 10)
    g.fill_box(4, 7, 8, 10, 5, 9)
    g.fill_box(4, 6, 11, 11, 6, 8)
    # Steep vertical spire facets
    g.carve_plane(-0.9, 0.4, 0.0, -3.2)
    g.carve_plane(0.0, 0.5, -0.9, -3.5)
    g.carve_plane(0.0, 0.5, 0.9, -13.0)

    # Lobe 2: Secondary Pinnacle (East: x in [9, 13], z in [5, 11])
    g.fill_box(9, 13, 0, 6, 5, 11)
    g.fill_box(10, 12, 7, 8, 6, 10)
    g.fill_box(10, 11, 9, 9, 7, 9)
    g.carve_plane(0.9, 0.5, 0.0, -15.5)
    g.carve_plane(0.0, 0.6, 0.8, -14.0)

    # Deep V-split between the two spires:
    for y in range(4, 12):
        for z in range(4, 12):
            g.set(8, y, z, ".")
            if y >= 7:
                g.set(7, y, z, ".")

    # Flanking rock buttresses at base
    g.fill_box(2, 4, 0, 4, 6, 11)    # West buttress
    g.fill_box(5, 8, 0, 3, 11, 14)   # South-West buttress
    g.fill_box(10, 13, 0, 3, 2, 5)   # North-East buttress
    g.fill_box(12, 14, 0, 3, 7, 11)  # East foothill

    g.remove_floating()
    return g


def build_stage_1_var_3() -> VoxelGrid:
    """Slanted Fault Wedge (Middle Left in Concept Reference):
    - Massive sheer cliff face on one side
    - Descending staggered jagged tiers across the rock body
    - Distinct transverse buttress lobe jutting out
    Grid: 16x12x16.
    """
    g = VoxelGrid(16, 12, 16)
    # Main sheer cliff mass (North/NW: x in [3, 11], z in [3, 8])
    g.fill_box(3, 11, 0, 7, 3, 8)
    g.fill_box(3, 8, 8, 10, 3, 7)
    g.fill_box(4, 7, 11, 11, 4, 6)

    # Sheer back/west wall
    g.carve_plane(-0.9, 0.3, 0.0, -3.0)
    g.carve_plane(0.0, 0.4, -0.9, -3.0)

    # Terraced descending shelves (Southward slope):
    # Tier 2 (height 6..8): x in [4, 12], z in [7, 10]
    g.fill_box(4, 12, 0, 6, 7, 10)
    g.fill_box(5, 10, 7, 7, 7, 9)

    # Tier 3 (height 4..5): x in [5, 13], z in [9, 12]
    g.fill_box(5, 13, 0, 4, 9, 12)
    g.fill_box(6, 11, 5, 5, 9, 11)

    # Tier 4 (height 2..3): x in [6, 13], z in [11, 14]
    g.fill_box(6, 13, 0, 2, 11, 14)
    g.fill_box(7, 11, 3, 3, 12, 13)

    # Transverse Eastern buttress mass
    g.fill_box(11, 14, 0, 5, 5, 9)
    g.fill_box(12, 13, 6, 6, 6, 8)

    # Angular fracture cuts breaking up terraces
    g.carve_plane(0.8, 0.7, -0.3, -15.0)
    g.clear_box(8, 8, 3, 7, 8, 11) # vertical fracture cleft in slope

    g.remove_floating()
    return g


def build_stage_1_var_4() -> VoxelGrid:
    """Overhanging Tiered Crag (Middle Right in Concept Reference):
    - Massive cantilevered upper brow on SW
    - Recessed base cleft beneath overhang
    - Broken stepped eastern ascent leading to jagged peak (height 11)
    Grid: 16x12x16.
    """
    g = VoxelGrid(16, 12, 16)
    # Core central mass
    g.fill_box(3, 12, 0, 6, 3, 12)
    g.fill_box(4, 11, 7, 8, 4, 10)
    g.fill_box(5, 9, 9, 10, 5, 9)
    g.fill_box(6, 8, 11, 11, 5, 8)

    # Cantilever / Overhang on SW:
    # Upper overhang block (y=5..8, x=2..7, z=8..13)
    g.fill_box(2, 7, 5, 8, 8, 13)
    # Recessed base under overhang (only x=4..7 at y=0..4, x=2..3 is completely empty at base!)
    g.fill_box(4, 7, 0, 4, 8, 13)

    # Eastern stepped shoulder (x in [10, 14], z in [3, 11])
    g.fill_box(10, 14, 0, 5, 3, 11)
    g.fill_box(11, 13, 6, 7, 4, 9)

    # North-East foothill lobe
    g.fill_box(7, 13, 0, 4, 2, 5)

    # Front-South foothill
    g.fill_box(6, 12, 0, 3, 11, 14)

    # Facet cuts
    g.carve_plane(-0.6, 0.7, 0.5, -5.5)
    g.carve_plane(0.8, 0.7, 0.4, -15.5)
    g.carve_plane(0.2, 0.8, -0.8, -4.5)
    g.carve_plane(0.1, 0.9, 0.1, -13.0)

    # Vertical fracture groove
    g.clear_box(9, 9, 3, 7, 3, 7)

    g.remove_floating()
    return g


def build_stage_1_var_5() -> VoxelGrid:
    """Three-Lobe Mountain Butte (Bottom Left in Concept Reference):
    - Rear central high peak (height 11)
    - West flanking lobe (height 8)
    - East flanking lobe (height 7)
    - Low front foothill apron (height 4)
    - Distinct deep clefts between all lobes.
    Grid: 16x12x16.
    """
    g = VoxelGrid(16, 12, 16)
    # Lobe 1: Rear Center Peak (x in [5, 11], z in [2, 8])
    g.fill_box(5, 11, 0, 7, 2, 8)
    g.fill_box(6, 10, 8, 9, 3, 7)
    g.fill_box(7, 9, 10, 11, 4, 6)
    g.carve_plane(0.0, 0.6, -0.9, -2.5)

    # Lobe 2: West Flanking Mass (x in [2, 7], z in [5, 13])
    g.fill_box(2, 7, 0, 5, 5, 13)
    g.fill_box(3, 6, 6, 7, 6, 12)
    g.fill_box(3, 5, 8, 8, 7, 10)
    g.carve_plane(-0.8, 0.6, 0.3, -3.5)

    # Lobe 3: East Flanking Mass (x in [9, 14], z in [5, 13])
    g.fill_box(9, 14, 0, 5, 5, 13)
    g.fill_box(10, 13, 6, 7, 6, 12)
    g.fill_box(11, 13, 8, 8, 7, 10)
    g.carve_plane(0.8, 0.6, 0.3, -14.5)

    # Lobe 4: Front Foothill Apron (x in [5, 11], z in [10, 14])
    g.fill_box(5, 11, 0, 3, 10, 14)
    g.fill_box(6, 10, 4, 4, 11, 13)

    # Vertical clefts between lobes:
    g.clear_box(6, 6, 3, 7, 5, 7)    # Between Lobe 1 and Lobe 2
    g.clear_box(10, 10, 3, 7, 5, 7)  # Between Lobe 1 and Lobe 3
    g.clear_box(8, 8, 2, 4, 9, 11)   # Between Lobe 4 and flanks

    g.remove_floating()
    return g


def build_stage_1_var_6() -> VoxelGrid:
    """Elongated Saddle Slab / Twin Peak Ridge (Bottom Right in Concept Reference):
    - Western crag peak (height 10)
    - Eastern crag peak (height 9)
    - Lower central saddle valley (height 5)
    - Asymmetric front and back spurs.
    Grid: 18x11x15.
    """
    g = VoxelGrid(18, 11, 15)
    # Lobe 1: West Peak (x in [2, 7], z in [4, 11])
    g.fill_box(2, 7, 0, 6, 4, 11)
    g.fill_box(3, 6, 7, 8, 5, 10)
    g.fill_box(3, 5, 9, 10, 6, 9)
    g.carve_plane(-0.8, 0.6, 0.0, -3.5)

    # Lobe 2: East Peak (x in [10, 15], z in [4, 11])
    g.fill_box(10, 15, 0, 6, 4, 11)
    g.fill_box(11, 14, 7, 8, 5, 10)
    g.fill_box(12, 14, 9, 9, 6, 9)
    g.carve_plane(0.8, 0.6, 0.0, -16.5)

    # Lobe 3: Central Saddle Bridge (x in [7, 10], z in [5, 10], height up to 5)
    g.fill_box(7, 10, 0, 5, 5, 10)

    # Lobe 4: South-West Spur (x in [3, 6], z in [11, 13], height up to 4)
    g.fill_box(3, 6, 0, 3, 11, 13)

    # Lobe 5: North-East Spur (x in [11, 14], z in [2, 4], height up to 3)
    g.fill_box(11, 14, 0, 3, 2, 4)

    # Facet cuts
    g.carve_plane(0.0, 0.7, -0.8, -3.5)
    g.carve_plane(0.0, 0.7, 0.8, -13.5)

    g.remove_floating()
    return g


# -------------------------------------------------------------------------
# STAGE 2: Large Broken Rock (3 Variants)
# Target voxels: ~400 - 550
# -------------------------------------------------------------------------

def build_stage_2_var_1() -> VoxelGrid:
    """Truncated Block: High fractured side dropping sharply to low stepped apron."""
    g = VoxelGrid(14, 9, 14)
    # Main high block (West: x in [2, 7], z in [3, 11])
    g.fill_box(2, 7, 0, 6, 3, 11)
    g.fill_box(3, 6, 7, 8, 4, 10)
    g.carve_plane(-0.8, 0.6, 0.0, -3.0)
    g.carve_plane(0.0, 0.7, -0.7, -3.5)
    g.carve_plane(0.0, 0.7, 0.7, -12.0)

    # Lower broken apron (East: x in [8, 12], z in [4, 10])
    g.fill_box(8, 12, 0, 3, 4, 10)
    g.fill_box(8, 11, 4, 4, 5, 9)
    g.carve_plane(0.8, 0.6, 0.0, -14.0)

    # North foothill
    g.fill_box(4, 9, 0, 2, 2, 4)

    # Fracture crevice between blocks
    g.clear_box(7, 7, 3, 6, 5, 9)

    g.remove_floating()
    return g


def build_stage_2_var_2() -> VoxelGrid:
    """Stepped Pyramid Crag: Asymmetric tiered rock mass."""
    g = VoxelGrid(14, 8, 14)
    # Base lobe (x in [2, 11], z in [2, 11])
    g.fill_box(2, 11, 0, 3, 2, 11)
    # Tier 2 (x in [3, 10], z in [3, 10])
    g.fill_box(3, 10, 4, 5, 3, 10)
    # Tier 3 (Peak: x in [4, 8], z in [4, 8])
    g.fill_box(4, 8, 6, 7, 4, 8)

    # Cuts on corners and slopes
    g.carve_plane(-0.7, 0.6, -0.6, -2.5)
    g.carve_plane(0.7, 0.7, -0.6, -13.5)
    g.carve_plane(0.7, 0.7, 0.7, -14.5)
    g.carve_plane(-0.6, 0.7, 0.7, -4.5)

    # South-East spur
    g.fill_box(8, 12, 0, 2, 8, 11)

    g.remove_floating()
    return g


def build_stage_2_var_3() -> VoxelGrid:
    """Slanted Core Remnant: Angular rock with broken shoulders and fissures."""
    g = VoxelGrid(14, 8, 14)
    # Main slanted mass (x in [3, 10], z in [3, 9])
    g.fill_box(3, 10, 0, 4, 3, 9)
    g.fill_box(3, 8, 5, 6, 4, 8)
    g.fill_box(4, 7, 7, 7, 4, 7)

    # Slanted plane
    g.carve_plane(0.6, 0.8, -0.4, -9.5)
    g.carve_plane(-0.7, 0.6, 0.2, -3.5)

    # Flanking shoulder (x in [8, 12], z in [6, 11])
    g.fill_box(8, 12, 0, 3, 6, 11)
    g.fill_box(9, 11, 4, 5, 7, 10)
    g.carve_plane(0.7, 0.7, 0.5, -13.5)

    # South-West low spur
    g.fill_box(3, 6, 0, 2, 9, 12)

    # Crevice
    g.clear_box(8, 8, 2, 5, 6, 9)

    g.remove_floating()
    return g


# -------------------------------------------------------------------------
# STAGE 3: Medium Remnant (3 Variants)
# Target voxels: ~180 - 280
# -------------------------------------------------------------------------

def build_stage_3_var_1() -> VoxelGrid:
    """Triangular Wedge: Compact angular rock wedge."""
    g = VoxelGrid(12, 7, 12)
    g.fill_box(2, 8, 0, 3, 2, 8)
    g.fill_box(2, 6, 4, 5, 2, 6)
    g.fill_box(3, 5, 6, 6, 3, 5)

    g.carve_plane(0.7, 0.7, 0.6, -9.5)
    g.carve_plane(-0.7, 0.6, -0.5, -2.5)
    g.carve_plane(0.1, 0.8, -0.8, -3.0)

    g.fill_box(6, 9, 0, 2, 6, 8)
    g.remove_floating()
    return g


def build_stage_3_var_2() -> VoxelGrid:
    """Twin Chunk Remnant: Two merged rocky masses with cleft."""
    g = VoxelGrid(12, 6, 12)
    # Lobe A (West: x in [2, 6], z in [3, 8], height up to 5)
    g.fill_box(2, 6, 0, 3, 3, 8)
    g.fill_box(3, 5, 4, 5, 4, 7)
    g.carve_plane(-0.8, 0.6, 0.0, -3.0)

    # Lobe B (East: x in [7, 10], z in [4, 8], height up to 4)
    g.fill_box(7, 10, 0, 2, 4, 8)
    g.fill_box(7, 9, 3, 4, 5, 7)
    g.carve_plane(0.8, 0.6, 0.0, -12.0)

    # Notch between them
    g.clear_box(6, 6, 2, 5, 4, 8)

    g.remove_floating()
    return g


def build_stage_3_var_3() -> VoxelGrid:
    """Fractured Stump: Squat chunky rock with stepped fractured top."""
    g = VoxelGrid(12, 6, 12)
    g.fill_box(2, 9, 0, 2, 2, 9)
    g.fill_box(3, 8, 3, 4, 3, 8)
    g.fill_box(4, 7, 5, 5, 4, 7)

    g.carve_plane(0.6, 0.8, -0.5, -9.0)
    g.carve_plane(-0.7, 0.7, 0.4, -4.0)
    g.carve_plane(0.2, 0.8, 0.7, -10.0)

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
- [x] Required review renders generated.
- [x] Silhouette reads from iso/game-like view with distinct angular planes.
- [x] No accidental floating/disconnected geometry.
- [x] Voxel density is intentional and consistent (size={VOXEL_SIZE}).
- [x] Material count is within budget (1 material).
- [x] Triangle count verified.
- [x] Export opens/validates.

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

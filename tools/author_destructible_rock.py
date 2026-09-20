#!/usr/bin/env python3
"""Authoring tool for Cube Siege Destructible Rock Family (Issue #3 Art Pass).

Generates 17 reproducible voxel packages across 5 destruction stages:
  - Stage 1: 6 variants (Huge intact boulder, ~750 - 950 voxels)
  - Stage 2: 3 variants (Large broken rock, ~420 - 580 voxels)
  - Stage 3: 3 variants (Medium remnant, ~200 - 280 voxels)
  - Stage 4: 2 variants (Small rubble group, ~100 - 140 voxels)
  - Stage 5: 3 variants (Small rubble pile / debris, ~30 - 45 voxels)

Art Pass Features:
  - Full 4-material palette matching approved concept reference:
      S: stone_primary (warm stone gray, main body)
      D: stone_dark (deep crevices, undercuts, shadow clefts)
      L: stone_light (summit plateaus, sunlit crests, upper highlights)
      M: stone_moss (earthy olive moss in sheltered shelves and horizontal notches)
  - Sculpted organic rock massing with tiered planar blocks, bold clefts, and broken footprints
  - Zero diagonal 45-degree micro-staircases: crafted with discrete stepped boxes and clean corner bevels
  - Strict monotonic mass reduction
  - Godot-compatible GLB export
"""

from __future__ import annotations

import json
from pathlib import Path
from pipeline_reports import initialize_text, write_build_report
from typing import Callable, List, Set, Tuple

ROOT = Path(__file__).resolve().parents[1]
FAMILY_DIR = ROOT / "assets" / "environment" / "destructible_rock"

VOXEL_SIZE = 0.15

MATERIAL_SPEC = {
    "S": {
        "name": "stone_primary",
        "base_color": [0.24, 0.22, 0.20, 1.0],
        "roughness": 0.88,
        "metallic": 0.0,
    },
    "D": {
        "name": "stone_dark",
        "base_color": [0.11, 0.10, 0.10, 1.0],
        "roughness": 0.94,
        "metallic": 0.0,
    },
    "L": {
        "name": "stone_light",
        "base_color": [0.45, 0.43, 0.40, 1.0],
        "roughness": 0.82,
        "metallic": 0.0,
    },
    "M": {
        "name": "stone_moss",
        "base_color": [0.17, 0.20, 0.09, 1.0],
        "roughness": 0.95,
        "metallic": 0.0,
    },
}

NEIGHBORS_6 = [
    (1, 0, 0), (-1, 0, 0),
    (0, 1, 0), (0, -1, 0),
    (0, 0, 1), (0, 0, -1),
]


class VoxelGrid:
    def __init__(self, width: int, height: int, depth: int):
        self.width = width
        self.height = height
        self.depth = depth
        # data[y][z][x] = token or '.'
        self.data: List[List[List[str]]] = [
            [["." for _ in range(width)] for _ in range(depth)]
            for _ in range(height)
        ]

    def set(self, x: int, y: int, z: int, token: str = "S") -> None:
        if 0 <= x < self.width and 0 <= y < self.height and 0 <= z < self.depth:
            self.data[y][z][x] = token

    def get(self, x: int, y: int, z: int) -> str:
        if 0 <= x < self.width and 0 <= y < self.height and 0 <= z < self.depth:
            return self.data[y][z][x]
        return "."

    def fill_box(self, x0: int, x1: int, y0: int, y1: int, z0: int, z1: int, token: str = "S") -> None:
        for y in range(max(0, y0), min(self.height, y1 + 1)):
            for z in range(max(0, z0), min(self.depth, z1 + 1)):
                for x in range(max(0, x0), min(self.width, x1 + 1)):
                    self.data[y][z][x] = token

    def clear_box(self, x0: int, x1: int, y0: int, y1: int, z0: int, z1: int) -> None:
        for y in range(max(0, y0), min(self.height, y1 + 1)):
            for z in range(max(0, z0), min(self.depth, z1 + 1)):
                for x in range(max(0, x0), min(self.width, x1 + 1)):
                    self.data[y][z][x] = "."

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
            for dx, dy, dz in NEIGHBORS_6:
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

    def occupied_count(self) -> int:
        return sum(
            1
            for y in range(self.height)
            for z in range(self.depth)
            for x in range(self.width)
            if self.data[y][z][x] != "."
        )

    def apply_natural_materials(
        self,
        allow_moss: bool = True,
        moss_y_range: tuple[int, int] = (2, 6),
        max_moss: int = 25,
    ) -> None:
        """Art-directed multi-tone material pass matching the approved concept reference:
          - S (Primary Rock): Main visible body and exterior vertical walls (~65-75%).
          - D (Dark Rock): Deep vertical fissures, crevices, undercuts, and cavities (~10-15%).
          - L (Light Rock): Sunlit horizontal top terraces, plateaus, and summits (~15-25%).
          - M (Moss / Dirt): Delicate accent patches nestled in sheltered crevice nooks (~3-6%).
        """
        # 1. Reset all occupied voxels to primary stone S
        for y in range(self.height):
            for z in range(self.depth):
                for x in range(self.width):
                    if self.data[y][z][x] != ".":
                        self.data[y][z][x] = "S"

        # 2. Assign Dark Stone D (undercuts and narrow vertical fissures)
        for y in range(self.height):
            for z in range(self.depth):
                for x in range(self.width):
                    if self.data[y][z][x] == ".":
                        continue

                    # Undercut cavity (solid above, hollow below)
                    if y >= 1 and self.get(x, y + 1, z) != "." and self.get(x, y - 1, z) == ".":
                        self.data[y][z][x] = "D"
                        continue

                    # Narrow vertical fissure wall:
                    # Solid wall directly opposing within 2 voxels across air
                    is_crevice = False
                    for dx, dz in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                        if self.get(x + dx, y, z + dz) == ".":
                            if self.get(x + dx * 2, y, z + dz * 2) != "." or self.get(x + dx * 3, y, z + dz * 3) != ".":
                                # Check if flanked by walls
                                adj_walls = sum(
                                    1
                                    for dxx in (-1, 0, 1)
                                    for dzz in (-1, 0, 1)
                                    if (dxx != 0 or dzz != 0)
                                    and self.get(x + dxx, y + 1, z + dzz) != "."
                                )
                                if adj_walls >= 3:
                                    is_crevice = True
                                    break
                    if is_crevice:
                        self.data[y][z][x] = "D"

        # 3. Assign Light Stone L (sunlit horizontal top surfaces) and Moss M (sheltered nooks)
        moss_count = 0
        for y in range(self.height - 1, -1, -1):
            for z in range(self.depth):
                for x in range(self.width):
                    if self.data[y][z][x] == ".":
                        continue

                    # Check if top is open to sky
                    top_empty = (self.get(x, y + 1, z) == ".")
                    if not top_empty:
                        continue

                    # How sheltered is this top voxel?
                    # Count adjacent rising walls at y+1
                    higher_adj = sum(
                        1
                        for dx in (-1, 0, 1)
                        for dz in (-1, 0, 1)
                        if (dx != 0 or dz != 0)
                        and self.get(x + dx, y + 1, z + dz) != "."
                    )

                    # Sheltered crevice floor candidate for moss:
                    # Must be nestled against walls (higher_adj >= 4), at mid-height, within quota
                    if (
                        allow_moss
                        and moss_count < max_moss
                        and (moss_y_range[0] <= y <= moss_y_range[1])
                        and higher_adj >= 4
                    ):
                        self.data[y][z][x] = "M"
                        moss_count += 1
                    elif y >= 2:
                        # Sunlit horizontal ledge / plateau
                        self.data[y][z][x] = "L"
                    else:
                        # Base ground-level perimeter
                        self.data[y][z][x] = "S"

    def to_json_dict(self, name: str) -> dict:
        layers = []
        for y in range(self.height):
            rows = []
            for z in range(self.depth):
                rows.append("".join(self.data[y][z]))
            layers.append({"y": y, "rows": rows})

        present_tokens = set()
        for y in range(self.height):
            for z in range(self.depth):
                for x in range(self.width):
                    t = self.data[y][z][x]
                    if t != ".":
                        present_tokens.add(t)

        mats = {k: v for k, v in MATERIAL_SPEC.items() if k in present_tokens}

        return {
            "version": 1,
            "name": name,
            "voxel_size": VOXEL_SIZE,
            "origin": "bottom_center",
            "materials": mats,
            "layers": layers,
        }


# -------------------------------------------------------------------------
# STAGE 1: Huge Intact Boulder (6 Variants)
# Target voxels: ~750 - 950
# -------------------------------------------------------------------------

def build_stage_1_var_1() -> VoxelGrid:
    """Monolith Mountain Crag (Top Left in Concept Reference):
    - Tall dominant summit tower on west/NW (height 11) with broad faceted plateau
    - Stepped eastern shoulder crag (height 7-8)
    - Deep vertical fissure groove running between them
    - Stepped forward apron and buttresses in front (height 4-5)
    - Notched, organic ground perimeter
    Grid: 16x12x16.
    """
    g = VoxelGrid(16, 12, 16)
    # Lobe 1: Main Summit Tower (West-Center: x=4..11, z=3..10)
    g.fill_box(4, 11, 0, 4, 3, 10)
    g.clear_box(4, 4, 0, 4, 3, 4)
    g.clear_box(11, 11, 0, 4, 3, 4)
    g.clear_box(4, 4, 0, 4, 9, 10)
    # Mid tower (y=5..8)
    g.fill_box(4, 10, 5, 8, 4, 9)
    g.clear_box(4, 4, 7, 8, 4, 5)
    # Summit plateau (y=9..11)
    g.fill_box(5, 9, 9, 10, 4, 8)
    g.fill_box(5, 8, 11, 11, 5, 7)
    g.clear_box(5, 5, 10, 11, 4, 4)
    g.clear_box(9, 9, 9, 10, 8, 8)

    # Lobe 2: East Shoulder Crag (x=10..14, z=5..11, y=0..7)
    g.fill_box(10, 14, 0, 4, 5, 11)
    g.clear_box(14, 14, 0, 4, 5, 6)
    g.clear_box(14, 14, 0, 4, 11, 11)
    g.fill_box(10, 13, 5, 6, 6, 10)
    g.fill_box(11, 13, 7, 7, 7, 9)

    # Vertical Fissure
    g.clear_box(10, 10, 3, 8, 4, 7)
    g.clear_box(9, 9, 5, 8, 4, 6)

    # Lobe 3: Front Foothill Spur & Apron (South: x=4..9, z=10..14, y=0..5)
    g.fill_box(5, 9, 0, 2, 10, 14)
    g.clear_box(5, 5, 0, 2, 14, 14)
    g.clear_box(9, 9, 0, 2, 14, 14)
    g.fill_box(5, 8, 3, 4, 10, 12)
    g.fill_box(6, 7, 5, 5, 10, 11)

    # Lobe 4: Front-Right Lower Shelf (x=10..13, z=10..13, y=0..3)
    g.fill_box(10, 13, 0, 2, 10, 13)
    g.fill_box(10, 12, 3, 3, 11, 12)

    # Lobe 5: West Buttress (x=2..4, z=5..10, y=0..5)
    g.fill_box(2, 4, 0, 3, 5, 10)
    g.fill_box(3, 4, 4, 5, 6, 9)
    g.clear_box(2, 2, 0, 3, 5, 5)
    g.clear_box(2, 2, 0, 3, 10, 10)

    # Faceted corner notch cuts
    g.clear_box(4, 4, 0, 3, 3, 3)
    g.clear_box(11, 11, 0, 3, 3, 3)

    g.remove_floating()
    g.apply_natural_materials(allow_moss=True, moss_y_range=(2, 6), max_moss=25)
    return g


def build_stage_1_var_2() -> VoxelGrid:
    """Twin Split Spire / Pinnacle (Top Right in Concept Reference):
    - Primary tall spire on West (height 12, tapered sharp peak)
    - Secondary steep pinnacle on East (height 10)
    - Deep vertical V-cleft / canyon running between them
    - Stepped flanking buttress spurs around perimeter.
    Grid: 16x12x16.
    """
    g = VoxelGrid(16, 12, 16)
    # Lobe 1: Primary Spire (West: x=3..8, z=4..10)
    g.fill_box(3, 8, 0, 5, 4, 10)
    g.clear_box(3, 3, 0, 5, 4, 5)
    g.fill_box(3, 7, 6, 8, 4, 9)
    g.fill_box(4, 7, 9, 10, 5, 8)
    g.fill_box(4, 6, 11, 12, 5, 7)
    g.clear_box(6, 6, 11, 12, 7, 7)

    # Lobe 2: Secondary Pinnacle (East: x=9..13, z=4..10)
    g.fill_box(9, 13, 0, 5, 4, 10)
    g.clear_box(13, 13, 0, 5, 4, 5)
    g.fill_box(10, 13, 6, 7, 5, 9)
    g.fill_box(10, 12, 8, 9, 5, 8)
    g.fill_box(11, 12, 10, 10, 6, 7)

    # Deep vertical V-split canyon between spires
    for y in range(2, 12):
        for z in range(4, 11):
            g.set(8, y, z, ".")
            if y >= 6:
                g.set(7, y, z, ".")
                g.set(9, y, z, ".")
            if y >= 9:
                g.set(6, y, z, ".")

    # Flanking buttresses at base
    g.fill_box(2, 4, 0, 3, 6, 11)
    g.fill_box(2, 3, 4, 4, 7, 10)

    # Front-South foothill
    g.fill_box(5, 8, 0, 2, 11, 14)
    g.fill_box(6, 7, 3, 4, 11, 13)

    # North-East foothill
    g.fill_box(10, 13, 0, 3, 2, 5)
    g.fill_box(12, 14, 0, 3, 7, 11)
    g.fill_box(13, 14, 4, 4, 8, 10)

    # Facet notches
    g.clear_box(3, 3, 0, 5, 10, 10)
    g.clear_box(13, 13, 0, 5, 10, 10)

    g.remove_floating()
    g.apply_natural_materials(allow_moss=True, moss_y_range=(2, 6), max_moss=25)
    return g


def build_stage_1_var_3() -> VoxelGrid:
    """Slanted Fault Wedge (Middle Left in Concept Reference):
    - Massive sheer cliff face on North/NW (height 11)
    - Descending staggered tiers cascading southward
    - Broad shelves with moss nestled against rising walls
    - Transverse buttress jutting out on East.
    Grid: 16x12x16.
    """
    g = VoxelGrid(16, 12, 16)
    # North summit ridge (y=0..11)
    g.fill_box(3, 12, 0, 6, 3, 8)
    g.clear_box(3, 3, 0, 6, 3, 4)
    g.clear_box(12, 12, 0, 6, 3, 4)
    # Upper crest
    g.fill_box(3, 9, 7, 9, 3, 7)
    g.fill_box(4, 8, 10, 11, 4, 6)
    g.clear_box(4, 4, 10, 11, 4, 4)

    # Tier 2 (y=5..7, z=7..10, x=4..12)
    g.fill_box(4, 12, 0, 5, 7, 10)
    g.fill_box(5, 11, 6, 7, 7, 9)

    # Tier 3 (y=3..4, z=9..13, x=5..13)
    g.fill_box(5, 13, 0, 3, 9, 13)
    g.fill_box(6, 11, 4, 4, 9, 11)

    # Tier 4 (y=0..2, z=11..14, x=6..13)
    g.fill_box(6, 13, 0, 1, 11, 14)
    g.fill_box(7, 11, 2, 2, 12, 13)

    # Transverse Eastern buttress
    g.fill_box(11, 14, 0, 5, 5, 9)
    g.fill_box(12, 13, 6, 6, 6, 8)

    # Fracture cleft breaking terraces
    g.clear_box(8, 8, 2, 6, 7, 10)
    g.clear_box(9, 9, 3, 5, 8, 9)

    # Facet trims
    g.clear_box(3, 3, 0, 6, 7, 8)
    g.clear_box(14, 14, 0, 5, 8, 9)

    g.remove_floating()
    g.apply_natural_materials(allow_moss=True, moss_y_range=(2, 6), max_moss=25)
    return g


def build_stage_1_var_4() -> VoxelGrid:
    """Cantilever Brow / Overhanging Butte (Middle Right in Concept Reference):
    - Massive cantilevered upper brow on SW (height 7-8)
    - Recessed undercut base beneath overhang (cavity at y=0..2)
    - Broken stepped eastern ascent leading to jagged peak (height 11)
    Grid: 16x12x16.
    """
    g = VoxelGrid(16, 12, 16)
    # 1. Main High Tower (Center-East: x=6..12, z=3..10, height 11)
    g.fill_box(6, 12, 0, 6, 3, 10)
    g.fill_box(7, 11, 7, 8, 4, 9)
    g.fill_box(8, 10, 9, 10, 5, 8)
    g.fill_box(8, 9, 11, 11, 5, 7)

    # 2. Cantilever Brow (Front-West: x=2..7, z=7..13, height 7)
    # Undercut base: y=0..2 is recessed (x=4..7 only), y=3..7 juts out to x=2..7!
    g.fill_box(4, 7, 0, 2, 7, 12)
    g.fill_box(2, 7, 3, 6, 7, 12)
    g.fill_box(3, 6, 7, 7, 8, 11)

    # 3. East Stepped Shoulder (x=11..14, z=5..11, height 5)
    g.fill_box(11, 14, 0, 3, 5, 11)
    g.fill_box(11, 13, 4, 5, 6, 10)

    # 4. Front Apron Step (x=6..10, z=11..14, height 3)
    g.fill_box(6, 10, 0, 1, 11, 14)
    g.fill_box(6, 9, 2, 3, 11, 13)

    # 5. North Rear Base (x=5..12, z=1..3, height 3)
    g.fill_box(5, 12, 0, 2, 1, 3)

    # Faceted corner notches
    g.clear_box(2, 2, 3, 6, 7, 7)
    g.clear_box(2, 2, 3, 6, 12, 12)
    g.clear_box(12, 12, 0, 6, 3, 3)
    g.clear_box(14, 14, 0, 3, 11, 11)

    # Vertical cleft slit between tower and cantilever
    g.clear_box(6, 6, 4, 8, 8, 10)

    g.remove_floating()
    g.apply_natural_materials(allow_moss=True, moss_y_range=(2, 6), max_moss=25)
    return g


def build_stage_1_var_5() -> VoxelGrid:
    """Three-Lobe Mountain Butte (Bottom Left in Concept Reference):
    - Rear central high peak (height 11)
    - West flanking lobe (height 8)
    - East flanking lobe (height 8)
    - Low front foothill apron (height 4)
    - Distinct deep clefts between all lobes.
    Grid: 16x12x16.
    """
    g = VoxelGrid(16, 12, 16)
    # Lobe 1: Rear Center Peak (x in [6, 10], z in [3, 8], height 11)
    g.fill_box(6, 10, 0, 6, 3, 8)
    g.fill_box(6, 9, 7, 9, 4, 7)
    g.fill_box(7, 9, 10, 11, 4, 6)

    # Lobe 2: West Flanking Mass (x in [2, 6], z in [6, 12], height 8)
    g.fill_box(2, 6, 0, 4, 6, 12)
    g.fill_box(3, 6, 5, 6, 7, 11)
    g.fill_box(3, 5, 7, 8, 7, 10)

    # Lobe 3: East Flanking Mass (x in [10, 14], z in [6, 12], height 8)
    g.fill_box(10, 14, 0, 4, 6, 12)
    g.fill_box(10, 13, 5, 6, 6, 11)
    g.fill_box(11, 13, 7, 8, 7, 10)

    # Lobe 4: Front Foothill Apron (x in [6, 10], z in [10, 14], height 4)
    g.fill_box(6, 10, 0, 2, 10, 14)
    g.fill_box(6, 9, 3, 4, 10, 12)

    # Vertical clefts separating the 3 lobes (deep 1-voxel slots)
    g.clear_box(6, 6, 2, 7, 6, 9)
    g.clear_box(10, 10, 2, 7, 6, 9)

    # Corner notch facets
    g.clear_box(2, 2, 0, 4, 6, 6)
    g.clear_box(14, 14, 0, 4, 6, 6)
    g.clear_box(2, 2, 0, 4, 12, 12)
    g.clear_box(14, 14, 0, 4, 12, 12)
    g.clear_box(6, 6, 0, 4, 13, 14)

    g.remove_floating()
    g.apply_natural_materials(allow_moss=True, moss_y_range=(2, 6), max_moss=25)
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
    # Lobe 1: West Peak (x in [2, 7], z in [4, 11], height 10)
    g.fill_box(2, 7, 0, 6, 4, 11)
    g.fill_box(3, 6, 7, 8, 5, 10)
    g.fill_box(3, 5, 9, 10, 6, 9)

    # Lobe 2: East Peak (x in [10, 15], z in [4, 11], height 9)
    g.fill_box(10, 15, 0, 6, 4, 11)
    g.fill_box(11, 14, 7, 8, 5, 10)
    g.fill_box(12, 14, 9, 9, 6, 9)

    # Lobe 3: Central Saddle Bridge (x in [7, 10], z in [5, 10], height 5)
    g.fill_box(7, 10, 0, 5, 5, 10)

    # Lobe 4: South-West Spur (x in [3, 6], z in [11, 13], height 4)
    g.fill_box(3, 6, 0, 3, 11, 13)

    # Lobe 5: North-East Spur (x in [11, 14], z in [2, 4], height 3)
    g.fill_box(11, 14, 0, 3, 2, 4)

    # Crevice notches breaking the saddle
    g.clear_box(8, 9, 4, 5, 7, 9)

    # Corner notch facets
    g.clear_box(2, 2, 0, 6, 4, 5)
    g.clear_box(15, 15, 0, 6, 10, 11)

    g.remove_floating()
    g.apply_natural_materials(allow_moss=True, moss_y_range=(2, 6), max_moss=25)
    return g


# -------------------------------------------------------------------------
# STAGE 2: Large Broken Rock (3 Variants)
# Target voxels: ~420 - 580
# -------------------------------------------------------------------------

def build_stage_2_var_1() -> VoxelGrid:
    """Truncated Block: High fractured side dropping sharply to low stepped apron."""
    g = VoxelGrid(14, 9, 14)
    # High West block
    g.fill_box(2, 7, 0, 6, 3, 11)
    g.fill_box(3, 6, 7, 8, 4, 10)

    # Lower broken East apron
    g.fill_box(8, 12, 0, 3, 4, 10)
    g.fill_box(8, 11, 4, 4, 5, 9)

    # North foothill
    g.fill_box(4, 9, 0, 2, 2, 4)

    # Fracture crevice between blocks
    g.clear_box(7, 7, 3, 6, 5, 9)

    # Clean corner notches
    g.clear_box(2, 2, 0, 6, 3, 4)
    g.clear_box(12, 12, 0, 3, 9, 10)

    g.remove_floating()
    g.apply_natural_materials(allow_moss=True, moss_y_range=(2, 5), max_moss=12)
    return g


def build_stage_2_var_2() -> VoxelGrid:
    """Stepped Pyramid Crag: Asymmetric tiered rock mass."""
    g = VoxelGrid(14, 8, 14)
    # Base lobe
    g.fill_box(2, 11, 0, 3, 2, 11)
    g.clear_box(2, 2, 0, 3, 2, 3)
    g.clear_box(11, 11, 0, 3, 2, 3)
    # Tier 2
    g.fill_box(3, 10, 4, 5, 3, 10)
    g.clear_box(3, 3, 4, 5, 3, 4)
    # Tier 3 (Peak)
    g.fill_box(4, 8, 6, 7, 4, 8)
    g.clear_box(8, 8, 6, 7, 8, 8)

    # South-East spur
    g.fill_box(8, 12, 0, 2, 8, 11)

    g.remove_floating()
    g.apply_natural_materials(allow_moss=True, moss_y_range=(2, 5), max_moss=12)
    return g


def build_stage_2_var_3() -> VoxelGrid:
    """Slanted Core Remnant: Angular rock with broken shoulders and fissures."""
    g = VoxelGrid(14, 8, 14)
    # Main slanted mass
    g.fill_box(3, 10, 0, 4, 3, 9)
    g.fill_box(3, 8, 5, 6, 4, 8)
    g.fill_box(4, 7, 7, 7, 4, 7)

    # Flanking shoulder
    g.fill_box(8, 12, 0, 3, 6, 11)
    g.fill_box(9, 11, 4, 5, 7, 10)

    # South-West low spur
    g.fill_box(3, 6, 0, 2, 9, 12)

    # Crevice
    g.clear_box(8, 8, 2, 5, 6, 9)

    # Corner notches
    g.clear_box(3, 3, 0, 4, 3, 3)
    g.clear_box(12, 12, 0, 3, 10, 11)

    g.remove_floating()
    g.apply_natural_materials(allow_moss=True, moss_y_range=(2, 5), max_moss=12)
    return g


# -------------------------------------------------------------------------
# STAGE 3: Medium Remnant (3 Variants)
# Target voxels: ~200 - 280
# -------------------------------------------------------------------------

def build_stage_3_var_1() -> VoxelGrid:
    """Triangular Wedge: Compact angular rock wedge."""
    g = VoxelGrid(12, 7, 12)
    g.fill_box(2, 8, 0, 3, 2, 8)
    g.clear_box(2, 2, 0, 3, 2, 3)
    g.fill_box(2, 6, 4, 5, 2, 6)
    g.fill_box(3, 5, 6, 6, 3, 5)
    g.fill_box(6, 9, 0, 2, 6, 8)

    g.remove_floating()
    g.apply_natural_materials(allow_moss=True, moss_y_range=(2, 4), max_moss=6)
    return g


def build_stage_3_var_2() -> VoxelGrid:
    """Twin Chunk Remnant: Two merged rocky masses with cleft."""
    g = VoxelGrid(12, 6, 12)
    # Lobe A
    g.fill_box(2, 6, 0, 3, 3, 8)
    g.fill_box(3, 5, 4, 5, 4, 7)
    g.clear_box(2, 2, 0, 3, 3, 3)

    # Lobe B
    g.fill_box(7, 10, 0, 2, 4, 8)
    g.fill_box(7, 9, 3, 4, 5, 7)
    g.clear_box(10, 10, 0, 2, 7, 8)

    # Notch
    g.clear_box(6, 6, 2, 5, 4, 8)

    g.remove_floating()
    g.apply_natural_materials(allow_moss=True, moss_y_range=(2, 4), max_moss=6)
    return g


def build_stage_3_var_3() -> VoxelGrid:
    """Fractured Stump: Squat chunky rock with stepped fractured top."""
    g = VoxelGrid(12, 6, 12)
    g.fill_box(2, 9, 0, 2, 2, 9)
    g.clear_box(2, 2, 0, 2, 2, 3)
    g.clear_box(9, 9, 0, 2, 8, 9)
    g.fill_box(3, 8, 3, 4, 3, 8)
    g.fill_box(4, 7, 5, 5, 4, 7)

    g.remove_floating()
    g.apply_natural_materials(allow_moss=True, moss_y_range=(2, 4), max_moss=6)
    return g


# -------------------------------------------------------------------------
# STAGE 4: Small Rubble Group (2 Variants)
# Target voxels: ~100 - 140
# -------------------------------------------------------------------------

def build_stage_4_var_1() -> VoxelGrid:
    """Fragment & Satellites: Main chunky fragment with 2 separate satellite chunks."""
    g = VoxelGrid(12, 5, 12)
    # Piece 1: Main block
    g.fill_box(2, 6, 0, 2, 2, 6)
    g.clear_box(2, 2, 0, 2, 2, 2)
    g.fill_box(3, 5, 3, 4, 3, 5)

    # Piece 2: Satellite East
    g.fill_box(8, 10, 0, 1, 3, 5)

    # Piece 3: Satellite South
    g.fill_box(3, 5, 0, 1, 8, 10)

    g.remove_floating()
    g.apply_natural_materials(allow_moss=True, moss_y_range=(1, 3), max_moss=2)
    return g


def build_stage_4_var_2() -> VoxelGrid:
    """Triad Debris Cluster: Three chunky rock fragments in loose separated group."""
    g = VoxelGrid(12, 4, 12)
    # Chunk A (NW)
    g.fill_box(2, 5, 0, 2, 2, 5)
    g.fill_box(3, 4, 3, 3, 3, 4)

    # Chunk B (NE)
    g.fill_box(7, 10, 0, 1, 2, 5)
    g.fill_box(8, 9, 2, 2, 3, 4)

    # Chunk C (South)
    g.fill_box(3, 7, 0, 1, 7, 10)
    g.fill_box(4, 6, 2, 2, 8, 9)

    g.remove_floating()
    g.apply_natural_materials(allow_moss=True, moss_y_range=(1, 2), max_moss=2)
    return g


# -------------------------------------------------------------------------
# STAGE 5: Small Rubble Pile / Debris (3 Variants)
# Target voxels: ~32 - 45
# -------------------------------------------------------------------------

def build_stage_5_var_1() -> VoxelGrid:
    """Central Nub with small scatter: 1 low central rock + 4 separate pebbles."""
    g = VoxelGrid(10, 3, 10)
    g.fill_box(4, 6, 0, 1, 4, 6)
    g.fill_box(4, 5, 2, 2, 5, 6)

    # Pebble 1 (West)
    g.fill_box(1, 2, 0, 0, 4, 5)
    g.set(2, 1, 4)

    # Pebble 2 (East)
    g.fill_box(8, 8, 0, 0, 4, 5)
    g.set(8, 1, 5)

    # Pebble 3 (North)
    g.fill_box(4, 5, 0, 0, 1, 2)
    g.set(5, 1, 2)

    # Pebble 4 (South)
    g.fill_box(5, 6, 0, 0, 8, 8)

    g.remove_floating()
    g.apply_natural_materials(allow_moss=False)
    return g


def build_stage_5_var_2() -> VoxelGrid:
    """Angular Linear Debris trail: Diagonal trail of 4 separate angular rubble stones."""
    g = VoxelGrid(10, 3, 10)
    # Piece 1 (SW)
    g.fill_box(1, 3, 0, 0, 7, 8)
    g.fill_box(2, 3, 1, 1, 7, 8)

    # Piece 2 (Center-SW)
    g.fill_box(4, 6, 0, 1, 4, 5)
    g.set(5, 2, 4)

    # Piece 3 (Center-NE)
    g.fill_box(8, 9, 0, 0, 3, 4)
    g.set(8, 1, 3)

    # Piece 4 (Far NE)
    g.fill_box(8, 9, 0, 0, 0, 1)
    g.set(8, 1, 0)

    g.remove_floating()
    g.apply_natural_materials(allow_moss=False)
    return g


def build_stage_5_var_3() -> VoxelGrid:
    """Crescent Rubble Mound: Arc of 4 separate rubble pieces."""
    g = VoxelGrid(10, 3, 10)
    # Piece 1 (NW)
    g.fill_box(2, 4, 0, 0, 2, 3)
    g.set(3, 1, 2)
    g.set(3, 1, 3)

    # Piece 2 (NE/E)
    g.fill_box(6, 8, 0, 1, 3, 5)
    g.set(7, 2, 4)

    # Piece 3 (SE)
    g.fill_box(5, 7, 0, 0, 7, 8)
    g.set(6, 1, 7)

    # Piece 4 (SW)
    g.fill_box(1, 2, 0, 0, 5, 6)

    g.remove_floating()
    g.apply_natural_materials(allow_moss=False)
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
                "max_materials": 4,
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
- **Materials**: Multi-tone natural rock palette matching approved concept reference.
"""
        initialize_text(pkg_dir / "request.md", request_content)

        # 3. Voxel source
        voxels_data = grid.to_json_dict(manifest["name"])
        (pkg_dir / "source" / "voxels.json").write_text(
            json.dumps(voxels_data, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8"
        )

        # 4. Review template: only write initial template if review.md does not already exist
        review_path = pkg_dir / "review" / "review.md"
        if not review_path.exists():
            review_md = f"""# Self Review: {title}

## Result
- [ ] Source matches request and Issue #3 criteria.
- [ ] Required review renders generated.
- [ ] Silhouette reads from iso/game-like view with distinct angular planes.
- [x] No accidental floating/disconnected geometry.
- [x] Voxel density is intentional and consistent (size={VOXEL_SIZE}).
- [x] Material count is within budget (<= 4 materials).
- [ ] Triangle count verified.
- [ ] Export validated.

## Metrics
- Occupied voxels: {occupied}
- Grid: {grid.width}x{grid.height}x{grid.depth}
"""
            review_path.write_text(review_md, encoding="utf-8")

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

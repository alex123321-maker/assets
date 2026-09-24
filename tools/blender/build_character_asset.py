"""Production-ready rigged voxel character builder for Cube Siege enemies.
Supports:
  - zombie (basic melee undead)
  - ranged_skirmisher (undead archer)
  - siege_breaker (massive siege brute)

Incorporates Mentor recommendations:
  - Archer: Prominent angular recurve bow held outward with clear negative space, quiver silhouette.
  - Zombie: Distinct stepped head -> shoulders -> hips silhouette, reaching arms separated from chest.
  - Siege Breaker: Wide shoulder clearance, distinct head cavity, undead bone/flesh cues amidst stone plates.
  - Rigging: Rigid voxel skin weighting, explicit sockets (BowSocket.L, ArrowReleasePoint, SmashPoint).
  - Robust Blender 5.2 pose bone keyframing.
  - Clean single-mesh 'Body' for single-mesh damage-flash material_override compatibility.
  - Pure silhouette passes, gameplay camera renders, and animation filmstrips.
"""

from __future__ import annotations
import argparse
import json
import math
import os
import sys
from pathlib import Path

import bpy
import bmesh
from mathutils import Vector, Euler, Matrix, Quaternion

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.append(str(Path(__file__).resolve().parent))
import character_builder_core as core


def parse_args():
    argv = sys.argv
    argv = argv[argv.index("--") + 1 :] if "--" in argv else []
    parser = argparse.ArgumentParser()
    parser.add_argument("--asset", required=True, type=Path, help="Path to character package")
    return parser.parse_args(argv)


# =============================================================================
# 1. ZOMBIE MODEL DEFINITION
# =============================================================================

def build_zombie_mesh(bm: bmesh.types.BMesh, weights: dict[str, list[int]]):
    # Palette:
    # 0: mat_decay_flesh    (#84946e) - Muted sage necrotic skin
    # 1: mat_pale_flesh     (#9baa84) - Lighter decay highlight
    # 2: mat_tattered_cloth (#524032) - Muted brown ragged cloth
    # 3: mat_bone_teeth     (#cfc8b6) - Warm ivory exposed bone/teeth
    # 4: mat_dark_socket    (#1c221a) - Deep dark recess

    # Hips / Pelvis (centered at Z=0.92)
    core.add_box_geometry(bm, (0, 0, 0.92), (0.48, 0.26, 0.20), "Hips", weights, mat_index=2, rot=(10, 0, 0))
    # Tattered ragged loincloth strips
    core.add_box_geometry(bm, (-0.12, 0.12, 0.82), (0.15, 0.06, 0.22), "Hips", weights, mat_index=2, rot=(14, 6, 0))
    core.add_box_geometry(bm, (0.10, 0.12, 0.80), (0.16, 0.06, 0.24), "Hips", weights, mat_index=2, rot=(12, -4, 0))
    core.add_box_geometry(bm, (0, -0.12, 0.82), (0.42, 0.06, 0.20), "Hips", weights, mat_index=2, rot=(8, 0, 0))

    # Spine (lower torso - hunched forward 16 deg)
    core.add_box_geometry(bm, (0, 0.06, 1.10), (0.46, 0.28, 0.22), "Spine", weights, mat_index=0, rot=(16, 0, 0))
    # Exposed ribs on spine
    core.add_box_geometry(bm, (-0.14, 0.19, 1.10), (0.10, 0.04, 0.12), "Spine", weights, mat_index=3, rot=(16, 0, 0))
    core.add_box_geometry(bm, (0.14, 0.19, 1.10), (0.10, 0.04, 0.12), "Spine", weights, mat_index=3, rot=(16, 0, 0))

    # Chest (hunched upper torso - 22 deg forward)
    core.add_box_geometry(bm, (0, 0.16, 1.28), (0.54, 0.34, 0.26), "Chest", weights, mat_index=2, rot=(22, 0, 0))
    # Torn tunic collars
    core.add_box_geometry(bm, (-0.22, 0.20, 1.38), (0.16, 0.24, 0.12), "Chest", weights, mat_index=2, rot=(20, 10, -4))
    core.add_box_geometry(bm, (0.22, 0.18, 1.36), (0.16, 0.22, 0.12), "Chest", weights, mat_index=2, rot=(24, -8, 4))
    # Exposed decaying chest center
    core.add_box_geometry(bm, (0, 0.32, 1.28), (0.24, 0.06, 0.18), "Chest", weights, mat_index=1, rot=(22, 0, 0))

    # Neck (thrust forward)
    core.add_box_geometry(bm, (0, 0.26, 1.44), (0.20, 0.20, 0.14), "Neck", weights, mat_index=0, rot=(28, 0, 0))

    # Head (hunched forward skull with jutting jaw)
    core.add_box_geometry(bm, (0, 0.38, 1.58), (0.38, 0.38, 0.36), "Head", weights, mat_index=0, rot=(14, 0, 0))
    # Pale brow / forehead
    core.add_box_geometry(bm, (0, 0.46, 1.68), (0.36, 0.22, 0.14), "Head", weights, mat_index=1, rot=(14, 0, 0))
    # Eye sockets (dark recess)
    core.add_box_geometry(bm, (-0.10, 0.56, 1.62), (0.09, 0.04, 0.09), "Head", weights, mat_index=4, rot=(14, 0, 0))
    core.add_box_geometry(bm, (0.10, 0.56, 1.62), (0.09, 0.04, 0.09), "Head", weights, mat_index=4, rot=(14, 0, 0))
    # Jutting Jaw & exposed teeth
    core.add_box_geometry(bm, (0, 0.48, 1.45), (0.32, 0.22, 0.14), "Head", weights, mat_index=0, rot=(8, 0, 0))
    core.add_box_geometry(bm, (0, 0.57, 1.47), (0.22, 0.05, 0.06), "Head", weights, mat_index=3, rot=(8, 0, 0))

    # Left Arm (aggro reaching outward-forward to preserve negative space)
    core.add_box_geometry(bm, (-0.38, 0.18, 1.34), (0.18, 0.18, 0.32), "UpperArm.L", weights, mat_index=2, rot=(26, 12, -8))
    core.add_box_geometry(bm, (-0.42, 0.46, 1.28), (0.16, 0.36, 0.16), "Forearm.L", weights, mat_index=0, rot=(55, 6, -10))
    # Left Hand & Claws
    core.add_box_geometry(bm, (-0.44, 0.70, 1.26), (0.18, 0.14, 0.14), "Hand.L", weights, mat_index=1, rot=(40, 0, -10))
    core.add_box_geometry(bm, (-0.48, 0.80, 1.24), (0.05, 0.14, 0.05), "Hand.L", weights, mat_index=3, rot=(26, 8, -4))
    core.add_box_geometry(bm, (-0.42, 0.82, 1.26), (0.05, 0.15, 0.05), "Hand.L", weights, mat_index=3, rot=(30, 0, -6))
    core.add_box_geometry(bm, (-0.36, 0.80, 1.25), (0.05, 0.13, 0.05), "Hand.L", weights, mat_index=3, rot=(28, -6, -4))

    # Right Arm (slight asymmetry: lower reach, open silhouette)
    core.add_box_geometry(bm, (0.38, 0.14, 1.32), (0.18, 0.18, 0.32), "UpperArm.R", weights, mat_index=0, rot=(20, -10, 8))
    core.add_box_geometry(bm, (0.42, 0.40, 1.18), (0.16, 0.36, 0.16), "Forearm.R", weights, mat_index=0, rot=(45, -4, 10))
    # Right Hand & Claws
    core.add_box_geometry(bm, (0.44, 0.62, 1.10), (0.18, 0.14, 0.14), "Hand.R", weights, mat_index=1, rot=(30, 0, 10))
    core.add_box_geometry(bm, (0.48, 0.72, 1.08), (0.05, 0.14, 0.05), "Hand.R", weights, mat_index=3, rot=(22, -8, 4))
    core.add_box_geometry(bm, (0.42, 0.74, 1.09), (0.05, 0.15, 0.05), "Hand.R", weights, mat_index=3, rot=(26, 0, 6))
    core.add_box_geometry(bm, (0.36, 0.72, 1.08), (0.05, 0.13, 0.05), "Hand.R", weights, mat_index=3, rot=(24, 6, 4))

    # Left Leg (Thigh, Shin, Foot)
    core.add_box_geometry(bm, (-0.16, 0.0, 0.70), (0.20, 0.22, 0.36), "Thigh.L", weights, mat_index=2, rot=(8, 0, 0))
    core.add_box_geometry(bm, (-0.16, 0.04, 0.34), (0.18, 0.20, 0.36), "Shin.L", weights, mat_index=0, rot=(-6, 0, 0))
    core.add_box_geometry(bm, (-0.16, 0.08, 0.07), (0.20, 0.34, 0.14), "Foot.L", weights, mat_index=0, rot=(0, 0, 0))

    # Right Leg
    core.add_box_geometry(bm, (0.16, -0.04, 0.70), (0.20, 0.22, 0.36), "Thigh.R", weights, mat_index=2, rot=(-4, 0, 0))
    core.add_box_geometry(bm, (0.16, -0.02, 0.34), (0.18, 0.20, 0.36), "Shin.R", weights, mat_index=0, rot=(4, 0, 0))
    core.add_box_geometry(bm, (0.16, -0.04, 0.07), (0.20, 0.34, 0.14), "Foot.R", weights, mat_index=0, rot=(0, 0, 0))


def get_zombie_bone_defs() -> dict[str, dict]:
    return {
        "Root": {"head": (0, 0, 0), "tail": (0, 0, 0.2), "parent": None},
        "Hips": {"head": (0, 0, 0.92), "tail": (0, 0.04, 1.02), "parent": "Root"},
        "Spine": {"head": (0, 0.04, 1.02), "tail": (0, 0.10, 1.20), "parent": "Hips", "connected": True},
        "Chest": {"head": (0, 0.10, 1.20), "tail": (0, 0.20, 1.40), "parent": "Spine", "connected": True},
        "Neck": {"head": (0, 0.20, 1.40), "tail": (0, 0.28, 1.52), "parent": "Chest", "connected": True},
        "Head": {"head": (0, 0.28, 1.52), "tail": (0, 0.42, 1.74), "parent": "Neck", "connected": True},
        
        "Shoulder.L": {"head": (-0.15, 0.14, 1.36), "tail": (-0.28, 0.16, 1.36), "parent": "Chest"},
        "UpperArm.L": {"head": (-0.28, 0.16, 1.36), "tail": (-0.38, 0.36, 1.32), "parent": "Shoulder.L", "connected": True},
        "Forearm.L": {"head": (-0.38, 0.36, 1.32), "tail": (-0.42, 0.62, 1.28), "parent": "UpperArm.L", "connected": True},
        "Hand.L": {"head": (-0.42, 0.62, 1.28), "tail": (-0.44, 0.80, 1.25), "parent": "Forearm.L", "connected": True},
        "ClawSocket.L": {"head": (-0.44, 0.80, 1.25), "tail": (-0.44, 0.90, 1.25), "parent": "Hand.L", "connected": True},
        
        "Shoulder.R": {"head": (0.15, 0.12, 1.34), "tail": (0.28, 0.14, 1.34), "parent": "Chest"},
        "UpperArm.R": {"head": (0.28, 0.14, 1.34), "tail": (0.38, 0.32, 1.24), "parent": "Shoulder.R", "connected": True},
        "Forearm.R": {"head": (0.38, 0.32, 1.24), "tail": (0.42, 0.54, 1.14), "parent": "UpperArm.R", "connected": True},
        "Hand.R": {"head": (0.42, 0.54, 1.14), "tail": (0.44, 0.72, 1.09), "parent": "Forearm.R", "connected": True},
        "ClawSocket.R": {"head": (0.44, 0.72, 1.09), "tail": (0.44, 0.82, 1.09), "parent": "Hand.R", "connected": True},
        
        "Thigh.L": {"head": (-0.16, 0.02, 0.88), "tail": (-0.16, 0.02, 0.50), "parent": "Hips"},
        "Shin.L": {"head": (-0.16, 0.02, 0.50), "tail": (-0.16, 0.04, 0.14), "parent": "Thigh.L", "connected": True},
        "Foot.L": {"head": (-0.16, 0.04, 0.14), "tail": (-0.16, 0.22, 0.06), "parent": "Shin.L", "connected": True},
        
        "Thigh.R": {"head": (0.16, -0.02, 0.88), "tail": (0.16, -0.02, 0.50), "parent": "Hips"},
        "Shin.R": {"head": (0.16, -0.02, 0.50), "tail": (0.16, -0.02, 0.14), "parent": "Thigh.R", "connected": True},
        "Foot.R": {"head": (0.16, -0.02, 0.14), "tail": (0.16, 0.16, 0.06), "parent": "Shin.R", "connected": True},
    }


# =============================================================================
# 2. RANGED SKIRMISHER MODEL DEFINITION
# =============================================================================

def build_skirmisher_mesh(bm: bmesh.types.BMesh, weights: dict[str, list[int]]):
    # Palette:
    # 0: mat_bone_weathered (#cfc4a6) - Warm ivory skeletal bone
    # 1: mat_bone_dark      (#9c9276) - Recessed dark bone/joint
    # 2: mat_ragged_leather (#4e392a) - Muted brown quiver & strap
    # 3: mat_bow_wood       (#683e20) - Distinct warm brown recurve wood
    # 4: mat_bow_string     (#e8e2d4) - Light bowstring
    # 5: mat_dark_socket    (#181816) - Dark eye/nasal cavity

    # Pelvis (lean 0.34m)
    core.add_box_geometry(bm, (0, 0, 0.94), (0.34, 0.18, 0.14), "Hips", weights, mat_index=0)
    core.add_box_geometry(bm, (0, 0, 0.95), (0.36, 0.20, 0.06), "Hips", weights, mat_index=2) # Leather belt

    # Slender Spine (clear negative space between pelvis and ribs)
    core.add_box_geometry(bm, (0, 0.01, 1.08), (0.12, 0.12, 0.16), "Spine", weights, mat_index=1)

    # Ribcage (tapered skeletal cage)
    core.add_box_geometry(bm, (0, 0.03, 1.26), (0.38, 0.22, 0.22), "Chest", weights, mat_index=0)
    # Dark rib cavity insets
    core.add_box_geometry(bm, (0, 0.14, 1.27), (0.32, 0.02, 0.05), "Chest", weights, mat_index=5)
    core.add_box_geometry(bm, (0, 0.14, 1.21), (0.28, 0.02, 0.04), "Chest", weights, mat_index=5)

    # Quiver on right shoulder (angled back-right, distinct silhouette in edge-on view)
    core.add_box_geometry(bm, (0.14, -0.16, 1.34), (0.14, 0.14, 0.52), "Chest", weights, mat_index=2, rot=(18, -16, 0))
    # Protruding arrow shafts with fletchings
    core.add_box_geometry(bm, (0.18, -0.22, 1.66), (0.04, 0.04, 0.18), "Chest", weights, mat_index=3, rot=(18, -16, 0))
    core.add_box_geometry(bm, (0.14, -0.18, 1.70), (0.04, 0.04, 0.20), "Chest", weights, mat_index=3, rot=(14, -20, 0))
    core.add_box_geometry(bm, (0.20, -0.25, 1.64), (0.07, 0.07, 0.08), "Chest", weights, mat_index=4, rot=(18, -16, 0))

    # Neck
    core.add_box_geometry(bm, (0, 0.03, 1.42), (0.12, 0.12, 0.10), "Neck", weights, mat_index=1)

    # Skull
    core.add_box_geometry(bm, (0, 0.05, 1.58), (0.34, 0.34, 0.32), "Head", weights, mat_index=0)
    # Eye sockets
    core.add_box_geometry(bm, (-0.08, 0.22, 1.60), (0.08, 0.02, 0.08), "Head", weights, mat_index=5)
    core.add_box_geometry(bm, (0.08, 0.22, 1.60), (0.08, 0.02, 0.08), "Head", weights, mat_index=5)
    # Teeth / upper jaw
    core.add_box_geometry(bm, (0, 0.21, 1.46), (0.20, 0.08, 0.06), "Head", weights, mat_index=0)

    # Left Arm (extended outward-lateral to create clear negative space between bow and body in gameplay camera)
    core.add_box_geometry(bm, (-0.32, 0.03, 1.31), (0.22, 0.12, 0.12), "UpperArm.L", weights, mat_index=0, rot=(4, -16, 6))
    core.add_box_geometry(bm, (-0.50, 0.05, 1.265), (0.18, 0.10, 0.10), "Forearm.L", weights, mat_index=1, rot=(2, -10, 7))
    core.add_box_geometry(bm, (-0.62, 0.06, 1.25), (0.10, 0.10, 0.12), "Hand.L", weights, mat_index=0, rot=(0, 0, 40))

    # Large Recurve Bow (stepped angular arc 1.1m tall, held outward in left hand, angled 40 deg for rich gameplay silhouette)
    # Central grip
    core.add_box_geometry(bm, (-0.64, 0.06, 1.25), (0.08, 0.08, 0.26), "Hand.L", weights, mat_index=3, rot=(0, 0, 40))
    # Upper limb (curving forward-outward then recurve tip)
    core.add_box_geometry(bm, (-0.678, 0.028, 1.43), (0.07, 0.07, 0.22), "Hand.L", weights, mat_index=3, rot=(-14, 12, 40))
    core.add_box_geometry(bm, (-0.717, -0.004, 1.61), (0.06, 0.06, 0.20), "Hand.L", weights, mat_index=3, rot=(-28, 23, 40))
    core.add_box_geometry(bm, (-0.740, -0.024, 1.77), (0.05, 0.06, 0.14), "Hand.L", weights, mat_index=3, rot=(19, -16, 40)) # Recurve tip
    # Lower limb (curving forward-outward then recurve tip)
    core.add_box_geometry(bm, (-0.678, 0.028, 1.07), (0.07, 0.07, 0.22), "Hand.L", weights, mat_index=3, rot=(14, -12, 40))
    core.add_box_geometry(bm, (-0.717, -0.004, 0.89), (0.06, 0.06, 0.20), "Hand.L", weights, mat_index=3, rot=(28, -23, 40))
    core.add_box_geometry(bm, (-0.740, -0.024, 0.73), (0.05, 0.06, 0.14), "Hand.L", weights, mat_index=3, rot=(-19, 16, 40)) # Recurve tip
    # Bow string
    core.add_box_geometry(bm, (-0.563, 0.124, 1.25), (0.04, 0.04, 1.04), "Hand.L", weights, mat_index=4, rot=(0, 0, 40))

    # Right Arm (poised with elbow out to emphasize archer readiness)
    core.add_box_geometry(bm, (0.24, 0.02, 1.32), (0.12, 0.12, 0.30), "UpperArm.R", weights, mat_index=0, rot=(12, -18, 12))
    core.add_box_geometry(bm, (0.30, 0.18, 1.10), (0.10, 0.26, 0.10), "Forearm.R", weights, mat_index=1, rot=(38, 0, 10))
    core.add_box_geometry(bm, (0.30, 0.30, 1.00), (0.10, 0.10, 0.10), "Hand.R", weights, mat_index=0)

    # Left Leg (slender bone)
    core.add_box_geometry(bm, (-0.13, 0.0, 0.70), (0.13, 0.14, 0.40), "Thigh.L", weights, mat_index=0)
    core.add_box_geometry(bm, (-0.13, 0.01, 0.33), (0.11, 0.12, 0.38), "Shin.L", weights, mat_index=1)
    core.add_box_geometry(bm, (-0.13, 0.06, 0.06), (0.13, 0.26, 0.12), "Foot.L", weights, mat_index=0)

    # Right Leg
    core.add_box_geometry(bm, (0.13, 0.0, 0.70), (0.13, 0.14, 0.40), "Thigh.R", weights, mat_index=0)
    core.add_box_geometry(bm, (0.13, -0.01, 0.33), (0.11, 0.12, 0.38), "Shin.R", weights, mat_index=1)
    core.add_box_geometry(bm, (0.13, 0.02, 0.06), (0.13, 0.26, 0.12), "Foot.R", weights, mat_index=0)


def get_skirmisher_bone_defs() -> dict[str, dict]:
    return {
        "Root": {"head": (0, 0, 0), "tail": (0, 0, 0.2), "parent": None},
        "Hips": {"head": (0, 0, 0.94), "tail": (0, 0.02, 1.04), "parent": "Root"},
        "Spine": {"head": (0, 0.02, 1.04), "tail": (0, 0.03, 1.18), "parent": "Hips", "connected": True},
        "Chest": {"head": (0, 0.03, 1.18), "tail": (0, 0.04, 1.38), "parent": "Spine", "connected": True},
        "Neck": {"head": (0, 0.04, 1.38), "tail": (0, 0.05, 1.48), "parent": "Chest", "connected": True},
        "Head": {"head": (0, 0.05, 1.48), "tail": (0, 0.06, 1.74), "parent": "Neck", "connected": True},
        
        "Shoulder.L": {"head": (-0.12, 0.02, 1.34), "tail": (-0.22, 0.02, 1.34), "parent": "Chest"},
        "UpperArm.L": {"head": (-0.22, 0.02, 1.34), "tail": (-0.42, 0.04, 1.28), "parent": "Shoulder.L", "connected": True},
        "Forearm.L": {"head": (-0.42, 0.04, 1.28), "tail": (-0.58, 0.06, 1.25), "parent": "UpperArm.L", "connected": True},
        "Hand.L": {"head": (-0.58, 0.06, 1.25), "tail": (-0.66, 0.06, 1.25), "parent": "Forearm.L", "connected": True},
        "BowSocket.L": {"head": (-0.64, 0.06, 1.25), "tail": (-0.64, 0.16, 1.25), "parent": "Hand.L"},
        "ArrowReleasePoint": {"head": (-0.64, 0.26, 1.25), "tail": (-0.64, 0.46, 1.25), "parent": "BowSocket.L"},

        "Shoulder.R": {"head": (0.12, 0.03, 1.34), "tail": (0.22, 0.03, 1.34), "parent": "Chest"},
        "UpperArm.R": {"head": (0.22, 0.03, 1.34), "tail": (0.28, 0.10, 1.18), "parent": "Shoulder.R", "connected": True},
        "Forearm.R": {"head": (0.28, 0.10, 1.18), "tail": (0.30, 0.24, 1.02), "parent": "UpperArm.R", "connected": True},
        "Hand.R": {"head": (0.30, 0.24, 1.02), "tail": (0.30, 0.34, 0.96), "parent": "Forearm.R", "connected": True},
        
        "QuiverSocket": {"head": (0.14, -0.16, 1.34), "tail": (0.14, -0.26, 1.50), "parent": "Chest"},

        "Thigh.L": {"head": (-0.13, 0.0, 0.88), "tail": (-0.13, 0.01, 0.50), "parent": "Hips"},
        "Shin.L": {"head": (-0.13, 0.01, 0.50), "tail": (-0.13, 0.01, 0.14), "parent": "Thigh.L", "connected": True},
        "Foot.L": {"head": (-0.13, 0.01, 0.14), "tail": (-0.13, 0.18, 0.06), "parent": "Shin.L", "connected": True},
        
        "Thigh.R": {"head": (0.13, 0.0, 0.88), "tail": (0.13, -0.01, 0.50), "parent": "Hips"},
        "Shin.R": {"head": (0.13, -0.01, 0.50), "tail": (0.13, -0.01, 0.14), "parent": "Thigh.R", "connected": True},
        "Foot.R": {"head": (0.13, -0.01, 0.14), "tail": (0.13, 0.14, 0.06), "parent": "Shin.R", "connected": True},
    }


# =============================================================================
# 3. SIEGE BREAKER MODEL DEFINITION
# =============================================================================

def build_siege_breaker_mesh(bm: bmesh.types.BMesh, weights: dict[str, list[int]]):
    # Palette:
    # 0: mat_decay_brute_flesh (#54624d) - Decaying necrotic titan skin
    # 1: mat_corrupted_stone   (#42484f) - Cool slate stone armor
    # 2: mat_iron_plate        (#2c2f34) - Heavy iron trim/fists (metallic)
    # 3: mat_bone_armor        (#cfc5ae) - Exposed necrotic skull/bone band
    # 4: mat_ragged_loincloth  (#4e2b24) - Heavy tattered cloth

    # Pelvis
    core.add_box_geometry(bm, (0, 0, 1.25), (0.92, 0.56, 0.30), "Hips", weights, mat_index=1)
    # Loincloth
    core.add_box_geometry(bm, (0, 0.26, 1.10), (0.40, 0.10, 0.42), "Hips", weights, mat_index=4, rot=(10, 0, 0))

    # Spine (with exposed decaying necrotic flesh flanks)
    core.add_box_geometry(bm, (0, 0.04, 1.48), (0.86, 0.52, 0.28), "Spine", weights, mat_index=0, rot=(8, 0, 0))
    core.add_box_geometry(bm, (0, -0.26, 1.50), (0.44, 0.14, 0.34), "Spine", weights, mat_index=1, rot=(8, 0, 0)) # Stone spine ridge

    # Chest / Torso
    core.add_box_geometry(bm, (0, 0.10, 1.74), (1.14, 0.68, 0.44), "Chest", weights, mat_index=0, rot=(12, 0, 0))
    # Stone chest plates (cut away at neck/shoulders for generous clearance)
    core.add_box_geometry(bm, (-0.26, 0.42, 1.78), (0.44, 0.12, 0.36), "Chest", weights, mat_index=1, rot=(12, 4, 0))
    core.add_box_geometry(bm, (0.26, 0.42, 1.78), (0.44, 0.12, 0.36), "Chest", weights, mat_index=1, rot=(12, -4, 0))
    core.add_box_geometry(bm, (0, 0.46, 1.70), (0.18, 0.08, 0.20), "Chest", weights, mat_index=2, rot=(12, 0, 0))

    # Shoulders Pauldrons (lifted and angled outward to prevent head intersection during overhead smash)
    core.add_box_geometry(bm, (-0.74, 0.08, 1.94), (0.42, 0.50, 0.38), "Chest", weights, mat_index=1, rot=(6, 18, -4))
    core.add_box_geometry(bm, (-0.78, 0.08, 2.08), (0.28, 0.36, 0.14), "Chest", weights, mat_index=2, rot=(6, 18, -4))
    core.add_box_geometry(bm, (0.74, 0.08, 1.94), (0.42, 0.50, 0.38), "Chest", weights, mat_index=1, rot=(6, -18, 4))
    core.add_box_geometry(bm, (0.78, 0.08, 2.08), (0.28, 0.36, 0.14), "Chest", weights, mat_index=2, rot=(6, -18, 4))

    # Neck
    core.add_box_geometry(bm, (0, 0.22, 1.92), (0.40, 0.38, 0.22), "Neck", weights, mat_index=0)

    # Armored Heavy Head & Undead Bone Jaw
    core.add_box_geometry(bm, (0, 0.28, 2.16), (0.56, 0.54, 0.46), "Head", weights, mat_index=0, rot=(8, 0, 0))
    # Stone brow plate
    core.add_box_geometry(bm, (0, 0.34, 2.34), (0.52, 0.48, 0.16), "Head", weights, mat_index=1, rot=(8, 0, 0))
    # Eye sockets
    core.add_box_geometry(bm, (-0.13, 0.54, 2.20), (0.11, 0.04, 0.11), "Head", weights, mat_index=2, rot=(8, 0, 0))
    core.add_box_geometry(bm, (0.13, 0.54, 2.20), (0.11, 0.04, 0.11), "Head", weights, mat_index=2, rot=(8, 0, 0))
    # Exposed undead skull / jaw band
    core.add_box_geometry(bm, (0, 0.48, 2.04), (0.46, 0.30, 0.22), "Head", weights, mat_index=3, rot=(6, 0, 0))
    core.add_box_geometry(bm, (0, 0.58, 2.08), (0.34, 0.08, 0.10), "Head", weights, mat_index=2, rot=(6, 0, 0))

    # Left Heavy Battering Arm (deliberate gap from torso)
    core.add_box_geometry(bm, (-0.82, 0.14, 1.62), (0.36, 0.38, 0.46), "UpperArm.L", weights, mat_index=0, rot=(18, 10, 0))
    core.add_box_geometry(bm, (-0.86, 0.44, 1.34), (0.40, 0.50, 0.40), "Forearm.L", weights, mat_index=1, rot=(46, 4, 0))
    # Giant Stone/Iron Battering Fist
    core.add_box_geometry(bm, (-0.86, 0.72, 1.10), (0.48, 0.48, 0.46), "Hand.L", weights, mat_index=1, rot=(28, 4, 0))
    core.add_box_geometry(bm, (-0.86, 0.86, 1.10), (0.42, 0.20, 0.40), "Hand.L", weights, mat_index=2, rot=(28, 4, 0)) # Knuckles

    # Right Heavy Battering Arm
    core.add_box_geometry(bm, (0.82, 0.12, 1.60), (0.36, 0.38, 0.46), "UpperArm.R", weights, mat_index=0, rot=(16, -10, 0))
    core.add_box_geometry(bm, (0.86, 0.42, 1.32), (0.40, 0.50, 0.40), "Forearm.R", weights, mat_index=1, rot=(42, -4, 0))
    # Giant Stone/Iron Battering Fist
    core.add_box_geometry(bm, (0.86, 0.70, 1.08), (0.48, 0.48, 0.46), "Hand.R", weights, mat_index=1, rot=(26, -4, 0))
    core.add_box_geometry(bm, (0.86, 0.84, 1.08), (0.42, 0.20, 0.40), "Hand.R", weights, mat_index=2, rot=(26, -4, 0))

    # Left Leg (Massive pillar leg)
    core.add_box_geometry(bm, (-0.36, 0.0, 0.94), (0.40, 0.42, 0.46), "Thigh.L", weights, mat_index=0)
    core.add_box_geometry(bm, (-0.38, 0.04, 0.50), (0.36, 0.38, 0.48), "Shin.L", weights, mat_index=1)
    core.add_box_geometry(bm, (-0.38, 0.10, 0.14), (0.40, 0.56, 0.28), "Foot.L", weights, mat_index=2)

    # Right Leg
    core.add_box_geometry(bm, (0.36, 0.0, 0.94), (0.40, 0.42, 0.46), "Thigh.R", weights, mat_index=0)
    core.add_box_geometry(bm, (0.38, -0.04, 0.50), (0.36, 0.38, 0.48), "Shin.R", weights, mat_index=1)
    core.add_box_geometry(bm, (0.38, -0.04, 0.14), (0.40, 0.56, 0.28), "Foot.R", weights, mat_index=2)


def get_siege_breaker_bone_defs() -> dict[str, dict]:
    return {
        "Root": {"head": (0, 0, 0), "tail": (0, 0, 0.3), "parent": None},
        "Hips": {"head": (0, 0, 1.25), "tail": (0, 0.04, 1.40), "parent": "Root"},
        "Spine": {"head": (0, 0.04, 1.40), "tail": (0, 0.08, 1.64), "parent": "Hips", "connected": True},
        "Chest": {"head": (0, 0.08, 1.64), "tail": (0, 0.18, 1.92), "parent": "Spine", "connected": True},
        "Neck": {"head": (0, 0.18, 1.92), "tail": (0, 0.24, 2.06), "parent": "Chest", "connected": True},
        "Head": {"head": (0, 0.24, 2.06), "tail": (0, 0.34, 2.40), "parent": "Neck", "connected": True},
        
        "Shoulder.L": {"head": (-0.30, 0.10, 1.84), "tail": (-0.56, 0.12, 1.84), "parent": "Chest"},
        "UpperArm.L": {"head": (-0.56, 0.12, 1.84), "tail": (-0.78, 0.30, 1.60), "parent": "Shoulder.L", "connected": True},
        "Forearm.L": {"head": (-0.78, 0.30, 1.60), "tail": (-0.84, 0.60, 1.32), "parent": "UpperArm.L", "connected": True},
        "Hand.L": {"head": (-0.84, 0.60, 1.32), "tail": (-0.84, 0.88, 1.08), "parent": "Forearm.L", "connected": True},
        
        "Shoulder.R": {"head": (0.30, 0.10, 1.84), "tail": (0.56, 0.12, 1.84), "parent": "Chest"},
        "UpperArm.R": {"head": (0.56, 0.12, 1.84), "tail": (0.78, 0.28, 1.58), "parent": "Shoulder.R", "connected": True},
        "Forearm.R": {"head": (0.78, 0.28, 1.58), "tail": (0.84, 0.58, 1.30), "parent": "UpperArm.R", "connected": True},
        "Hand.R": {"head": (0.84, 0.58, 1.30), "tail": (0.84, 0.86, 1.06), "parent": "Forearm.R", "connected": True},
        
        "SmashPoint": {"head": (0, 0.85, 0.0), "tail": (0, 0.85, 0.3), "parent": "Root"},

        "Thigh.L": {"head": (-0.36, 0.0, 1.18), "tail": (-0.38, 0.02, 0.72), "parent": "Hips"},
        "Shin.L": {"head": (-0.38, 0.02, 0.72), "tail": (-0.38, 0.06, 0.28), "parent": "Thigh.L", "connected": True},
        "Foot.L": {"head": (-0.38, 0.06, 0.28), "tail": (-0.38, 0.32, 0.12), "parent": "Shin.L", "connected": True},
        
        "Thigh.R": {"head": (0.36, 0.0, 1.18), "tail": (0.38, -0.02, 0.72), "parent": "Hips"},
        "Shin.R": {"head": (0.38, -0.02, 0.72), "tail": (0.38, -0.04, 0.28), "parent": "Thigh.R", "connected": True},
        "Foot.R": {"head": (0.38, -0.04, 0.28), "tail": (0.38, 0.22, 0.12), "parent": "Shin.R", "connected": True},
    }


# =============================================================================
# 4. ROBUST KEYFRAME ANIMATION GENERATOR (Blender 5.x compatible)
# =============================================================================

def apply_pose_keyframe(amt_obj: bpy.types.Object, bone_name: str, frame: int, loc: Vector | None = None, rot_euler: Euler | None = None):
    pb = amt_obj.pose.bones.get(bone_name)
    if not pb:
        return
    pb.rotation_mode = 'QUATERNION'
    if loc is not None:
        pb.location = loc
        pb.keyframe_insert(data_path="location", frame=frame)
    if rot_euler is not None:
        pb.rotation_quaternion = rot_euler.to_quaternion()
        pb.keyframe_insert(data_path="rotation_quaternion", frame=frame)


def reset_pose(amt_obj: bpy.types.Object):
    for pb in amt_obj.pose.bones:
        pb.location = Vector((0, 0, 0))
        pb.rotation_quaternion = Quaternion((1, 0, 0, 0))


def create_character_actions(char_name: str, amt_obj: bpy.types.Object) -> list[bpy.types.Action]:
    actions = []
    amt_obj.animation_data_create()

    # -------------------------------------------------------------
    # ACTION 1: IDLE (60 frames, looping)
    # -------------------------------------------------------------
    act_idle = bpy.data.actions.new(name="idle")
    amt_obj.animation_data.action = act_idle
    reset_pose(amt_obj)

    for frame, chest_rot, head_rot, sway in [(0, 0.0, 0.0, 0.0), (30, 4.0, -3.0, 0.02), (60, 0.0, 0.0, 0.0)]:
        apply_pose_keyframe(amt_obj, "Chest", frame, rot_euler=Euler((math.radians(chest_rot), 0, 0)))
        apply_pose_keyframe(amt_obj, "Head", frame, rot_euler=Euler((math.radians(head_rot), 0, 0)))
        apply_pose_keyframe(amt_obj, "Hips", frame, loc=Vector((sway, 0, 0)))
        if char_name == "zombie":
            apply_pose_keyframe(amt_obj, "UpperArm.L", frame, rot_euler=Euler((math.radians(chest_rot * 1.5), 0, 0)))
            apply_pose_keyframe(amt_obj, "UpperArm.R", frame, rot_euler=Euler((math.radians(-chest_rot * 1.5), 0, 0)))
        elif char_name == "ranged_skirmisher":
            apply_pose_keyframe(amt_obj, "UpperArm.L", frame, rot_euler=Euler((math.radians(chest_rot * 0.5), 0, 0)))
        elif char_name == "siege_breaker":
            apply_pose_keyframe(amt_obj, "UpperArm.L", frame, rot_euler=Euler((math.radians(chest_rot * 1.2), math.radians(2), 0)))
            apply_pose_keyframe(amt_obj, "UpperArm.R", frame, rot_euler=Euler((math.radians(chest_rot * 1.2), math.radians(-2), 0)))
    actions.append(act_idle)

    # -------------------------------------------------------------
    # ACTION 2: MOVE (30 frames, in-place walk loop)
    # -------------------------------------------------------------
    act_move = bpy.data.actions.new(name="move")
    amt_obj.animation_data.action = act_move
    reset_pose(amt_obj)

    leg_amp = 26.0 if char_name != "siege_breaker" else 18.0
    for frame, phase in [(0, 0.0), (7, 0.5), (15, 1.0), (22, 1.5), (30, 2.0)]:
        angle_l = math.sin(phase * math.pi) * leg_amp
        angle_r = -angle_l
        bob_z = -abs(math.sin(phase * math.pi)) * 0.05
        sway_x = math.sin(phase * math.pi) * 0.03
        
        apply_pose_keyframe(amt_obj, "Hips", frame, loc=Vector((sway_x, 0, bob_z)))
        apply_pose_keyframe(amt_obj, "Thigh.L", frame, rot_euler=Euler((math.radians(angle_l), 0, 0)))
        apply_pose_keyframe(amt_obj, "Thigh.R", frame, rot_euler=Euler((math.radians(angle_r), 0, 0)))
        apply_pose_keyframe(amt_obj, "Shin.L", frame, rot_euler=Euler((math.radians(max(0, -angle_l * 0.8)), 0, 0)))
        apply_pose_keyframe(amt_obj, "Shin.R", frame, rot_euler=Euler((math.radians(max(0, -angle_r * 0.8)), 0, 0)))
        
        apply_pose_keyframe(amt_obj, "Chest", frame, rot_euler=Euler((0, 0, math.radians(-sway_x * 50))))
        if char_name == "zombie":
            apply_pose_keyframe(amt_obj, "UpperArm.L", frame, rot_euler=Euler((math.radians(angle_r * 0.8 + 15), 0, 0)))
            apply_pose_keyframe(amt_obj, "UpperArm.R", frame, rot_euler=Euler((math.radians(angle_l * 0.8 + 15), 0, 0)))
        elif char_name == "ranged_skirmisher":
            apply_pose_keyframe(amt_obj, "UpperArm.L", frame, rot_euler=Euler((math.radians(10), 0, 0)))
            apply_pose_keyframe(amt_obj, "UpperArm.R", frame, rot_euler=Euler((math.radians(angle_l * 0.6), 0, 0)))
        elif char_name == "siege_breaker":
            apply_pose_keyframe(amt_obj, "UpperArm.L", frame, rot_euler=Euler((math.radians(angle_r * 0.7), math.radians(5), 0)))
            apply_pose_keyframe(amt_obj, "UpperArm.R", frame, rot_euler=Euler((math.radians(angle_l * 0.7), math.radians(-5), 0)))
    actions.append(act_move)

    # -------------------------------------------------------------
    # ACTION 3: ATTACK (role specific attack semantics)
    # -------------------------------------------------------------
    act_attack = bpy.data.actions.new(name="attack")
    amt_obj.animation_data.action = act_attack
    reset_pose(amt_obj)

    if char_name == "zombie":
        # Fast claw swipe
        apply_pose_keyframe(amt_obj, "Chest", 0, rot_euler=Euler((0, 0, 0)))
        apply_pose_keyframe(amt_obj, "UpperArm.R", 0, rot_euler=Euler((0, 0, 0)))
        apply_pose_keyframe(amt_obj, "Forearm.R", 0, rot_euler=Euler((0, 0, 0)))

        apply_pose_keyframe(amt_obj, "Chest", 12, rot_euler=Euler((math.radians(-15), math.radians(5), math.radians(20))))
        apply_pose_keyframe(amt_obj, "UpperArm.R", 12, rot_euler=Euler((math.radians(-40), math.radians(-20), math.radians(25))))
        apply_pose_keyframe(amt_obj, "Forearm.R", 12, rot_euler=Euler((math.radians(-30), 0, 0)))

        apply_pose_keyframe(amt_obj, "Chest", 20, rot_euler=Euler((math.radians(25), math.radians(-5), math.radians(-25))))
        apply_pose_keyframe(amt_obj, "UpperArm.R", 20, rot_euler=Euler((math.radians(65), math.radians(10), math.radians(-30))))
        apply_pose_keyframe(amt_obj, "Forearm.R", 20, rot_euler=Euler((math.radians(40), 0, 0)))

        apply_pose_keyframe(amt_obj, "Chest", 28, rot_euler=Euler((math.radians(15), 0, math.radians(-15))))
        apply_pose_keyframe(amt_obj, "UpperArm.R", 28, rot_euler=Euler((math.radians(45), 0, math.radians(-15))))

        apply_pose_keyframe(amt_obj, "Chest", 40, rot_euler=Euler((0, 0, 0)))
        apply_pose_keyframe(amt_obj, "UpperArm.R", 40, rot_euler=Euler((0, 0, 0)))
        apply_pose_keyframe(amt_obj, "Forearm.R", 40, rot_euler=Euler((0, 0, 0)))

    elif char_name == "ranged_skirmisher":
        # Draw bow, hold, snap release
        apply_pose_keyframe(amt_obj, "UpperArm.L", 0, rot_euler=Euler((0, 0, 0)))
        apply_pose_keyframe(amt_obj, "UpperArm.R", 0, rot_euler=Euler((0, 0, 0)))
        apply_pose_keyframe(amt_obj, "Forearm.R", 0, rot_euler=Euler((0, 0, 0)))

        apply_pose_keyframe(amt_obj, "Chest", 10, rot_euler=Euler((0, 0, math.radians(-15))))
        apply_pose_keyframe(amt_obj, "UpperArm.L", 10, rot_euler=Euler((math.radians(60), math.radians(10), 0)))
        apply_pose_keyframe(amt_obj, "UpperArm.R", 10, rot_euler=Euler((math.radians(-30), math.radians(-20), 0)))

        apply_pose_keyframe(amt_obj, "Chest", 18, rot_euler=Euler((0, 0, math.radians(-25))))
        apply_pose_keyframe(amt_obj, "UpperArm.L", 18, rot_euler=Euler((math.radians(75), math.radians(15), 0)))
        apply_pose_keyframe(amt_obj, "UpperArm.R", 18, rot_euler=Euler((math.radians(40), math.radians(-35), math.radians(20))))
        apply_pose_keyframe(amt_obj, "Forearm.R", 18, rot_euler=Euler((math.radians(85), 0, 0)))

        apply_pose_keyframe(amt_obj, "Chest", 23, rot_euler=Euler((0, 0, math.radians(-25))))
        apply_pose_keyframe(amt_obj, "UpperArm.L", 23, rot_euler=Euler((math.radians(75), math.radians(15), 0)))
        apply_pose_keyframe(amt_obj, "UpperArm.R", 23, rot_euler=Euler((math.radians(40), math.radians(-35), math.radians(20))))
        apply_pose_keyframe(amt_obj, "Forearm.R", 23, rot_euler=Euler((math.radians(85), 0, 0)))

        apply_pose_keyframe(amt_obj, "UpperArm.L", 25, rot_euler=Euler((math.radians(80), math.radians(12), 0)))
        apply_pose_keyframe(amt_obj, "UpperArm.R", 25, rot_euler=Euler((math.radians(20), math.radians(-50), math.radians(10))))
        apply_pose_keyframe(amt_obj, "Forearm.R", 25, rot_euler=Euler((math.radians(30), 0, 0)))

        apply_pose_keyframe(amt_obj, "Chest", 40, rot_euler=Euler((0, 0, 0)))
        apply_pose_keyframe(amt_obj, "UpperArm.L", 40, rot_euler=Euler((0, 0, 0)))
        apply_pose_keyframe(amt_obj, "UpperArm.R", 40, rot_euler=Euler((0, 0, 0)))
        apply_pose_keyframe(amt_obj, "Forearm.R", 40, rot_euler=Euler((0, 0, 0)))

    elif char_name == "siege_breaker":
        # Heavy two-handed downward ground smash
        apply_pose_keyframe(amt_obj, "Chest", 0, rot_euler=Euler((0, 0, 0)))
        apply_pose_keyframe(amt_obj, "UpperArm.L", 0, rot_euler=Euler((0, 0, 0)))
        apply_pose_keyframe(amt_obj, "UpperArm.R", 0, rot_euler=Euler((0, 0, 0)))

        apply_pose_keyframe(amt_obj, "Hips", 15, loc=Vector((0, 0, 0.08)))
        apply_pose_keyframe(amt_obj, "Chest", 15, rot_euler=Euler((math.radians(-25), 0, 0)))
        apply_pose_keyframe(amt_obj, "UpperArm.L", 15, rot_euler=Euler((math.radians(-110), math.radians(20), 0)))
        apply_pose_keyframe(amt_obj, "UpperArm.R", 15, rot_euler=Euler((math.radians(-110), math.radians(-20), 0)))
        apply_pose_keyframe(amt_obj, "Forearm.L", 15, rot_euler=Euler((math.radians(50), 0, 0)))
        apply_pose_keyframe(amt_obj, "Forearm.R", 15, rot_euler=Euler((math.radians(50), 0, 0)))

        apply_pose_keyframe(amt_obj, "Chest", 24, rot_euler=Euler((math.radians(-28), 0, 0)))

        apply_pose_keyframe(amt_obj, "Hips", 28, loc=Vector((0, 0, -0.15)))
        apply_pose_keyframe(amt_obj, "Chest", 28, rot_euler=Euler((math.radians(35), 0, 0)))
        apply_pose_keyframe(amt_obj, "UpperArm.L", 28, rot_euler=Euler((math.radians(55), math.radians(10), 0)))
        apply_pose_keyframe(amt_obj, "UpperArm.R", 28, rot_euler=Euler((math.radians(55), math.radians(-10), 0)))
        apply_pose_keyframe(amt_obj, "Forearm.L", 28, rot_euler=Euler((math.radians(20), 0, 0)))
        apply_pose_keyframe(amt_obj, "Forearm.R", 28, rot_euler=Euler((math.radians(20), 0, 0)))

        apply_pose_keyframe(amt_obj, "Chest", 36, rot_euler=Euler((math.radians(30), 0, 0)))

        apply_pose_keyframe(amt_obj, "Hips", 45, loc=Vector((0, 0, 0)))
        apply_pose_keyframe(amt_obj, "Chest", 45, rot_euler=Euler((0, 0, 0)))
        apply_pose_keyframe(amt_obj, "UpperArm.L", 45, rot_euler=Euler((0, 0, 0)))
        apply_pose_keyframe(amt_obj, "UpperArm.R", 45, rot_euler=Euler((0, 0, 0)))
        apply_pose_keyframe(amt_obj, "Forearm.L", 45, rot_euler=Euler((0, 0, 0)))
        apply_pose_keyframe(amt_obj, "Forearm.R", 45, rot_euler=Euler((0, 0, 0)))
    actions.append(act_attack)

    # -------------------------------------------------------------
    # ACTION 4: HIT / REACTION (15 frames)
    # -------------------------------------------------------------
    act_hit = bpy.data.actions.new(name="hit")
    amt_obj.animation_data.action = act_hit
    reset_pose(amt_obj)

    apply_pose_keyframe(amt_obj, "Hips", 0, loc=Vector((0, 0, 0)))
    apply_pose_keyframe(amt_obj, "Chest", 0, rot_euler=Euler((0, 0, 0)))
    apply_pose_keyframe(amt_obj, "Head", 0, rot_euler=Euler((0, 0, 0)))

    hit_recoil = -18.0 if char_name != "siege_breaker" else -8.0
    apply_pose_keyframe(amt_obj, "Hips", 4, loc=Vector((0, -0.08, -0.02)))
    apply_pose_keyframe(amt_obj, "Chest", 4, rot_euler=Euler((math.radians(hit_recoil), 0, 0)))
    apply_pose_keyframe(amt_obj, "Head", 4, rot_euler=Euler((math.radians(hit_recoil * 1.2), 0, 0)))

    apply_pose_keyframe(amt_obj, "Hips", 15, loc=Vector((0, 0, 0)))
    apply_pose_keyframe(amt_obj, "Chest", 15, rot_euler=Euler((0, 0, 0)))
    apply_pose_keyframe(amt_obj, "Head", 15, rot_euler=Euler((0, 0, 0)))
    actions.append(act_hit)

    # -------------------------------------------------------------
    # ACTION 5: DEATH (40 frames)
    # -------------------------------------------------------------
    act_death = bpy.data.actions.new(name="death")
    amt_obj.animation_data.action = act_death
    reset_pose(amt_obj)

    apply_pose_keyframe(amt_obj, "Hips", 0, loc=Vector((0, 0, 0)), rot_euler=Euler((0, 0, 0)))
    apply_pose_keyframe(amt_obj, "Chest", 0, rot_euler=Euler((0, 0, 0)))

    apply_pose_keyframe(amt_obj, "Hips", 10, loc=Vector((0, -0.05, -0.15)), rot_euler=Euler((math.radians(10), 0, 0)))
    apply_pose_keyframe(amt_obj, "Chest", 10, rot_euler=Euler((math.radians(20), 0, 0)))

    drop_z = -0.75 if char_name != "siege_breaker" else -1.05
    apply_pose_keyframe(amt_obj, "Hips", 25, loc=Vector((0, 0.20, drop_z)), rot_euler=Euler((math.radians(50), 0, 0)))
    apply_pose_keyframe(amt_obj, "Chest", 25, rot_euler=Euler((math.radians(35), 0, 0)))
    apply_pose_keyframe(amt_obj, "Head", 25, rot_euler=Euler((math.radians(40), 0, 0)))

    apply_pose_keyframe(amt_obj, "Hips", 40, loc=Vector((0, 0.40, drop_z - 0.12)), rot_euler=Euler((math.radians(85), 0, 0)))
    apply_pose_keyframe(amt_obj, "Chest", 40, rot_euler=Euler((math.radians(10), 0, 0)))
    apply_pose_keyframe(amt_obj, "Head", 40, rot_euler=Euler((math.radians(10), 0, 0)))
    actions.append(act_death)

    # Reset to rest pose
    reset_pose(amt_obj)
    amt_obj.animation_data.action = None

    # Push all actions to NLA tracks for complete GLB export
    for act in actions:
        track = amt_obj.animation_data.nla_tracks.new()
        track.name = act.name
        # Keep track muted during rest pose setup
        track.mute = True
        strip = track.strips.new(act.name, 1, act)
        strip.action = act

    return actions


# =============================================================================
# 5. REVIEW RENDERING & FILMSTRIPS
# =============================================================================

def render_camera_view(filepath: Path, cam: bpy.types.Object, location: Vector, target: Vector, ortho: bool, scale_or_fov: float, res: tuple[int, int] = (640, 640)):
    cam.location = location
    core.look_at(cam, target)
    if ortho:
        cam.data.type = "ORTHO"
        cam.data.ortho_scale = scale_or_fov
    else:
        cam.data.type = "PERSP"
        cam.data.angle = math.radians(scale_or_fov)
        
    scene = bpy.context.scene
    scene.render.resolution_x = res[0]
    scene.render.resolution_y = res[1]
    scene.render.filepath = str(filepath.resolve())
    bpy.ops.render.render(write_still=True)


def build_and_render_package(asset_dir: Path):
    char_name = asset_dir.name
    print(f"Building character package: {char_name} in {asset_dir}")
    core.clear_scene()
    scene = bpy.context.scene
    scene.render.fps = 30
    scene.render.fps_base = 1.0

    spec_path = asset_dir / "source" / "character_spec.json"
    if spec_path.is_file():
        print(f"Loading authored specification: {spec_path}")
        spec = json.loads(spec_path.read_text(encoding="utf-8"))
        materials = [
            core.create_pbr_material(m["name"], m["color_hex"], m.get("roughness", 0.85), m.get("metallic", 0.0))
            for m in spec["materials"]
        ]
        amt_obj = core.create_armature(f"{char_name}_Armature", spec["bones"])

        bm = bmesh.new()
        weights: dict[str, list[int]] = {}
        for box in spec["boxes"]:
            core.add_box_geometry(
                bm,
                tuple(box["center"]),
                tuple(box["size"]),
                box["bone"],
                weights,
                mat_index=box["mat_index"],
                rot=tuple(box.get("rot", (0, 0, 0))),
            )
    else:
        # Fallback to programmatic generator
        if char_name == "zombie":
            materials = [
                core.create_pbr_material("mat_decay_flesh", "#84946e", roughness=0.88),
                core.create_pbr_material("mat_pale_flesh", "#9baa84", roughness=0.85),
                core.create_pbr_material("mat_tattered_cloth", "#524032", roughness=0.92),
                core.create_pbr_material("mat_bone_teeth", "#cfc8b6", roughness=0.75),
                core.create_pbr_material("mat_dark_socket", "#1c221a", roughness=1.0),
            ]
            bone_defs = get_zombie_bone_defs()
            mesh_builder = build_zombie_mesh
        elif char_name == "ranged_skirmisher":
            materials = [
                core.create_pbr_material("mat_bone_weathered", "#cfc4a6", roughness=0.80),
                core.create_pbr_material("mat_bone_dark", "#9c9276", roughness=0.82),
                core.create_pbr_material("mat_ragged_leather", "#4e392a", roughness=0.90),
                core.create_pbr_material("mat_bow_wood", "#683e20", roughness=0.75),
                core.create_pbr_material("mat_bow_string", "#e8e2d4", roughness=0.60),
                core.create_pbr_material("mat_dark_socket", "#181816", roughness=1.0),
            ]
            bone_defs = get_skirmisher_bone_defs()
            mesh_builder = build_skirmisher_mesh
        elif char_name == "siege_breaker":
            materials = [
                core.create_pbr_material("mat_decay_brute_flesh", "#54624d", roughness=0.88),
                core.create_pbr_material("mat_corrupted_stone", "#42484f", roughness=0.95),
                core.create_pbr_material("mat_iron_plate", "#2c2f34", roughness=0.55, metallic=0.5),
                core.create_pbr_material("mat_bone_armor", "#cfc5ae", roughness=0.80),
                core.create_pbr_material("mat_ragged_loincloth", "#4e2b24", roughness=0.92),
            ]
            bone_defs = get_siege_breaker_bone_defs()
            mesh_builder = build_siege_breaker_mesh
        else:
            raise ValueError(f"Unknown character type: {char_name}")

        # 1. Armature (oriented facing -Y standard front direction)
        rot_mat = Matrix.Rotation(math.pi, 3, 'Z')
        rotated_bone_defs = {}
        for b_name, b_info in bone_defs.items():
            new_info = dict(b_info)
            new_info["head"] = tuple(rot_mat @ Vector(b_info["head"]))
            new_info["tail"] = tuple(rot_mat @ Vector(b_info["tail"]))
            rotated_bone_defs[b_name] = new_info

        amt_obj = core.create_armature(f"{char_name}_Armature", rotated_bone_defs)

        # 2. Geometry
        bm = bmesh.new()
        weights: dict[str, list[int]] = {}
        mesh_builder(bm, weights)
        # Rotate mesh geometry to face -Y (standard front)
        bmesh.ops.rotate(bm, cent=(0, 0, 0), matrix=Matrix.Rotation(math.pi, 4, 'Z'), verts=bm.verts)

    mesh = bpy.data.meshes.new(f"{char_name}_Mesh")
    bm.to_mesh(mesh)
    bm.free()

    mesh_obj = bpy.data.objects.new("Body", mesh)
    bpy.context.collection.objects.link(mesh_obj)
    for mat in materials:
        mesh_obj.data.materials.append(mat)

    core.bind_mesh_to_armature(mesh_obj, amt_obj, weights)

    # 3. Actions / Animations
    actions = create_character_actions(char_name, amt_obj)

    # 4. Save canonical source .blend
    source_dir = asset_dir / "source"
    source_dir.mkdir(parents=True, exist_ok=True)
    blend_path = source_dir / "model.blend"
    bpy.ops.wm.save_as_mainfile(filepath=str(blend_path.resolve()))
    print(f"Saved source blend: {blend_path}")

    # 5. Export GLB
    output_dir = asset_dir / "output"
    output_dir.mkdir(parents=True, exist_ok=True)
    glb_path = output_dir / "model.glb"
    
    bpy.ops.object.select_all(action="DESELECT")
    amt_obj.select_set(True)
    mesh_obj.select_set(True)
    bpy.context.view_layer.objects.active = amt_obj

    # Unmute all NLA tracks so that GLB exporter includes all 5 actions
    for trk in amt_obj.animation_data.nla_tracks:
        trk.mute = False

    bpy.ops.export_scene.gltf(
        filepath=str(glb_path.resolve()),
        export_format="GLB",
        use_selection=True,
        export_yup=True,
        export_materials="EXPORT",
        export_animations=True,
        export_skins=True,
        export_all_influences=True,
        export_nla_strips=True,
        export_def_bones=True,
    )
    print(f"Exported runtime GLB: {glb_path}")

    # Mute NLA tracks back for isolated rendering
    for trk in amt_obj.animation_data.nla_tracks:
        trk.mute = True

    # 6. Render Review Views
    review_dir = asset_dir / "review"
    review_dir.mkdir(parents=True, exist_ok=True)

    ground = core.add_ground_plane(size=30.0)
    core.setup_lights()

    cam_data = bpy.data.cameras.new("ReviewCam")
    cam = bpy.data.objects.new("ReviewCam", cam_data)
    bpy.context.collection.objects.link(cam)
    bpy.context.scene.camera = cam

    scene = bpy.context.scene
    scene.render.engine = core.get_eevee_engine()
    scene.render.image_settings.file_format = "PNG"
    scene.render.resolution_percentage = 100
    scene.render.film_transparent = False
    scene.render.dither_intensity = 0.0
    scene.render.filter_size = 1.25
    if hasattr(scene, "eevee"):
        if hasattr(scene.eevee, "taa_render_samples"):
            scene.eevee.taa_render_samples = 512
        if hasattr(scene.eevee, "shadow_step_count"):
            scene.eevee.shadow_step_count = 1
        if hasattr(scene.eevee, "shadow_ray_count"):
            scene.eevee.shadow_ray_count = 1
    scene.world.color = (0.05, 0.055, 0.065)

    char_h = 2.45 if char_name == "siege_breaker" else 1.82
    center_z = char_h / 2.0
    center = Vector((0, 0, center_z))
    ortho_scale = char_h * 1.55

    # Reset to rest pose for turnaround
    reset_pose(amt_obj)
    amt_obj.animation_data.action = None

    # Orthographic model turnaround views (clean background without floor shadow noise)
    ground.hide_render = True
    render_camera_view(review_dir / "front.png", cam, Vector((0, -char_h * 2.8, center_z)), center, ortho=True, scale_or_fov=ortho_scale)
    render_camera_view(review_dir / "side.png", cam, Vector((char_h * 2.8, 0, center_z)), center, ortho=True, scale_or_fov=ortho_scale)
    render_camera_view(review_dir / "top.png", cam, Vector((0, 0, char_h * 3.5)), center, ortho=True, scale_or_fov=ortho_scale)
    render_camera_view(review_dir / "iso.png", cam, Vector((char_h * 2.2, -char_h * 2.2, char_h * 1.9)), center, ortho=True, scale_or_fov=ortho_scale)

    # Gameplay (Godot CameraMath: FOV 45, angle (15, 20, 15) with ground plane)
    ground.hide_render = False
    render_camera_view(review_dir / "gameplay.png", cam, Vector((7.5, -7.5, 10.0)), center, ortho=False, scale_or_fov=45.0, res=(1280, 720))

    # Silhouette (pure black against pure white, shadows hidden)
    # Record original polygon material indices to guarantee non-destructive pass (EVID-01)
    original_polygon_mat_indices = [p.material_index for p in mesh_obj.data.polygons]
    original_materials = list(mesh_obj.data.materials)

    mat_black = core.create_pbr_material("mat_black", "#010101", roughness=1.0)
    bpy.context.view_layer.material_override = mat_black
    ground.hide_render = True
    scene.world.color = (1.0, 1.0, 1.0)
    render_camera_view(review_dir / "silhouette.png", cam, Vector((0, -char_h * 2.8, center_z)), center, ortho=True, scale_or_fov=ortho_scale)
    
    # Restore materials override & background
    bpy.context.view_layer.material_override = None
    ground.hide_render = False
    scene.world.color = (0.05, 0.055, 0.065)

    # Verification: assert polygon material assignments remain strictly identical before and after silhouette pass
    current_polygon_mat_indices = [p.material_index for p in mesh_obj.data.polygons]
    assert current_polygon_mat_indices == original_polygon_mat_indices, (
        "EVID-01 violation: polygon material indices altered during silhouette pass!"
    )
    assert list(mesh_obj.data.materials) == original_materials, (
        "EVID-01 violation: mesh materials altered during silhouette pass!"
    )

    # Material closeup
    closeup_target = Vector((0, 0, char_h * 0.72))
    render_camera_view(review_dir / "material_closeup.png", cam, Vector((char_h * 0.6, -char_h * 0.8, char_h * 0.9)), closeup_target, ortho=False, scale_or_fov=35.0)

    # Animation filmstrips
    anim_frames = {
        "idle": [0, 15, 30, 45, 60],
        "move": [0, 7, 15, 22, 30],
        "attack": [0, 10, 20, 28, 40] if char_name != "siege_breaker" else [0, 15, 24, 28, 45],
        "hit": [0, 4, 8, 12, 15],
        "death": [0, 10, 20, 30, 40],
    }

    temp_dir = review_dir / "_temp_frames"
    temp_dir.mkdir(parents=True, exist_ok=True)
    for act in actions:
        amt_obj.animation_data.action = act
        frames = anim_frames.get(act.name, [0, 10, 20, 30])
        for f in frames:
            scene.frame_set(f)
            frame_path = temp_dir / f"{act.name}_f{f:02d}.png"
            render_camera_view(frame_path, cam, Vector((char_h * 1.8, -char_h * 1.8, char_h * 1.5)), center, ortho=True, scale_or_fov=ortho_scale, res=(512, 512))
        print(f"Rendered frames for {act.name}: {frames}")

    scene.frame_set(0)
    amt_obj.animation_data.action = None

    # 7. Metrics (computed dynamically from actual scene.render.fps)
    fps = scene.render.fps
    attack_frames = 45 if char_name == "siege_breaker" else 40
    contact_frame = 25 if char_name == "ranged_skirmisher" else (20 if char_name == "zombie" else 28)
    tris = sum(len(p.vertices) - 2 for p in mesh_obj.data.polygons)
    metrics = {
        "character": char_name,
        "triangles": tris,
        "materials": len(original_materials),
        "bones": len(amt_obj.data.bones),
        "animations": [act.name for act in actions],
        "animation_details": {
            "idle": {"frames": 60, "fps": fps, "duration_sec": round(60.0 / fps, 2), "loop": True},
            "move": {"frames": 30, "fps": fps, "duration_sec": round(30.0 / fps, 2), "loop": True, "in_place": True},
            "attack": {
                "frames": attack_frames,
                "fps": fps,
                "duration_sec": round(float(attack_frames) / fps, 2),
                "loop": False,
                "contact_or_release_frame": contact_frame,
            },
            "hit": {"frames": 15, "fps": fps, "duration_sec": round(15.0 / fps, 2), "loop": False},
            "death": {"frames": 40, "fps": fps, "duration_sec": round(40.0 / fps, 2), "loop": False},
        },
        "dimensions": {
            "x": round(mesh_obj.dimensions.x, 3),
            "y": round(mesh_obj.dimensions.y, 3),
            "z": round(mesh_obj.dimensions.z, 3),
        },
        "pivot": "bottom-center (0, 0, 0)",
        "glb_size_bytes": os.path.getsize(glb_path),
        "blender_version": bpy.app.version_string,
        "render_engine": core.get_eevee_engine(),
    }
    metrics_path = review_dir / "metrics.json"
    metrics_path.write_text(json.dumps(metrics, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Metrics: {metrics}")


if __name__ == "__main__":
    args = parse_args()
    build_and_render_package(args.asset)

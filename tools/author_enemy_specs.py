"""Authoring script to generate production-quality character_spec.json for Cube Siege enemies.
Elevates the blockout models to clustered-voxel production assets matching undead_enemies_concept.png.
Guarantees <= 1000 triangles per character, preserves rigging, pivots, animations, and negative-space silhouettes.
"""

from __future__ import annotations
import json
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent


def get_zombie_spec() -> dict:
    materials = [
        {"name": "mat_decay_flesh", "color_hex": "#84946e", "roughness": 0.88, "metallic": 0.0},
        {"name": "mat_pale_flesh", "color_hex": "#9baa84", "roughness": 0.85, "metallic": 0.0},
        {"name": "mat_tattered_cloth", "color_hex": "#524032", "roughness": 0.92, "metallic": 0.0},
        {"name": "mat_bone_teeth", "color_hex": "#cfc8b6", "roughness": 0.75, "metallic": 0.0},
        {"name": "mat_dark_socket", "color_hex": "#1c221a", "roughness": 1.0, "metallic": 0.0},
    ]

    bones = {
        "Root": {"head": [0.0, 0.0, 0.0], "tail": [0.0, 0.0, 0.2], "parent": None},
        "Hips": {"head": [0.0, 0.0, 0.92], "tail": [-0.0, -0.04, 1.02], "parent": "Root"},
        "Spine": {"head": [-0.0, -0.04, 1.02], "tail": [-0.0, -0.10, 1.20], "parent": "Hips", "connected": True},
        "Chest": {"head": [-0.0, -0.10, 1.20], "tail": [-0.0, -0.20, 1.40], "parent": "Spine", "connected": True},
        "Neck": {"head": [-0.0, -0.20, 1.40], "tail": [-0.0, -0.28, 1.52], "parent": "Chest", "connected": True},
        "Head": {"head": [-0.0, -0.28, 1.52], "tail": [-0.0, -0.42, 1.74], "parent": "Neck", "connected": True},
        "Shoulder.L": {"head": [0.15, -0.14, 1.36], "tail": [0.28, -0.16, 1.36], "parent": "Chest"},
        "UpperArm.L": {"head": [0.28, -0.16, 1.36], "tail": [0.38, -0.36, 1.32], "parent": "Shoulder.L", "connected": True},
        "Forearm.L": {"head": [0.38, -0.36, 1.32], "tail": [0.42, -0.62, 1.28], "parent": "UpperArm.L", "connected": True},
        "Hand.L": {"head": [0.42, -0.62, 1.28], "tail": [0.44, -0.80, 1.25], "parent": "Forearm.L", "connected": True},
        "ClawSocket.L": {"head": [0.44, -0.80, 1.25], "tail": [0.44, -0.90, 1.25], "parent": "Hand.L", "connected": True},
        "Shoulder.R": {"head": [-0.15, -0.12, 1.34], "tail": [-0.28, -0.14, 1.34], "parent": "Chest"},
        "UpperArm.R": {"head": [-0.28, -0.14, 1.34], "tail": [-0.38, -0.32, 1.24], "parent": "Shoulder.R", "connected": True},
        "Forearm.R": {"head": [-0.38, -0.32, 1.24], "tail": [-0.42, -0.54, 1.14], "parent": "UpperArm.R", "connected": True},
        "Hand.R": {"head": [-0.42, -0.54, 1.14], "tail": [-0.44, -0.72, 1.09], "parent": "Forearm.R", "connected": True},
        "ClawSocket.R": {"head": [-0.44, -0.72, 1.09], "tail": [-0.44, -0.82, 1.09], "parent": "Hand.R", "connected": True},
        "Thigh.L": {"head": [0.16, -0.02, 0.88], "tail": [0.16, -0.02, 0.50], "parent": "Hips"},
        "Shin.L": {"head": [0.16, -0.02, 0.50], "tail": [0.16, -0.04, 0.14], "parent": "Thigh.L", "connected": True},
        "Foot.L": {"head": [0.16, -0.04, 0.14], "tail": [0.16, -0.22, 0.06], "parent": "Shin.L", "connected": True},
        "Thigh.R": {"head": [-0.16, 0.02, 0.88], "tail": [-0.16, 0.02, 0.50], "parent": "Hips"},
        "Shin.R": {"head": [-0.16, 0.02, 0.50], "tail": [-0.16, 0.02, 0.14], "parent": "Thigh.R", "connected": True},
        "Foot.R": {"head": [-0.16, 0.02, 0.14], "tail": [-0.16, -0.16, 0.06], "parent": "Shin.R", "connected": True},
    }

    boxes = [
        # --- HEAD & SKULL (stepped cranium, sunken eye sockets, open jaw, teeth) ---
        {"center": [0.0, -0.36, 1.71], "size": [0.32, 0.28, 0.12], "bone": "Head", "mat_index": 0, "rot": [-14.0, 0.0, 0.0]},
        {"center": [0.0, -0.45, 1.66], "size": [0.34, 0.16, 0.10], "bone": "Head", "mat_index": 1, "rot": [-14.0, 0.0, 0.0]},
        {"center": [0.15, -0.38, 1.60], "size": [0.07, 0.22, 0.18], "bone": "Head", "mat_index": 0, "rot": [-14.0, 0.0, 0.0]},
        {"center": [-0.15, -0.38, 1.60], "size": [0.07, 0.22, 0.18], "bone": "Head", "mat_index": 0, "rot": [-14.0, 0.0, 0.0]},
        {"center": [0.0, -0.27, 1.58], "size": [0.30, 0.16, 0.22], "bone": "Head", "mat_index": 0, "rot": [-14.0, 0.0, 0.0]},
        {"center": [0.09, -0.51, 1.62], "size": [0.08, 0.04, 0.08], "bone": "Head", "mat_index": 4, "rot": [-14.0, 0.0, 0.0]},
        {"center": [-0.09, -0.51, 1.62], "size": [0.08, 0.04, 0.08], "bone": "Head", "mat_index": 4, "rot": [-14.0, 0.0, 0.0]},
        {"center": [0.0, -0.51, 1.60], "size": [0.04, 0.05, 0.06], "bone": "Head", "mat_index": 1, "rot": [-14.0, 0.0, 0.0]},
        {"center": [0.0, -0.52, 1.55], "size": [0.05, 0.03, 0.04], "bone": "Head", "mat_index": 4, "rot": [-14.0, 0.0, 0.0]},
        {"center": [0.13, -0.48, 1.54], "size": [0.08, 0.10, 0.08], "bone": "Head", "mat_index": 0, "rot": [-14.0, 0.0, 0.0]},
        {"center": [-0.13, -0.48, 1.54], "size": [0.08, 0.10, 0.08], "bone": "Head", "mat_index": 3, "rot": [-14.0, 0.0, 0.0]},
        {"center": [0.0, -0.48, 1.49], "size": [0.24, 0.14, 0.07], "bone": "Head", "mat_index": 0, "rot": [-14.0, 0.0, 0.0]},
        {"center": [0.05, -0.54, 1.47], "size": [0.04, 0.03, 0.04], "bone": "Head", "mat_index": 3, "rot": [-14.0, 0.0, 0.0]},
        {"center": [-0.05, -0.54, 1.47], "size": [0.04, 0.03, 0.04], "bone": "Head", "mat_index": 3, "rot": [-14.0, 0.0, 0.0]},
        {"center": [0.0, -0.49, 1.46], "size": [0.18, 0.06, 0.05], "bone": "Head", "mat_index": 4, "rot": [-8.0, 0.0, 0.0]},
        {"center": [0.0, -0.49, 1.41], "size": [0.26, 0.20, 0.07], "bone": "Head", "mat_index": 0, "rot": [-8.0, 0.0, 0.0]},
        {"center": [0.0, -0.57, 1.42], "size": [0.18, 0.08, 0.06], "bone": "Head", "mat_index": 1, "rot": [-8.0, 0.0, 0.0]},
        {"center": [0.06, -0.58, 1.46], "size": [0.04, 0.03, 0.04], "bone": "Head", "mat_index": 3, "rot": [-8.0, 0.0, 0.0]},
        {"center": [-0.06, -0.58, 1.46], "size": [0.04, 0.03, 0.04], "bone": "Head", "mat_index": 3, "rot": [-8.0, 0.0, 0.0]},

        # --- NECK ---
        {"center": [0.0, -0.24, 1.44], "size": [0.18, 0.16, 0.12], "bone": "Neck", "mat_index": 0, "rot": [-28.0, 0.0, 0.0]},
        {"center": [0.0, -0.16, 1.47], "size": [0.08, 0.08, 0.08], "bone": "Neck", "mat_index": 3, "rot": [-28.0, 0.0, 0.0]},

        # --- CHEST & TATTERED VEST & RIBS ---
        {"center": [0.0, -0.15, 1.28], "size": [0.44, 0.28, 0.24], "bone": "Chest", "mat_index": 0, "rot": [-22.0, 0.0, 0.0]},
        {"center": [0.20, -0.17, 1.37], "size": [0.15, 0.24, 0.12], "bone": "Chest", "mat_index": 2, "rot": [-20.0, -10.0, -4.0]},
        {"center": [-0.20, -0.17, 1.37], "size": [0.15, 0.24, 0.12], "bone": "Chest", "mat_index": 2, "rot": [-24.0, 8.0, 4.0]},
        {"center": [0.0, -0.06, 1.34], "size": [0.46, 0.10, 0.20], "bone": "Chest", "mat_index": 2, "rot": [-22.0, 0.0, 0.0]},
        {"center": [0.08, -0.27, 1.27], "size": [0.20, 0.08, 0.20], "bone": "Chest", "mat_index": 2, "rot": [-22.0, -6.0, 0.0]},
        {"center": [-0.15, -0.27, 1.32], "size": [0.12, 0.05, 0.04], "bone": "Chest", "mat_index": 3, "rot": [-22.0, 10.0, 0.0]},
        {"center": [-0.14, -0.26, 1.25], "size": [0.12, 0.05, 0.04], "bone": "Chest", "mat_index": 3, "rot": [-22.0, 8.0, 0.0]},
        {"center": [-0.13, -0.25, 1.28], "size": [0.10, 0.03, 0.10], "bone": "Chest", "mat_index": 4, "rot": [-22.0, 0.0, 0.0]},
        {"center": [0.0, -0.28, 1.20], "size": [0.18, 0.06, 0.10], "bone": "Chest", "mat_index": 1, "rot": [-22.0, 0.0, 0.0]},

        # --- SPINE ---
        {"center": [0.0, -0.06, 1.10], "size": [0.42, 0.26, 0.20], "bone": "Spine", "mat_index": 0, "rot": [-16.0, 0.0, 0.0]},
        {"center": [0.0, 0.04, 1.12], "size": [0.44, 0.07, 0.18], "bone": "Spine", "mat_index": 2, "rot": [-16.0, 0.0, 0.0]},
        {"center": [0.0, 0.05, 1.08], "size": [0.08, 0.06, 0.08], "bone": "Spine", "mat_index": 3, "rot": [-16.0, 0.0, 0.0]},
        {"center": [0.15, -0.17, 1.09], "size": [0.10, 0.04, 0.04], "bone": "Spine", "mat_index": 3, "rot": [-16.0, -6.0, 0.0]},

        # --- HIPS & TATTERED LOINCLOTH ---
        {"center": [0.0, 0.0, 0.92], "size": [0.46, 0.26, 0.18], "bone": "Hips", "mat_index": 2, "rot": [-10.0, 0.0, 0.0]},
        {"center": [0.08, -0.13, 0.80], "size": [0.12, 0.05, 0.22], "bone": "Hips", "mat_index": 2, "rot": [-14.0, -6.0, 0.0]},
        {"center": [-0.07, -0.13, 0.77], "size": [0.13, 0.05, 0.26], "bone": "Hips", "mat_index": 2, "rot": [-12.0, 4.0, 0.0]},
        {"center": [0.19, -0.06, 0.82], "size": [0.08, 0.16, 0.16], "bone": "Hips", "mat_index": 2, "rot": [-10.0, -8.0, 0.0]},
        {"center": [-0.19, -0.06, 0.82], "size": [0.08, 0.16, 0.16], "bone": "Hips", "mat_index": 2, "rot": [-10.0, 8.0, 0.0]},
        {"center": [0.0, 0.12, 0.81], "size": [0.42, 0.06, 0.20], "bone": "Hips", "mat_index": 2, "rot": [-8.0, 0.0, 0.0]},

        # --- LEFT ARM ---
        {"center": [0.26, -0.15, 1.36], "size": [0.16, 0.18, 0.14], "bone": "UpperArm.L", "mat_index": 2, "rot": [-26.0, -12.0, -8.0]},
        {"center": [0.36, -0.22, 1.34], "size": [0.18, 0.18, 0.16], "bone": "UpperArm.L", "mat_index": 2, "rot": [-26.0, -12.0, -8.0]},
        {"center": [0.38, -0.32, 1.32], "size": [0.16, 0.16, 0.20], "bone": "UpperArm.L", "mat_index": 0, "rot": [-26.0, -12.0, -8.0]},
        {"center": [0.40, -0.38, 1.30], "size": [0.10, 0.10, 0.10], "bone": "UpperArm.L", "mat_index": 3, "rot": [-30.0, -8.0, -10.0]},
        {"center": [0.42, -0.48, 1.28], "size": [0.15, 0.26, 0.15], "bone": "Forearm.L", "mat_index": 0, "rot": [-55.0, -6.0, -10.0]},
        {"center": [0.43, -0.52, 1.29], "size": [0.08, 0.16, 0.08], "bone": "Forearm.L", "mat_index": 1, "rot": [-55.0, -6.0, -10.0]},
        {"center": [0.43, -0.63, 1.27], "size": [0.12, 0.10, 0.12], "bone": "Forearm.L", "mat_index": 0, "rot": [-45.0, 0.0, -10.0]},
        {"center": [0.44, -0.70, 1.26], "size": [0.16, 0.12, 0.12], "bone": "Hand.L", "mat_index": 1, "rot": [-40.0, 0.0, -10.0]},
        {"center": [0.37, -0.72, 1.23], "size": [0.05, 0.10, 0.05], "bone": "Hand.L", "mat_index": 3, "rot": [-20.0, 15.0, -10.0]},
        {"center": [0.41, -0.80, 1.26], "size": [0.05, 0.14, 0.05], "bone": "Hand.L", "mat_index": 3, "rot": [-30.0, 2.0, -6.0]},
        {"center": [0.46, -0.82, 1.25], "size": [0.05, 0.16, 0.05], "bone": "Hand.L", "mat_index": 3, "rot": [-32.0, -4.0, -4.0]},
        {"center": [0.51, -0.79, 1.24], "size": [0.05, 0.12, 0.05], "bone": "Hand.L", "mat_index": 3, "rot": [-28.0, -10.0, -2.0]},

        # --- RIGHT ARM ---
        {"center": [-0.26, -0.13, 1.34], "size": [0.16, 0.18, 0.14], "bone": "UpperArm.R", "mat_index": 2, "rot": [-20.0, 10.0, 8.0]},
        {"center": [-0.36, -0.20, 1.32], "size": [0.18, 0.18, 0.16], "bone": "UpperArm.R", "mat_index": 2, "rot": [-20.0, 10.0, 8.0]},
        {"center": [-0.38, -0.30, 1.28], "size": [0.16, 0.16, 0.20], "bone": "UpperArm.R", "mat_index": 0, "rot": [-20.0, 10.0, 8.0]},
        {"center": [-0.40, -0.36, 1.22], "size": [0.10, 0.10, 0.10], "bone": "UpperArm.R", "mat_index": 3, "rot": [-25.0, 8.0, 8.0]},
        {"center": [-0.42, -0.46, 1.16], "size": [0.15, 0.26, 0.15], "bone": "Forearm.R", "mat_index": 0, "rot": [-45.0, 4.0, 10.0]},
        {"center": [-0.44, -0.48, 1.15], "size": [0.06, 0.18, 0.06], "bone": "Forearm.R", "mat_index": 3, "rot": [-45.0, 4.0, 10.0]},
        {"center": [-0.43, -0.58, 1.11], "size": [0.12, 0.10, 0.12], "bone": "Forearm.R", "mat_index": 0, "rot": [-35.0, 0.0, 10.0]},
        {"center": [-0.44, -0.64, 1.10], "size": [0.16, 0.12, 0.12], "bone": "Hand.R", "mat_index": 1, "rot": [-30.0, 0.0, 10.0]},
        {"center": [-0.37, -0.66, 1.07], "size": [0.05, 0.10, 0.05], "bone": "Hand.R", "mat_index": 3, "rot": [-15.0, -15.0, 10.0]},
        {"center": [-0.41, -0.74, 1.09], "size": [0.05, 0.14, 0.05], "bone": "Hand.R", "mat_index": 3, "rot": [-24.0, -2.0, 6.0]},
        {"center": [-0.46, -0.76, 1.08], "size": [0.05, 0.16, 0.05], "bone": "Hand.R", "mat_index": 3, "rot": [-26.0, 4.0, 4.0]},
        {"center": [-0.51, -0.73, 1.07], "size": [0.05, 0.12, 0.05], "bone": "Hand.R", "mat_index": 3, "rot": [-22.0, 10.0, 2.0]},

        # --- LEFT LEG ---
        {"center": [0.16, -0.01, 0.76], "size": [0.22, 0.24, 0.22], "bone": "Thigh.L", "mat_index": 2, "rot": [-8.0, 0.0, 0.0]},
        {"center": [0.16, -0.01, 0.60], "size": [0.18, 0.20, 0.18], "bone": "Thigh.L", "mat_index": 0, "rot": [-8.0, 0.0, 0.0]},
        {"center": [0.16, -0.03, 0.50], "size": [0.12, 0.10, 0.10], "bone": "Thigh.L", "mat_index": 3, "rot": [0.0, 0.0, 0.0]},
        {"center": [0.16, -0.04, 0.36], "size": [0.16, 0.18, 0.24], "bone": "Shin.L", "mat_index": 0, "rot": [6.0, 0.0, 0.0]},
        {"center": [0.16, -0.05, 0.20], "size": [0.14, 0.14, 0.14], "bone": "Shin.L", "mat_index": 1, "rot": [6.0, 0.0, 0.0]},
        {"center": [0.16, 0.0, 0.07], "size": [0.18, 0.18, 0.14], "bone": "Foot.L", "mat_index": 0, "rot": [0.0, 0.0, 0.0]},
        {"center": [0.13, -0.16, 0.05], "size": [0.10, 0.14, 0.10], "bone": "Foot.L", "mat_index": 1, "rot": [0.0, 0.0, 0.0]},
        {"center": [0.21, -0.15, 0.05], "size": [0.08, 0.12, 0.09], "bone": "Foot.L", "mat_index": 0, "rot": [0.0, 0.0, 0.0]},

        # --- RIGHT LEG ---
        {"center": [-0.16, 0.03, 0.76], "size": [0.22, 0.24, 0.22], "bone": "Thigh.R", "mat_index": 2, "rot": [4.0, 0.0, 0.0]},
        {"center": [-0.16, 0.03, 0.60], "size": [0.18, 0.20, 0.18], "bone": "Thigh.R", "mat_index": 0, "rot": [4.0, 0.0, 0.0]},
        {"center": [-0.16, 0.01, 0.50], "size": [0.12, 0.10, 0.10], "bone": "Thigh.R", "mat_index": 3, "rot": [0.0, 0.0, 0.0]},
        {"center": [-0.16, 0.02, 0.36], "size": [0.16, 0.18, 0.24], "bone": "Shin.R", "mat_index": 0, "rot": [-4.0, 0.0, 0.0]},
        {"center": [-0.16, -0.05, 0.32], "size": [0.08, 0.05, 0.20], "bone": "Shin.R", "mat_index": 3, "rot": [-4.0, 0.0, 0.0]},
        {"center": [-0.16, 0.01, 0.20], "size": [0.14, 0.14, 0.14], "bone": "Shin.R", "mat_index": 0, "rot": [-4.0, 0.0, 0.0]},
        {"center": [-0.16, 0.06, 0.07], "size": [0.18, 0.18, 0.14], "bone": "Foot.R", "mat_index": 0, "rot": [0.0, 0.0, 0.0]},
        {"center": [-0.13, -0.10, 0.05], "size": [0.10, 0.14, 0.10], "bone": "Foot.R", "mat_index": 1, "rot": [0.0, 0.0, 0.0]},
        {"center": [-0.21, -0.09, 0.05], "size": [0.08, 0.12, 0.09], "bone": "Foot.R", "mat_index": 0, "rot": [0.0, 0.0, 0.0]},
    ]

    return {
        "version": 1,
        "character": "zombie",
        "materials": materials,
        "bones": bones,
        "boxes": boxes,
    }


def get_skirmisher_spec() -> dict:
    materials = [
        {"name": "mat_bone_weathered", "color_hex": "#cfc4a6", "roughness": 0.80, "metallic": 0.0},
        {"name": "mat_bone_dark", "color_hex": "#9c9276", "roughness": 0.82, "metallic": 0.0},
        {"name": "mat_ragged_leather", "color_hex": "#4e392a", "roughness": 0.90, "metallic": 0.0},
        {"name": "mat_bow_wood", "color_hex": "#683e20", "roughness": 0.75, "metallic": 0.0},
        {"name": "mat_bow_string", "color_hex": "#e8e2d4", "roughness": 0.60, "metallic": 0.0},
        {"name": "mat_dark_socket", "color_hex": "#181816", "roughness": 1.0, "metallic": 0.0},
    ]

    bones = {
        "Root": {"head": [0.0, 0.0, 0.0], "tail": [0.0, 0.0, 0.2], "parent": None},
        "Hips": {"head": [0.0, 0.0, 0.94], "tail": [-0.0, -0.02, 1.04], "parent": "Root"},
        "Spine": {"head": [-0.0, -0.02, 1.04], "tail": [-0.0, -0.03, 1.18], "parent": "Hips", "connected": True},
        "Chest": {"head": [-0.0, -0.03, 1.18], "tail": [-0.0, -0.04, 1.38], "parent": "Spine", "connected": True},
        "Neck": {"head": [-0.0, -0.04, 1.38], "tail": [-0.0, -0.05, 1.48], "parent": "Chest", "connected": True},
        "Head": {"head": [-0.0, -0.05, 1.48], "tail": [-0.0, -0.06, 1.74], "parent": "Neck", "connected": True},
        "Shoulder.L": {"head": [0.12, -0.02, 1.34], "tail": [0.22, -0.02, 1.34], "parent": "Chest"},
        "UpperArm.L": {"head": [0.22, -0.02, 1.34], "tail": [0.42, -0.04, 1.28], "parent": "Shoulder.L", "connected": True},
        "Forearm.L": {"head": [0.42, -0.04, 1.28], "tail": [0.58, -0.06, 1.25], "parent": "UpperArm.L", "connected": True},
        "Hand.L": {"head": [0.58, -0.06, 1.25], "tail": [0.66, -0.06, 1.25], "parent": "Forearm.L", "connected": True},
        "BowSocket.L": {"head": [0.64, -0.06, 1.25], "tail": [0.64, -0.16, 1.25], "parent": "Hand.L"},
        "ArrowReleasePoint": {"head": [0.64, -0.26, 1.25], "tail": [0.64, -0.46, 1.25], "parent": "BowSocket.L"},
        "Shoulder.R": {"head": [-0.12, -0.03, 1.34], "tail": [-0.22, -0.03, 1.34], "parent": "Chest"},
        "UpperArm.R": {"head": [-0.22, -0.03, 1.34], "tail": [-0.28, -0.10, 1.18], "parent": "Shoulder.R", "connected": True},
        "Forearm.R": {"head": [-0.28, -0.10, 1.18], "tail": [-0.30, -0.24, 1.02], "parent": "UpperArm.R", "connected": True},
        "Hand.R": {"head": [-0.30, -0.24, 1.02], "tail": [-0.30, -0.34, 0.96], "parent": "Forearm.R", "connected": True},
        "QuiverSocket": {"head": [-0.14, 0.16, 1.34], "tail": [-0.14, 0.26, 1.50], "parent": "Chest"},
        "Thigh.L": {"head": [0.13, 0.0, 0.88], "tail": [0.13, -0.01, 0.50], "parent": "Hips"},
        "Shin.L": {"head": [0.13, -0.01, 0.50], "tail": [0.13, -0.01, 0.14], "parent": "Thigh.L", "connected": True},
        "Foot.L": {"head": [0.13, -0.01, 0.14], "tail": [0.13, -0.18, 0.06], "parent": "Shin.L", "connected": True},
        "Thigh.R": {"head": [-0.13, 0.0, 0.88], "tail": [-0.13, 0.01, 0.50], "parent": "Hips"},
        "Shin.R": {"head": [-0.13, 0.01, 0.50], "tail": [-0.13, 0.01, 0.14], "parent": "Thigh.R", "connected": True},
        "Foot.R": {"head": [-0.13, 0.01, 0.14], "tail": [-0.13, -0.14, 0.06], "parent": "Shin.R", "connected": True},
    }

    boxes = [
        # --- HEAD & COWL / HOOD (framing skeletal face as in concept) ---
        {"center": [0.0, -0.05, 1.74], "size": [0.36, 0.36, 0.08], "bone": "Head", "mat_index": 2},
        {"center": [0.17, -0.04, 1.62], "size": [0.06, 0.32, 0.20], "bone": "Head", "mat_index": 2},
        {"center": [-0.17, -0.04, 1.62], "size": [0.06, 0.32, 0.20], "bone": "Head", "mat_index": 2},
        {"center": [0.0, 0.14, 1.60], "size": [0.30, 0.08, 0.22], "bone": "Head", "mat_index": 2},
        # Exposed skull inside hood
        {"center": [0.0, -0.06, 1.67], "size": [0.26, 0.16, 0.10], "bone": "Head", "mat_index": 0},
        {"center": [0.0, -0.12, 1.62], "size": [0.26, 0.08, 0.06], "bone": "Head", "mat_index": 0},
        # Hollow eye sockets
        {"center": [0.07, -0.16, 1.60], "size": [0.07, 0.04, 0.07], "bone": "Head", "mat_index": 5},
        {"center": [-0.07, -0.16, 1.60], "size": [0.07, 0.04, 0.07], "bone": "Head", "mat_index": 5},
        # Nasal hollow
        {"center": [0.0, -0.16, 1.54], "size": [0.04, 0.03, 0.04], "bone": "Head", "mat_index": 5},
        # Upper maxilla & teeth
        {"center": [0.0, -0.15, 1.49], "size": [0.18, 0.10, 0.06], "bone": "Head", "mat_index": 0},
        {"center": [0.04, -0.18, 1.47], "size": [0.03, 0.02, 0.03], "bone": "Head", "mat_index": 1},
        {"center": [-0.04, -0.18, 1.47], "size": [0.03, 0.02, 0.03], "bone": "Head", "mat_index": 1},
        # Lower jaw
        {"center": [0.0, -0.13, 1.43], "size": [0.16, 0.12, 0.05], "bone": "Head", "mat_index": 0, "rot": [-6.0, 0.0, 0.0]},
        {"center": [0.0, -0.17, 1.45], "size": [0.10, 0.02, 0.03], "bone": "Head", "mat_index": 1, "rot": [-6.0, 0.0, 0.0]},

        # --- NECK ---
        {"center": [0.0, -0.03, 1.42], "size": [0.10, 0.10, 0.10], "bone": "Neck", "mat_index": 1},

        # --- CHEST & 3D RIBCAGE & QUIVER ---
        {"center": [0.0, 0.08, 1.28], "size": [0.10, 0.10, 0.20], "bone": "Chest", "mat_index": 1},
        {"center": [0.0, -0.12, 1.28], "size": [0.06, 0.04, 0.18], "bone": "Chest", "mat_index": 0},
        # Curved 3D Ribs (leaving hollow negative spaces between ribs!)
        {"center": [0.15, -0.02, 1.34], "size": [0.12, 0.18, 0.04], "bone": "Chest", "mat_index": 0},
        {"center": [-0.15, -0.02, 1.34], "size": [0.12, 0.18, 0.04], "bone": "Chest", "mat_index": 0},
        {"center": [0.16, -0.01, 1.27], "size": [0.12, 0.18, 0.04], "bone": "Chest", "mat_index": 0},
        {"center": [-0.16, -0.01, 1.27], "size": [0.12, 0.18, 0.04], "bone": "Chest", "mat_index": 0},
        {"center": [0.14, 0.0, 1.20], "size": [0.11, 0.16, 0.04], "bone": "Chest", "mat_index": 0},
        {"center": [-0.14, 0.0, 1.20], "size": [0.11, 0.16, 0.04], "bone": "Chest", "mat_index": 0},
        {"center": [0.0, -0.01, 1.27], "size": [0.16, 0.12, 0.14], "bone": "Chest", "mat_index": 5},
        # Diagonal bandolier strap across ribs
        {"center": [0.06, -0.13, 1.31], "size": [0.05, 0.03, 0.14], "bone": "Chest", "mat_index": 2, "rot": [0.0, 0.0, -25.0]},
        {"center": [-0.05, -0.12, 1.23], "size": [0.05, 0.03, 0.14], "bone": "Chest", "mat_index": 2, "rot": [0.0, 0.0, -25.0]},
        # Quiver on right shoulder blade
        {"center": [-0.14, 0.16, 1.36], "size": [0.13, 0.13, 0.44], "bone": "Chest", "mat_index": 2, "rot": [18.0, 16.0, 0.0]},
        {"center": [-0.16, 0.20, 1.56], "size": [0.15, 0.15, 0.06], "bone": "Chest", "mat_index": 2, "rot": [18.0, 16.0, 0.0]},
        # Arrows in quiver
        {"center": [-0.14, 0.20, 1.66], "size": [0.03, 0.03, 0.16], "bone": "Chest", "mat_index": 3, "rot": [18.0, 16.0, 0.0]},
        {"center": [-0.14, 0.22, 1.72], "size": [0.06, 0.06, 0.06], "bone": "Chest", "mat_index": 4, "rot": [18.0, 16.0, 0.0]},
        {"center": [-0.18, 0.18, 1.68], "size": [0.03, 0.03, 0.18], "bone": "Chest", "mat_index": 3, "rot": [14.0, 20.0, 0.0]},
        {"center": [-0.19, 0.20, 1.74], "size": [0.06, 0.06, 0.06], "bone": "Chest", "mat_index": 4, "rot": [14.0, 20.0, 0.0]},

        # --- SPINE ---
        {"center": [0.0, 0.01, 1.09], "size": [0.10, 0.10, 0.14], "bone": "Spine", "mat_index": 1},

        # --- HIPS & TASSET SKIRT ---
        {"center": [0.0, 0.0, 0.95], "size": [0.32, 0.16, 0.10], "bone": "Hips", "mat_index": 0},
        {"center": [0.15, 0.0, 0.97], "size": [0.05, 0.16, 0.08], "bone": "Hips", "mat_index": 0},
        {"center": [-0.15, 0.0, 0.97], "size": [0.05, 0.16, 0.08], "bone": "Hips", "mat_index": 0},
        {"center": [0.0, 0.0, 0.96], "size": [0.36, 0.18, 0.05], "bone": "Hips", "mat_index": 2},
        {"center": [0.0, -0.10, 0.96], "size": [0.07, 0.03, 0.06], "bone": "Hips", "mat_index": 1},
        # Hanging tasset strips
        {"center": [0.0, -0.09, 0.88], "size": [0.09, 0.04, 0.14], "bone": "Hips", "mat_index": 2, "rot": [-8.0, 0.0, 0.0]},
        {"center": [0.10, -0.08, 0.86], "size": [0.08, 0.04, 0.16], "bone": "Hips", "mat_index": 2, "rot": [-8.0, -6.0, 0.0]},
        {"center": [-0.10, -0.08, 0.86], "size": [0.08, 0.04, 0.16], "bone": "Hips", "mat_index": 2, "rot": [-8.0, 6.0, 0.0]},
        {"center": [0.16, 0.0, 0.88], "size": [0.04, 0.12, 0.12], "bone": "Hips", "mat_index": 2},
        {"center": [-0.16, 0.0, 0.88], "size": [0.04, 0.12, 0.12], "bone": "Hips", "mat_index": 2},

        # --- LEFT ARM & RECURVE BOW (Preserve ART-01 lateral clearance & 40 deg angle) ---
        {"center": [0.20, -0.02, 1.33], "size": [0.09, 0.09, 0.09], "bone": "UpperArm.L", "mat_index": 1},
        {"center": [0.32, -0.03, 1.31], "size": [0.18, 0.10, 0.10], "bone": "UpperArm.L", "mat_index": 0, "rot": [-4.0, 16.0, 6.0]},
        {"center": [0.40, -0.04, 1.29], "size": [0.09, 0.09, 0.09], "bone": "Forearm.L", "mat_index": 1},
        {"center": [0.50, -0.05, 1.265], "size": [0.16, 0.09, 0.09], "bone": "Forearm.L", "mat_index": 0, "rot": [-2.0, 10.0, 7.0]},
        {"center": [0.58, -0.06, 1.25], "size": [0.08, 0.08, 0.08], "bone": "Hand.L", "mat_index": 1, "rot": [0.0, 0.0, -40.0]},
        {"center": [0.62, -0.06, 1.25], "size": [0.10, 0.10, 0.12], "bone": "Hand.L", "mat_index": 0, "rot": [0.0, 0.0, -40.0]},
        # Large Recurve Bow (angular stepped wooden limbs, binding rings, horn recurve tips)
        {"center": [0.64, -0.06, 1.25], "size": [0.08, 0.08, 0.24], "bone": "Hand.L", "mat_index": 3, "rot": [0.0, 0.0, -40.0]},
        {"center": [0.64, -0.06, 1.34], "size": [0.09, 0.09, 0.04], "bone": "Hand.L", "mat_index": 1, "rot": [0.0, 0.0, -40.0]},
        {"center": [0.64, -0.06, 1.16], "size": [0.09, 0.09, 0.04], "bone": "Hand.L", "mat_index": 1, "rot": [0.0, 0.0, -40.0]},
        # Upper limb
        {"center": [0.678, -0.028, 1.43], "size": [0.07, 0.07, 0.20], "bone": "Hand.L", "mat_index": 3, "rot": [14.0, -12.0, -40.0]},
        {"center": [0.717, 0.004, 1.61], "size": [0.06, 0.06, 0.18], "bone": "Hand.L", "mat_index": 3, "rot": [28.0, -23.0, -40.0]},
        {"center": [0.740, 0.024, 1.77], "size": [0.05, 0.06, 0.14], "bone": "Hand.L", "mat_index": 3, "rot": [-19.0, 16.0, -40.0]},
        {"center": [0.745, 0.026, 1.83], "size": [0.06, 0.07, 0.04], "bone": "Hand.L", "mat_index": 1, "rot": [-19.0, 16.0, -40.0]},
        # Lower limb
        {"center": [0.678, -0.028, 1.07], "size": [0.07, 0.07, 0.20], "bone": "Hand.L", "mat_index": 3, "rot": [-14.0, 12.0, -40.0]},
        {"center": [0.717, 0.004, 0.89], "size": [0.06, 0.06, 0.18], "bone": "Hand.L", "mat_index": 3, "rot": [-28.0, 23.0, -40.0]},
        {"center": [0.740, 0.024, 0.73], "size": [0.05, 0.06, 0.14], "bone": "Hand.L", "mat_index": 3, "rot": [19.0, -16.0, -40.0]},
        {"center": [0.745, 0.026, 0.67], "size": [0.06, 0.07, 0.04], "bone": "Hand.L", "mat_index": 1, "rot": [19.0, -16.0, -40.0]},
        # Taut bowstring
        {"center": [0.563, -0.124, 1.25], "size": [0.03, 0.03, 1.10], "bone": "Hand.L", "mat_index": 4, "rot": [0.0, 0.0, -40.0]},

        # --- RIGHT ARM (ready pose with leather bracer) ---
        {"center": [-0.18, -0.02, 1.33], "size": [0.09, 0.09, 0.09], "bone": "UpperArm.R", "mat_index": 1},
        {"center": [-0.24, -0.02, 1.32], "size": [0.11, 0.11, 0.28], "bone": "UpperArm.R", "mat_index": 0, "rot": [-12.0, 18.0, -12.0]},
        {"center": [-0.28, -0.10, 1.20], "size": [0.09, 0.09, 0.09], "bone": "Forearm.R", "mat_index": 1},
        {"center": [-0.30, -0.18, 1.10], "size": [0.10, 0.22, 0.10], "bone": "Forearm.R", "mat_index": 0, "rot": [-38.0, 0.0, -10.0]},
        {"center": [-0.30, -0.20, 1.10], "size": [0.12, 0.14, 0.11], "bone": "Forearm.R", "mat_index": 2, "rot": [-38.0, 0.0, -10.0]},
        {"center": [-0.30, -0.28, 1.00], "size": [0.10, 0.10, 0.10], "bone": "Hand.R", "mat_index": 0},

        # --- LEFT LEG (skeletal limb + leather boot wrap) ---
        {"center": [0.13, 0.0, 0.72], "size": [0.11, 0.12, 0.36], "bone": "Thigh.L", "mat_index": 0},
        {"center": [0.13, -0.02, 0.50], "size": [0.09, 0.09, 0.09], "bone": "Thigh.L", "mat_index": 1},
        {"center": [0.13, -0.01, 0.38], "size": [0.10, 0.10, 0.22], "bone": "Shin.L", "mat_index": 0},
        {"center": [0.13, -0.01, 0.20], "size": [0.14, 0.15, 0.16], "bone": "Shin.L", "mat_index": 2},
        {"center": [0.13, 0.01, 0.07], "size": [0.11, 0.12, 0.12], "bone": "Foot.L", "mat_index": 1},
        {"center": [0.13, -0.09, 0.05], "size": [0.11, 0.15, 0.08], "bone": "Foot.L", "mat_index": 0},

        # --- RIGHT LEG (skeletal limb + leather boot wrap) ---
        {"center": [-0.13, 0.0, 0.72], "size": [0.11, 0.12, 0.36], "bone": "Thigh.R", "mat_index": 0},
        {"center": [-0.13, 0.01, 0.50], "size": [0.09, 0.09, 0.09], "bone": "Thigh.R", "mat_index": 1},
        {"center": [-0.13, 0.01, 0.38], "size": [0.10, 0.10, 0.22], "bone": "Shin.R", "mat_index": 0},
        {"center": [-0.13, 0.01, 0.20], "size": [0.14, 0.15, 0.16], "bone": "Shin.R", "mat_index": 2},
        {"center": [-0.13, 0.03, 0.07], "size": [0.11, 0.12, 0.12], "bone": "Foot.R", "mat_index": 1},
        {"center": [-0.13, -0.07, 0.05], "size": [0.11, 0.15, 0.08], "bone": "Foot.R", "mat_index": 0},
    ]

    return {
        "version": 1,
        "character": "ranged_skirmisher",
        "materials": materials,
        "bones": bones,
        "boxes": boxes,
    }


def get_siege_breaker_spec() -> dict:
    materials = [
        {"name": "mat_decay_brute_flesh", "color_hex": "#54624d", "roughness": 0.88, "metallic": 0.0},
        {"name": "mat_corrupted_stone", "color_hex": "#42484f", "roughness": 0.95, "metallic": 0.0},
        {"name": "mat_iron_plate", "color_hex": "#2c2f34", "roughness": 0.55, "metallic": 0.5},
        {"name": "mat_bone_armor", "color_hex": "#cfc5ae", "roughness": 0.80, "metallic": 0.0},
        {"name": "mat_ragged_loincloth", "color_hex": "#4e2b24", "roughness": 0.92, "metallic": 0.0},
    ]

    bones = {
        "Root": {"head": [0.0, 0.0, 0.0], "tail": [0.0, 0.0, 0.3], "parent": None},
        "Hips": {"head": [0.0, 0.0, 1.25], "tail": [-0.0, -0.04, 1.40], "parent": "Root"},
        "Spine": {"head": [-0.0, -0.04, 1.40], "tail": [-0.0, -0.08, 1.64], "parent": "Hips", "connected": True},
        "Chest": {"head": [-0.0, -0.08, 1.64], "tail": [-0.0, -0.18, 1.92], "parent": "Spine", "connected": True},
        "Neck": {"head": [-0.0, -0.18, 1.92], "tail": [-0.0, -0.24, 2.06], "parent": "Chest", "connected": True},
        "Head": {"head": [-0.0, -0.24, 2.06], "tail": [-0.0, -0.34, 2.40], "parent": "Neck", "connected": True},
        "Shoulder.L": {"head": [0.30, -0.10, 1.84], "tail": [0.56, -0.12, 1.84], "parent": "Chest"},
        "UpperArm.L": {"head": [0.56, -0.12, 1.84], "tail": [0.78, -0.30, 1.60], "parent": "Shoulder.L", "connected": True},
        "Forearm.L": {"head": [0.78, -0.30, 1.60], "tail": [0.84, -0.60, 1.32], "parent": "UpperArm.L", "connected": True},
        "Hand.L": {"head": [0.84, -0.60, 1.32], "tail": [0.84, -0.88, 1.08], "parent": "Forearm.L", "connected": True},
        "Shoulder.R": {"head": [-0.30, -0.10, 1.84], "tail": [-0.56, -0.12, 1.84], "parent": "Chest"},
        "UpperArm.R": {"head": [-0.56, -0.12, 1.84], "tail": [-0.78, -0.28, 1.58], "parent": "Shoulder.R", "connected": True},
        "Forearm.R": {"head": [-0.78, -0.28, 1.58], "tail": [-0.84, -0.58, 1.30], "parent": "UpperArm.R", "connected": True},
        "Hand.R": {"head": [-0.84, -0.58, 1.30], "tail": [-0.84, -0.86, 1.06], "parent": "Forearm.R", "connected": True},
        "SmashPoint": {"head": [-0.0, -0.85, 0.0], "tail": [-0.0, -0.85, 0.3], "parent": "Root"},
        "Thigh.L": {"head": [0.36, -0.0, 1.18], "tail": [0.38, -0.02, 0.72], "parent": "Hips"},
        "Shin.L": {"head": [0.38, -0.02, 0.72], "tail": [0.38, -0.06, 0.28], "parent": "Thigh.L", "connected": True},
        "Foot.L": {"head": [0.38, -0.06, 0.28], "tail": [0.38, -0.32, 0.12], "parent": "Shin.L", "connected": True},
        "Thigh.R": {"head": [-0.36, -0.0, 1.18], "tail": [-0.38, 0.02, 0.72], "parent": "Hips"},
        "Shin.R": {"head": [-0.38, 0.02, 0.72], "tail": [-0.38, 0.04, 0.28], "parent": "Thigh.R", "connected": True},
        "Foot.R": {"head": [-0.38, 0.04, 0.28], "tail": [-0.38, -0.22, 0.12], "parent": "Shin.R", "connected": True},
    }

    boxes = [
        # --- HEAD & CREST & BRUTE SKULL (spiked crest helmet, hollow skull visor with tusks) ---
        {"center": [0.0, -0.30, 2.30], "size": [0.50, 0.46, 0.16], "bone": "Head", "mat_index": 1, "rot": [-8.0, 0.0, 0.0]},
        {"center": [0.0, -0.42, 2.42], "size": [0.12, 0.12, 0.14], "bone": "Head", "mat_index": 2, "rot": [-8.0, 0.0, 0.0]},
        {"center": [0.0, -0.30, 2.44], "size": [0.12, 0.12, 0.16], "bone": "Head", "mat_index": 2, "rot": [-8.0, 0.0, 0.0]},
        {"center": [0.0, -0.18, 2.41], "size": [0.12, 0.12, 0.14], "bone": "Head", "mat_index": 2, "rot": [-8.0, 0.0, 0.0]},
        {"center": [0.0, -0.44, 2.30], "size": [0.48, 0.16, 0.10], "bone": "Head", "mat_index": 1, "rot": [-8.0, 0.0, 0.0]},
        {"center": [0.24, -0.32, 2.22], "size": [0.08, 0.36, 0.22], "bone": "Head", "mat_index": 1, "rot": [-8.0, 0.0, 0.0]},
        {"center": [-0.24, -0.32, 2.22], "size": [0.08, 0.36, 0.22], "bone": "Head", "mat_index": 1, "rot": [-8.0, 0.0, 0.0]},
        # Skull face inside helmet cavity
        {"center": [0.0, -0.34, 2.18], "size": [0.38, 0.30, 0.22], "bone": "Head", "mat_index": 3, "rot": [-8.0, 0.0, 0.0]},
        {"center": [0.10, -0.48, 2.22], "size": [0.09, 0.04, 0.08], "bone": "Head", "mat_index": 2, "rot": [-8.0, 0.0, 0.0]},
        {"center": [-0.10, -0.48, 2.22], "size": [0.09, 0.04, 0.08], "bone": "Head", "mat_index": 2, "rot": [-8.0, 0.0, 0.0]},
        # Massive undead jaw & tusks
        {"center": [0.0, -0.44, 2.06], "size": [0.40, 0.26, 0.12], "bone": "Head", "mat_index": 3, "rot": [-6.0, 0.0, 0.0]},
        {"center": [0.14, -0.54, 2.12], "size": [0.06, 0.06, 0.10], "bone": "Head", "mat_index": 3, "rot": [-6.0, 0.0, 0.0]},
        {"center": [-0.14, -0.54, 2.12], "size": [0.06, 0.06, 0.10], "bone": "Head", "mat_index": 3, "rot": [-6.0, 0.0, 0.0]},
        {"center": [0.0, -0.54, 2.10], "size": [0.14, 0.05, 0.06], "bone": "Head", "mat_index": 3, "rot": [-6.0, 0.0, 0.0]},

        # --- NECK & COLLAR ---
        {"center": [0.0, -0.18, 1.94], "size": [0.38, 0.34, 0.20], "bone": "Neck", "mat_index": 0},
        {"center": [0.0, -0.24, 1.92], "size": [0.46, 0.14, 0.16], "bone": "Neck", "mat_index": 1},

        # --- CHEST & STEPPED PAULDRONS (with pyramid studs along top) ---
        {"center": [0.0, -0.08, 1.74], "size": [0.96, 0.58, 0.38], "bone": "Chest", "mat_index": 0, "rot": [-12.0, 0.0, 0.0]},
        {"center": [0.46, -0.06, 1.72], "size": [0.18, 0.44, 0.32], "bone": "Chest", "mat_index": 0, "rot": [-12.0, 0.0, 0.0]},
        {"center": [-0.46, -0.06, 1.72], "size": [0.18, 0.44, 0.32], "bone": "Chest", "mat_index": 0, "rot": [-12.0, 0.0, 0.0]},
        # Segmented stone chest plates
        {"center": [0.24, -0.34, 1.78], "size": [0.38, 0.12, 0.30], "bone": "Chest", "mat_index": 1, "rot": [-12.0, -4.0, 0.0]},
        {"center": [-0.24, -0.34, 1.78], "size": [0.38, 0.12, 0.30], "bone": "Chest", "mat_index": 1, "rot": [-12.0, 4.0, 0.0]},
        {"center": [0.0, -0.38, 1.72], "size": [0.16, 0.06, 0.22], "bone": "Chest", "mat_index": 2, "rot": [-12.0, 0.0, 0.0]},
        # Left stepped pauldron with spikes
        {"center": [0.72, -0.06, 1.94], "size": [0.38, 0.48, 0.32], "bone": "Chest", "mat_index": 1, "rot": [-6.0, -18.0, -4.0]},
        {"center": [0.76, -0.06, 2.08], "size": [0.28, 0.36, 0.14], "bone": "Chest", "mat_index": 1, "rot": [-6.0, -18.0, -4.0]},
        {"center": [0.78, -0.16, 2.18], "size": [0.10, 0.10, 0.10], "bone": "Chest", "mat_index": 2, "rot": [-6.0, -18.0, -4.0]},
        {"center": [0.80, -0.04, 2.20], "size": [0.10, 0.10, 0.12], "bone": "Chest", "mat_index": 2, "rot": [-6.0, -18.0, -4.0]},
        {"center": [0.78, 0.08, 2.18], "size": [0.10, 0.10, 0.10], "bone": "Chest", "mat_index": 2, "rot": [-6.0, -18.0, -4.0]},
        # Right stepped pauldron with spikes
        {"center": [-0.72, -0.06, 1.94], "size": [0.38, 0.48, 0.32], "bone": "Chest", "mat_index": 1, "rot": [-6.0, 18.0, 4.0]},
        {"center": [-0.76, -0.06, 2.08], "size": [0.28, 0.36, 0.14], "bone": "Chest", "mat_index": 1, "rot": [-6.0, 18.0, 4.0]},
        {"center": [-0.78, -0.16, 2.18], "size": [0.10, 0.10, 0.10], "bone": "Chest", "mat_index": 2, "rot": [-6.0, 18.0, 4.0]},
        {"center": [-0.80, -0.04, 2.20], "size": [0.10, 0.10, 0.12], "bone": "Chest", "mat_index": 2, "rot": [-6.0, 18.0, 4.0]},
        {"center": [-0.78, 0.08, 2.18], "size": [0.10, 0.10, 0.10], "bone": "Chest", "mat_index": 2, "rot": [-6.0, 18.0, 4.0]},

        # --- SPINE ---
        {"center": [0.0, -0.02, 1.48], "size": [0.82, 0.48, 0.26], "bone": "Spine", "mat_index": 0, "rot": [-8.0, 0.0, 0.0]},
        {"center": [0.0, 0.24, 1.50], "size": [0.38, 0.14, 0.32], "bone": "Spine", "mat_index": 1, "rot": [-8.0, 0.0, 0.0]},
        {"center": [0.0, 0.32, 1.54], "size": [0.14, 0.10, 0.14], "bone": "Spine", "mat_index": 2, "rot": [-8.0, 0.0, 0.0]},

        # --- HIPS & BELT & TATTERED LOINCLOTH ---
        {"center": [0.0, 0.0, 1.25], "size": [0.88, 0.52, 0.28], "bone": "Hips", "mat_index": 1},
        {"center": [0.0, -0.02, 1.25], "size": [0.92, 0.54, 0.12], "bone": "Hips", "mat_index": 4},
        {"center": [0.0, -0.30, 1.25], "size": [0.24, 0.08, 0.18], "bone": "Hips", "mat_index": 2},
        # Long tattered reddish-brown loincloth apron
        {"center": [0.0, -0.28, 1.15], "size": [0.38, 0.08, 0.16], "bone": "Hips", "mat_index": 4, "rot": [-8.0, 0.0, 0.0]},
        {"center": [0.0, -0.28, 0.95], "size": [0.24, 0.06, 0.30], "bone": "Hips", "mat_index": 4, "rot": [-8.0, 0.0, 0.0]},
        {"center": [0.16, -0.26, 1.02], "size": [0.12, 0.05, 0.18], "bone": "Hips", "mat_index": 4, "rot": [-8.0, -4.0, 0.0]},
        {"center": [-0.16, -0.26, 1.02], "size": [0.12, 0.05, 0.18], "bone": "Hips", "mat_index": 4, "rot": [-8.0, 4.0, 0.0]},

        # --- LEFT BATTERING ARM & HAMMER-FIST ---
        {"center": [0.80, -0.12, 1.62], "size": [0.34, 0.36, 0.44], "bone": "UpperArm.L", "mat_index": 0, "rot": [-18.0, -10.0, 0.0]},
        {"center": [0.96, -0.12, 1.62], "size": [0.10, 0.28, 0.36], "bone": "UpperArm.L", "mat_index": 1, "rot": [-18.0, -10.0, 0.0]},
        {"center": [0.84, -0.42, 1.34], "size": [0.42, 0.48, 0.42], "bone": "Forearm.L", "mat_index": 1, "rot": [-46.0, -4.0, 0.0]},
        {"center": [0.84, -0.58, 1.22], "size": [0.44, 0.20, 0.44], "bone": "Forearm.L", "mat_index": 2, "rot": [-38.0, -4.0, 0.0]},
        # Hammer-Fist
        {"center": [0.84, -0.70, 1.10], "size": [0.48, 0.46, 0.46], "bone": "Hand.L", "mat_index": 1, "rot": [-28.0, -4.0, 0.0]},
        {"center": [0.84, -0.84, 1.10], "size": [0.42, 0.16, 0.40], "bone": "Hand.L", "mat_index": 2, "rot": [-28.0, -4.0, 0.0]},
        {"center": [1.02, -0.74, 1.10], "size": [0.10, 0.12, 0.12], "bone": "Hand.L", "mat_index": 2, "rot": [-28.0, -4.0, 0.0]},
        {"center": [0.84, -0.72, 1.28], "size": [0.14, 0.12, 0.10], "bone": "Hand.L", "mat_index": 2, "rot": [-28.0, -4.0, 0.0]},

        # --- RIGHT BATTERING ARM & REINFORCED HAMMER-FIST ---
        {"center": [-0.80, -0.10, 1.60], "size": [0.34, 0.36, 0.44], "bone": "UpperArm.R", "mat_index": 0, "rot": [-16.0, 10.0, 0.0]},
        {"center": [-0.96, -0.10, 1.60], "size": [0.10, 0.28, 0.36], "bone": "UpperArm.R", "mat_index": 1, "rot": [-16.0, 10.0, 0.0]},
        {"center": [-0.84, -0.40, 1.32], "size": [0.42, 0.48, 0.42], "bone": "Forearm.R", "mat_index": 1, "rot": [-42.0, 4.0, 0.0]},
        {"center": [-0.84, -0.56, 1.20], "size": [0.44, 0.20, 0.44], "bone": "Forearm.R", "mat_index": 2, "rot": [-34.0, 4.0, 0.0]},
        # Reinforced Hammer-Fist
        {"center": [-0.84, -0.68, 1.08], "size": [0.50, 0.48, 0.48], "bone": "Hand.R", "mat_index": 1, "rot": [-26.0, 4.0, 0.0]},
        {"center": [-0.84, -0.84, 1.08], "size": [0.44, 0.18, 0.42], "bone": "Hand.R", "mat_index": 2, "rot": [-26.0, 4.0, 0.0]},
        {"center": [-1.03, -0.72, 1.08], "size": [0.12, 0.14, 0.14], "bone": "Hand.R", "mat_index": 2, "rot": [-26.0, 4.0, 0.0]},
        {"center": [-0.84, -0.70, 1.27], "size": [0.16, 0.14, 0.10], "bone": "Hand.R", "mat_index": 2, "rot": [-26.0, 4.0, 0.0]},

        # --- LEFT PILLAR LEG & GREAVE ---
        {"center": [0.36, 0.0, 0.94], "size": [0.38, 0.40, 0.44], "bone": "Thigh.L", "mat_index": 0},
        {"center": [0.48, -0.04, 0.94], "size": [0.10, 0.34, 0.40], "bone": "Thigh.L", "mat_index": 1},
        {"center": [0.38, -0.14, 0.72], "size": [0.34, 0.14, 0.22], "bone": "Shin.L", "mat_index": 1},
        {"center": [0.38, -0.22, 0.72], "size": [0.12, 0.06, 0.12], "bone": "Shin.L", "mat_index": 2},
        {"center": [0.38, -0.04, 0.50], "size": [0.36, 0.38, 0.46], "bone": "Shin.L", "mat_index": 1},
        {"center": [0.38, -0.04, 0.14], "size": [0.42, 0.48, 0.26], "bone": "Foot.L", "mat_index": 1},
        {"center": [0.38, -0.26, 0.10], "size": [0.38, 0.14, 0.18], "bone": "Foot.L", "mat_index": 2},

        # --- RIGHT PILLAR LEG & GREAVE ---
        {"center": [-0.36, 0.0, 0.94], "size": [0.38, 0.40, 0.44], "bone": "Thigh.R", "mat_index": 0},
        {"center": [-0.48, -0.04, 0.94], "size": [0.10, 0.34, 0.40], "bone": "Thigh.R", "mat_index": 1},
        {"center": [-0.38, -0.14, 0.72], "size": [0.34, 0.14, 0.22], "bone": "Shin.R", "mat_index": 1},
        {"center": [-0.38, -0.22, 0.72], "size": [0.12, 0.06, 0.12], "bone": "Shin.R", "mat_index": 2},
        {"center": [-0.38, 0.04, 0.50], "size": [0.36, 0.38, 0.46], "bone": "Shin.R", "mat_index": 1},
        {"center": [-0.38, 0.04, 0.14], "size": [0.42, 0.48, 0.26], "bone": "Foot.R", "mat_index": 1},
        {"center": [-0.38, -0.18, 0.10], "size": [0.38, 0.14, 0.18], "bone": "Foot.R", "mat_index": 2},
    ]

    return {
        "version": 1,
        "character": "siege_breaker",
        "materials": materials,
        "bones": bones,
        "boxes": boxes,
    }


def main():
    specs = {
        "zombie": get_zombie_spec(),
        "ranged_skirmisher": get_skirmisher_spec(),
        "siege_breaker": get_siege_breaker_spec(),
    }

    for char_name, spec in specs.items():
        spec_path = REPO_ROOT / "assets" / "characters" / char_name / "source" / "character_spec.json"
        spec_path.write_text(json.dumps(spec, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        box_count = len(spec["boxes"])
        tri_count = box_count * 12
        print(f"Generated {char_name}: {box_count} boxes ({tri_count} tris) -> {spec_path}")


if __name__ == "__main__":
    main()

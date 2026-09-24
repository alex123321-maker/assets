"""Helper script to extract structured character_spec.json from character definitions.
Runs inside Blender to leverage mathutils / bmesh.
"""

from __future__ import annotations
import json
import math
from pathlib import Path
import bpy
import bmesh
from mathutils import Vector, Euler, Matrix

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
import sys
sys.path.append(str(Path(__file__).resolve().parent))
import build_character_asset as bca


class MockPoseBone:
    def __init__(self, name: str, recorder: list):
        self.name = name
        self.recorder = recorder
        self.location = Vector((0, 0, 0))
        self.rotation_quaternion = None

    def keyframe_insert(self, data_path: str, frame: int):
        rec = {"frame": frame, "bone": self.name}
        if data_path == "location":
            rec["loc"] = [round(v, 4) for v in self.location]
        elif data_path == "rotation_quaternion":
            euler = self.rotation_quaternion.to_euler()
            rec["rot_euler_deg"] = [round(math.degrees(v), 2) for v in euler]
        self.recorder.append(rec)


class MockPose:
    def __init__(self, recorder: list):
        self.recorder = recorder
        self.bones = {}

    def get(self, name: str):
        if name not in self.bones:
            self.bones[name] = MockPoseBone(name, self.recorder)
        return self.bones[name]


class MockArmatureObject:
    def __init__(self):
        self.recorder = []
        self.pose = MockPose(self.recorder)
        self.animation_data = None

    def animation_data_create(self):
        pass


def record_boxes(mesh_builder) -> list[dict]:
    boxes = []
    def mock_add_box(bm, center, size, bone_name, weights, mat_index=0, rot=(0, 0, 0)):
        # Apply the -Y front rotation (180 around Z)
        rot_mat = Matrix.Rotation(math.pi, 3, 'Z')
        c_rot = rot_mat @ Vector(center)
        # Combine rotations
        euler = Euler((math.radians(rot[0]), math.radians(rot[1]), math.radians(rot[2])), 'XYZ')
        r_mat = rot_mat @ euler.to_matrix() @ rot_mat.transposed()
        r_deg = [round(math.degrees(v), 2) for v in r_mat.to_euler('XYZ')]
        boxes.append({
            "center": [round(c_rot.x, 4), round(c_rot.y, 4), round(c_rot.z, 4)],
            "size": [round(s, 4) for s in size],
            "bone": bone_name,
            "mat_index": mat_index,
            "rot": r_deg,
        })

    orig_add_box = bca.core.add_box_geometry
    bca.core.add_box_geometry = mock_add_box
    mesh_builder(None, {})
    bca.core.add_box_geometry = orig_add_box
    return boxes


def record_bones(bone_defs: dict[str, dict]) -> dict[str, dict]:
    rot_mat = Matrix.Rotation(math.pi, 3, 'Z')
    res = {}
    for b_name, b_info in bone_defs.items():
        h = rot_mat @ Vector(b_info["head"])
        t = rot_mat @ Vector(b_info["tail"])
        item = {
            "head": [round(h.x, 4), round(h.y, 4), round(h.z, 4)],
            "tail": [round(t.x, 4), round(t.y, 4), round(t.z, 4)],
            "parent": b_info.get("parent"),
        }
        if b_info.get("connected"):
            item["connected"] = True
        res[b_name] = item
    return res


def extract_character(char_name: str, pkg_dir: Path):
    if char_name == "zombie":
        materials = [
            {"name": "mat_decay_flesh", "color_hex": "#84946e", "roughness": 0.88, "metallic": 0.0},
            {"name": "mat_pale_flesh", "color_hex": "#9baa84", "roughness": 0.85, "metallic": 0.0},
            {"name": "mat_tattered_cloth", "color_hex": "#524032", "roughness": 0.92, "metallic": 0.0},
            {"name": "mat_bone_teeth", "color_hex": "#cfc8b6", "roughness": 0.75, "metallic": 0.0},
            {"name": "mat_dark_socket", "color_hex": "#1c221a", "roughness": 1.0, "metallic": 0.0},
        ]
        bone_defs = bca.get_zombie_bone_defs()
        mesh_builder = bca.build_zombie_mesh
    elif char_name == "ranged_skirmisher":
        materials = [
            {"name": "mat_bone_weathered", "color_hex": "#cfc4a6", "roughness": 0.80, "metallic": 0.0},
            {"name": "mat_bone_dark", "color_hex": "#9c9276", "roughness": 0.82, "metallic": 0.0},
            {"name": "mat_ragged_leather", "color_hex": "#4e392a", "roughness": 0.90, "metallic": 0.0},
            {"name": "mat_bow_wood", "color_hex": "#683e20", "roughness": 0.75, "metallic": 0.0},
            {"name": "mat_bow_string", "color_hex": "#e8e2d4", "roughness": 0.60, "metallic": 0.0},
            {"name": "mat_dark_socket", "color_hex": "#181816", "roughness": 1.0, "metallic": 0.0},
        ]
        bone_defs = bca.get_skirmisher_bone_defs()
        mesh_builder = bca.build_skirmisher_mesh
    elif char_name == "siege_breaker":
        materials = [
            {"name": "mat_decay_brute_flesh", "color_hex": "#54624d", "roughness": 0.88, "metallic": 0.0},
            {"name": "mat_corrupted_stone", "color_hex": "#42484f", "roughness": 0.95, "metallic": 0.0},
            {"name": "mat_iron_plate", "color_hex": "#2c2f34", "roughness": 0.55, "metallic": 0.5},
            {"name": "mat_bone_armor", "color_hex": "#cfc5ae", "roughness": 0.80, "metallic": 0.0},
            {"name": "mat_ragged_loincloth", "color_hex": "#4e2b24", "roughness": 0.92, "metallic": 0.0},
        ]
        bone_defs = bca.get_siege_breaker_bone_defs()
        mesh_builder = bca.build_siege_breaker_mesh

    boxes = record_boxes(mesh_builder)
    bones = record_bones(bone_defs)

    spec = {
        "version": 1,
        "character": char_name,
        "materials": materials,
        "bones": bones,
        "boxes": boxes,
    }

    out_file = pkg_dir / "source" / "character_spec.json"
    out_file.parent.mkdir(parents=True, exist_ok=True)
    out_file.write_text(json.dumps(spec, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"Wrote {out_file} ({len(boxes)} boxes, {len(bones)} bones)")


def main():
    for name in ["zombie", "ranged_skirmisher", "siege_breaker"]:
        pkg_dir = REPO_ROOT / "assets" / "characters" / name
        extract_character(name, pkg_dir)


if __name__ == "__main__":
    main()

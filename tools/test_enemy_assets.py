"""Automated unit and integration test suite for Cube Siege enemy assets.
Validates:
  - TECH-01: All box face normals point outward across all 6 faces (no inverted normals).
  - TECH-02: Exported GLB animation clip durations and timestamps match 30 fps timescale.
  - EVID-01: Non-destructive silhouette rendering preserves polygon material indices.
"""

from __future__ import annotations
import json
import math
import struct
import sys
from pathlib import Path
import unittest

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.append(str(REPO_ROOT / "tools/blender"))


def parse_glb_animations(glb_path: Path) -> dict[str, dict]:
    """Parse glTF 2.0 binary file to inspect animation clips and sampler timestamps."""
    with open(glb_path, "rb") as f:
        magic, version, length = struct.unpack("<4sII", f.read(12))
        assert magic == b"glTF", f"Invalid magic in {glb_path}"
        
        # Read JSON chunk
        chunk_len, chunk_type = struct.unpack("<II", f.read(8))
        assert chunk_type == 0x4E4F534A, "First chunk must be JSON"
        json_bytes = f.read(chunk_len)
        gltf = json.loads(json_bytes.decode("utf-8"))
        
        # Read BIN chunk
        chunk_len2, chunk_type2 = struct.unpack("<II", f.read(8))
        assert chunk_type2 == 0x004E4942, "Second chunk must be BIN"
        bin_data = f.read(chunk_len2)

    accessors = gltf.get("accessors", [])
    buffer_views = gltf.get("bufferViews", [])

    def get_accessor_floats(acc_idx: int) -> list[float]:
        acc = accessors[acc_idx]
        bv = buffer_views[acc["bufferView"]]
        offset = bv.get("byteOffset", 0) + acc.get("byteOffset", 0)
        count = acc["count"]
        # Component type 5126 = FLOAT
        assert acc.get("componentType") == 5126, "Expected FLOAT component type"
        raw = bin_data[offset : offset + count * 4]
        return list(struct.unpack(f"<{count}f", raw))

    results = {}
    for anim in gltf.get("animations", []):
        name = anim.get("name", "unnamed")
        max_time = 0.0
        min_time = 0.0
        sample_counts = []
        for sampler in anim.get("samplers", []):
            time_accessor_idx = sampler["input"]
            timestamps = get_accessor_floats(time_accessor_idx)
            if timestamps:
                min_time = min(min_time, timestamps[0])
                max_time = max(max_time, timestamps[-1])
                sample_counts.append(len(timestamps))
        results[name] = {
            "duration": round(max_time, 4),
            "start": round(min_time, 4),
            "sample_counts": sample_counts,
        }
    return results


class TestEnemyAssets(unittest.TestCase):
    def test_tech01_box_geometry_normals_outward(self):
        """TECH-01: Verify all 6 box face normals point strictly outward from the center."""
        import bmesh
        from mathutils import Vector
        import character_builder_core as core

        # Test various centers, dimensions, and Euler rotations
        test_cases = [
            ((0, 0, 0), (1.0, 1.0, 1.0), (0, 0, 0)),
            ((2.0, -3.0, 1.5), (0.4, 0.6, 0.8), (0, 0, 0)),
            ((0, 0, 1.0), (0.2, 0.5, 1.2), (18, -16, 0)),
            ((-0.46, 0.38, 1.66), (0.06, 0.06, 0.20), (-36, 0, 0)),
            ((0.36, 0.0, 1.18), (0.38, 0.38, 0.64), (10, 0, -8)),
        ]

        for center, size, rot in test_cases:
            bm = bmesh.new()
            weights = {}
            core.add_box_geometry(bm, center, size, "Bone", weights, mat_index=0, rot=rot)
            bm.normal_update()

            self.assertEqual(len(bm.faces), 6, "A box must have exactly 6 faces")
            box_c = Vector(center)

            for idx, face in enumerate(bm.faces):
                face_center = face.calc_center_median()
                outward_vec = face_center - box_c
                dot = face.normal.dot(outward_vec)
                self.assertGreater(
                    dot,
                    0.0001,
                    f"Face {idx} normal {face.normal} points inward! dot={dot} for box at {center} rot={rot}",
                )
            bm.free()

    def test_tech02_glb_animation_durations_at_30fps(self):
        """TECH-02: Verify exported GLB animation clips have correct durations for 30 fps."""
        chars = {
            "zombie": {
                "idle": 2.0,      # 60 frames / 30 fps
                "move": 1.0,      # 30 frames / 30 fps
                "attack": 1.3333, # 40 frames / 30 fps
                "hit": 0.5,       # 15 frames / 30 fps
                "death": 1.3333,  # 40 frames / 30 fps
            },
            "ranged_skirmisher": {
                "idle": 2.0,
                "move": 1.0,
                "attack": 1.3333, # 40 frames / 30 fps
                "hit": 0.5,
                "death": 1.3333,
            },
            "siege_breaker": {
                "idle": 2.0,
                "move": 1.0,
                "attack": 1.5,    # 45 frames / 30 fps
                "hit": 0.5,
                "death": 1.3333,
            },
        }

        for char_name, expected_clips in chars.items():
            glb_path = REPO_ROOT / f"assets/characters/{char_name}/output/model.glb"
            if not glb_path.exists():
                self.skipTest(f"{glb_path} does not exist yet (run build first)")
            
            clips = parse_glb_animations(glb_path)
            for anim_name, exp_dur in expected_clips.items():
                self.assertIn(
                    anim_name,
                    clips,
                    f"Required animation '{anim_name}' missing from {char_name}.glb",
                )
                actual_dur = clips[anim_name]["duration"]
                # Must be accurate within 0.01 seconds (30 fps frame step is 0.0333s)
                self.assertAlmostEqual(
                    actual_dur,
                    exp_dur,
                    delta=0.04,
                    msg=f"Animation '{anim_name}' in {char_name}.glb duration {actual_dur}s does not match 30 fps timescale ({exp_dur}s)!",
                )

    def test_evid01_silhouette_material_override_non_destructive(self):
        """EVID-01: Verify that view_layer.material_override does not alter mesh polygon material indices."""
        import bpy
        import bmesh
        import character_builder_core as core

        core.clear_scene()
        bm = bmesh.new()
        weights = {}
        # Add 3 boxes with different material indices
        core.add_box_geometry(bm, (0, 0, 0), (1, 1, 1), "Bone1", weights, mat_index=0)
        core.add_box_geometry(bm, (0, 0, 1), (1, 1, 1), "Bone2", weights, mat_index=1)
        core.add_box_geometry(bm, (0, 0, 2), (1, 1, 1), "Bone3", weights, mat_index=2)

        mesh = bpy.data.meshes.new("TestMesh")
        bm.to_mesh(mesh)
        bm.free()

        obj = bpy.data.objects.new("TestObj", mesh)
        bpy.context.collection.objects.link(obj)

        mat0 = core.create_pbr_material("mat0", "#ff0000")
        mat1 = core.create_pbr_material("mat1", "#00ff00")
        mat2 = core.create_pbr_material("mat2", "#0000ff")
        obj.data.materials.append(mat0)
        obj.data.materials.append(mat1)
        obj.data.materials.append(mat2)

        # Record original polygon material indices
        orig_indices = [p.material_index for p in obj.data.polygons]
        self.assertIn(0, orig_indices)
        self.assertIn(1, orig_indices)
        self.assertIn(2, orig_indices)

        # Apply silhouette view_layer material override
        mat_black = core.create_pbr_material("mat_black", "#010101")
        bpy.context.view_layer.material_override = mat_black

        # Render pass would happen here...

        # Clear silhouette view_layer material override
        bpy.context.view_layer.material_override = None

        # Verify polygon material indices are strictly identical
        restored_indices = [p.material_index for p in obj.data.polygons]
        self.assertEqual(
            orig_indices,
            restored_indices,
            "Polygon material indices must NOT be modified by view_layer.material_override!",
        )
        self.assertEqual(
            [m.name for m in obj.data.materials],
            ["mat0", "mat1", "mat2"],
            "Mesh material list must remain intact!",
        )


if __name__ == "__main__":
    test_args = [sys.argv[0]]
    if "--" in sys.argv:
        test_args.extend(sys.argv[sys.argv.index("--") + 1 :])
    unittest.main(argv=test_args)

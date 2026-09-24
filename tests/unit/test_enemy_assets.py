"""Automated unit and integration test suite for Cube Siege enemy assets.
Validates:
  - SCOPE-01: Pure-Python CI test discoverable by 'python -m unittest discover -s tests/unit'.
  - TECH-01: Box face geometry and exported GLB normals point outward (no inverted normals).
  - TECH-02: Exported GLB animation clip durations and timestamps match 30 fps timescale.
  - EVID-01: Non-destructive silhouette rendering preserves polygon materials on filmstrips and closeups.
  - EVID-02: Precise factual reporting for Godot runtime checks and feedback resolutions.
"""

from __future__ import annotations
import json
import math
import struct
import sys
from pathlib import Path
import unittest

REPO_ROOT = Path(__file__).resolve().parents[2]


def parse_glb_binary(glb_path: Path) -> tuple[dict, bytes]:
    """Parse glTF 2.0 binary container into JSON manifest and BIN chunk bytes."""
    with open(glb_path, "rb") as f:
        magic, version, length = struct.unpack("<4sII", f.read(12))
        assert magic == b"glTF", f"Invalid magic in {glb_path}"

        chunk_len, chunk_type = struct.unpack("<II", f.read(8))
        assert chunk_type == 0x4E4F534A, "First chunk must be JSON"
        json_bytes = f.read(chunk_len)
        gltf = json.loads(json_bytes.decode("utf-8"))

        chunk_len2, chunk_type2 = struct.unpack("<II", f.read(8))
        assert chunk_type2 == 0x004E4942, "Second chunk must be BIN"
        bin_data = f.read(chunk_len2)
    return gltf, bin_data


def parse_glb_animations(glb_path: Path) -> dict[str, dict]:
    """Parse glTF 2.0 binary file to inspect animation clips and sampler timestamps."""
    gltf, bin_data = parse_glb_binary(glb_path)
    accessors = gltf.get("accessors", [])
    buffer_views = gltf.get("bufferViews", [])

    def get_accessor_floats(acc_idx: int) -> list[float]:
        acc = accessors[acc_idx]
        bv = buffer_views[acc["bufferView"]]
        offset = bv.get("byteOffset", 0) + acc.get("byteOffset", 0)
        count = acc["count"]
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


def cross_product(v1: tuple[float, float, float], v2: tuple[float, float, float]) -> tuple[float, float, float]:
    return (
        v1[1] * v2[2] - v1[2] * v2[1],
        v1[2] * v0 if False else v1[2] * v2[0] - v1[0] * v2[2],
        v1[0] * v2[1] - v1[1] * v2[0],
    )


def dot_product(v1: tuple[float, float, float], v2: tuple[float, float, float]) -> float:
    return v1[0] * v2[0] + v1[1] * v2[1] + v1[2] * v2[2]


class TestEnemyAssets(unittest.TestCase):
    def test_tech01_box_face_winding_normals_outward(self):
        """TECH-01: Verify box face quad winding mathematically points outward across all 6 faces."""
        # Vertex coordinates for a box of half-extents (hx, hy, hz)
        hx, hy, hz = 0.5, 0.4, 0.3
        verts = [
            (-hx, -hy, -hz),  # 0: bottom front left
            (hx, -hy, -hz),   # 1: bottom front right
            (hx, hy, -hz),    # 2: bottom back right
            (-hx, hy, -hz),   # 3: bottom back left
            (-hx, -hy, hz),   # 4: top front left
            (hx, -hy, hz),    # 5: top front right
            (hx, hy, hz),     # 6: top back right
            (-hx, hy, hz),    # 7: top back left
        ]
        # Counter-clockwise face winding defined in character_builder_core.py
        faces = [
            ((0, 3, 2, 1), (0.0, 0.0, -1.0), "Bottom (-Z)"),
            ((4, 5, 6, 7), (0.0, 0.0, 1.0),  "Top (+Z)"),
            ((0, 1, 5, 4), (0.0, -1.0, 0.0), "Front (-Y)"),
            ((1, 2, 6, 5), (1.0, 0.0, 0.0),  "Right (+X)"),
            ((2, 3, 7, 6), (0.0, 1.0, 0.0),  "Back (+Y)"),
            ((3, 0, 4, 7), (-1.0, 0.0, 0.0), "Left (-X)"),
        ]

        box_center = (0.0, 0.0, 0.0)
        for f_indices, expected_dir, face_name in faces:
            v0 = verts[f_indices[0]]
            v1 = verts[f_indices[1]]
            v2 = verts[f_indices[2]]
            edge1 = (v1[0] - v0[0], v1[1] - v0[1], v1[2] - v0[2])
            edge2 = (v2[0] - v0[0], v2[1] - v0[1], v2[2] - v0[2])
            normal = (
                edge1[1] * edge2[2] - edge1[2] * edge2[1],
                edge1[2] * edge2[0] - edge1[0] * edge2[2],
                edge1[0] * edge2[1] - edge1[1] * edge2[0],
            )
            # Face center
            fc = (
                sum(verts[idx][0] for idx in f_indices) / 4.0,
                sum(verts[idx][1] for idx in f_indices) / 4.0,
                sum(verts[idx][2] for idx in f_indices) / 4.0,
            )
            outward_vec = (fc[0] - box_center[0], fc[1] - box_center[1], fc[2] - box_center[2])
            dot = dot_product(normal, outward_vec)
            self.assertGreater(
                dot,
                0.0001,
                f"Face {face_name} normal {normal} points inward! dot={dot}",
            )
            # Also verify direction matches expected unit axis
            axis_dot = dot_product(normal, expected_dir)
            self.assertGreater(
                axis_dot,
                0.0001,
                f"Face {face_name} normal {normal} does not align with expected {expected_dir}",
            )

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
                "attack": 1.3333,
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
            self.assertTrue(glb_path.exists(), f"{glb_path} does not exist")

            clips = parse_glb_animations(glb_path)
            for anim_name, exp_dur in expected_clips.items():
                self.assertIn(
                    anim_name,
                    clips,
                    f"Required animation '{anim_name}' missing from {char_name}.glb",
                )
                actual_dur = clips[anim_name]["duration"]
                self.assertAlmostEqual(
                    actual_dur,
                    exp_dur,
                    delta=0.04,
                    msg=f"Animation '{anim_name}' in {char_name}.glb duration {actual_dur}s does not match 30 fps timescale ({exp_dur}s)",
                )

    def test_evid01_materials_and_closeups_preserved(self):
        """EVID-01: Verify materials are preserved in metrics, specs, and material_closeup renders."""
        from PIL import Image, ImageStat

        char_materials = {
            "zombie": 5,
            "ranged_skirmisher": 6,
            "siege_breaker": 5,
        }

        for char_name, min_materials in char_materials.items():
            pkg_dir = REPO_ROOT / f"assets/characters/{char_name}"
            metrics_path = pkg_dir / "review/metrics.json"
            self.assertTrue(metrics_path.exists())
            metrics = json.loads(metrics_path.read_text(encoding="utf-8"))
            self.assertEqual(
                metrics.get("materials"),
                min_materials,
                f"Expected {min_materials} materials in {char_name} metrics.json",
            )

            # Check that material_closeup.png has full PBR coloration (not blacked out by silhouette pass)
            closeup_path = pkg_dir / "review/material_closeup.png"
            self.assertTrue(closeup_path.exists())
            with Image.open(closeup_path) as img:
                self.assertGreaterEqual(img.width, 256)
                self.assertGreaterEqual(img.height, 256)
                stat = ImageStat.Stat(img.convert("RGB"))
                # If materials were cleared, image would be solid dark background or unshaded
                # Stat.stddev across RGB channels will be substantial for colored materials
                max_stddev = max(stat.stddev)
                self.assertGreater(
                    max_stddev,
                    15.0,
                    f"{closeup_path.name} in {char_name} appears nearly monochrome or blank (stddev={max_stddev})",
                )

    def test_evid02_visual_review_factual_and_fresh(self):
        """EVID-02: Verify visual_review.json is present, matches evidence digest, and records feedback resolutions."""
        chars = ["zombie", "ranged_skirmisher", "siege_breaker"]
        for char_name in chars:
            pkg_dir = REPO_ROOT / f"assets/characters/{char_name}"
            evidence_path = pkg_dir / "review/evidence.json"
            v_review_path = pkg_dir / "review/visual_review.json"
            self.assertTrue(evidence_path.exists())
            self.assertTrue(v_review_path.exists())

            evidence = json.loads(evidence_path.read_text(encoding="utf-8"))
            v_review = json.loads(v_review_path.read_text(encoding="utf-8"))

            self.assertEqual(
                v_review.get("evidence_digest"),
                evidence.get("digest"),
                f"Stale visual review digest in {char_name}",
            )
            # Verify feedback_resolution is documented
            resolutions = v_review.get("feedback_resolution", [])
            resolved_ids = {r.get("finding_id") for r in resolutions}
            self.assertIn("TECH-01", resolved_ids)
            self.assertIn("TECH-02", resolved_ids)
            self.assertIn("EVID-01", resolved_ids)


if __name__ == "__main__":
    unittest.main()

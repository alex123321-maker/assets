"""Geometric checks for the scoped Cairn cube-motion validator."""

import math
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from tools.cairn.validate_voxel_motion import validate_asset


def cube(cube_id, center, bone=None, size=1.0):
    return {"id": cube_id, "center": center, "size": size, "bone": bone or cube_id}


def matrix(center=(0, 0, 0), degrees=0, size=1.0):
    angle = math.radians(degrees)
    c, s = math.cos(angle) * size, math.sin(angle) * size
    return [[c, -s, 0, center[0]], [s, c, 0, center[1]],
            [0, 0, size, center[2]], [0, 0, 0, 1]]


class CairnVoxelMotionTests(unittest.TestCase):
    def test_face_edge_and_point_contact_are_allowed(self):
        for center in ([1, 0, 0], [1, 1, 0], [1, 1, 1]):
            with self.subTest(center=center):
                self.assertTrue(validate_asset([cube("a", [0, 0, 0]), cube("b", center)])["pass"])

    def test_real_overlap_reports_pair_and_depth(self):
        report = validate_asset([cube("a", [0, 0, 0]), cube("b", [.8, 0, 0])])
        self.assertFalse(report["pass"])
        self.assertEqual(report["rest_overlap_count"], 1)
        self.assertEqual(report["issues"][0]["pair"], ["a", "b"])
        self.assertAlmostEqual(report["issues"][0]["depth_m"], .2)

    def test_contact_tolerance_is_in_metres(self):
        cubes = [cube("a", [0, 0, 0]), cube("b", [1 - 1e-6, 0, 0])]
        self.assertTrue(validate_asset(cubes)["pass"])
        self.assertFalse(validate_asset(cubes, tolerance=1e-7)["pass"])

    def test_duplicate_ids_and_vector_size_are_invalid(self):
        for cubes in ([cube("a", [0, 0, 0]), cube("a", [2, 0, 0])],
                      [cube("a", [0, 0, 0], size=[1, 1, 1])]):
            with self.subTest(cubes=cubes):
                report = validate_asset(cubes)
                self.assertFalse(report["pass"])
                self.assertEqual(report["issues"][0]["code"], "invalid_input")

    def test_rotated_cubes_can_have_overlapping_aabbs_without_penetration(self):
        cubes = [cube("a", [0, 0, 0]), cube("b", [2, 0, 0])]
        frame = {"frame": 5, "cube_matrices": {
            "a": matrix(degrees=45), "b": matrix(center=(1, 1, 0), degrees=45)}}
        report = validate_asset(cubes, [frame])
        self.assertTrue(report["pass"])
        self.assertEqual(report["sat_tests"], 1)  # AABB alone would reject this.

    def test_rotated_cube_penetration_and_sample_label(self):
        cubes = [cube("a", [0, 0, 0]), cube("b", [2, 0, 0])]
        frame = {"frame": "attack:12", "cube_matrices": {
            "a": matrix(degrees=45), "b": matrix(center=(.5, .5, 0), degrees=45)}}
        report = validate_asset(cubes, [frame])
        self.assertFalse(report["pass"])
        self.assertEqual(report["animated_overlap_count"], 1)
        self.assertEqual(report["issues"][0]["frame"], "attack:12")
        self.assertAlmostEqual(report["issues"][0]["depth_m"], 1 - math.sqrt(.5), places=8)

    def test_edge_cross_axis_separates_when_all_six_face_axes_overlap(self):
        # A 3D pair where face axes each overlap >= 0.052m; an edge cross
        # axis is the separating axis. Checking only face normals is wrong.
        tilted = [
            [0.6595441561700077, -0.7321100726492085, -0.17034185506669505, 0.37976987340110036],
            [0.13348168078663608, 0.33709276682120903, -0.931960893734923, -0.8861147207786826],
            [0.7397189648483855, 0.59193184411923, 0.3200508474621501, 1.241440514196341],
            [0, 0, 0, 1],
        ]
        cubes = [cube("a", [0, 0, 0]), cube("b", [2, 0, 0])]
        report = validate_asset(cubes, [{"cube_matrices": {"a": matrix(), "b": tilted}}])
        self.assertTrue(report["pass"])
        self.assertEqual(report["sat_tests"], 1)

    def test_same_bone_rest_penetration_is_not_skipped(self):
        report = validate_asset([cube("a", [0, 0, 0], "body"), cube("b", [.5, 0, 0], "body")])
        self.assertFalse(report["pass"])

    def test_bone_matrices_transform_rest_centers(self):
        cubes = [cube("a", [0, 0, 0], "body"), cube("b", [1, 0, 0], "body")]
        report = validate_asset(cubes, [{"bone_matrices": {"body": matrix(center=(2, 3, 4), degrees=45)}}])
        self.assertTrue(report["pass"])
        self.assertEqual(report["frames_checked"], 1)
        self.assertEqual(report["animated_overlap_count"], 0)

    def test_per_cube_matrices_check_same_bone_when_motion_is_independent(self):
        cubes = [cube("a", [0, 0, 0], "body"), cube("b", [1, 0, 0], "body")]
        report = validate_asset(cubes, [{"cube_matrices": {"a": matrix(), "b": matrix(center=(.5, 0, 0))}}])
        self.assertFalse(report["pass"])
        self.assertEqual(report["animated_overlap_count"], 1)

    def test_missing_shear_and_nonuniform_matrices_are_rejected(self):
        shear = matrix()
        shear[0][1] = .2
        unequal = matrix()
        unequal[1][1] = 2
        for mapping in ({}, {"a": shear}, {"a": unequal}):
            with self.subTest(mapping=mapping):
                report = validate_asset([cube("a", [0, 0, 0])], [{"bone_matrices": mapping}])
                self.assertFalse(report["pass"])
                self.assertEqual(report["issues"][0]["code"], "invalid_input")

    def test_large_touching_grid_avoids_quadratic_sat(self):
        cubes = [cube(f"{x}:{y}:{z}", [x * .1, y * .1, z * .1], "body", .1)
                 for x in range(15) for y in range(10) for z in range(10)]
        report = validate_asset(cubes, [{"bone_matrices": {"body": matrix(degrees=25)}}])
        self.assertTrue(report["pass"])
        self.assertEqual(report["cube_count"], 1500)
        self.assertEqual(report["sat_tests"], 0)

    def test_invalid_issue_limit_returns_diagnostic(self):
        report = validate_asset([cube("a", [0, 0, 0])], max_issues="bad")
        self.assertFalse(report["pass"])
        self.assertEqual(report["issues"][0]["code"], "invalid_input")

    def test_cli_rejects_overlap_and_emits_json(self):
        entrypoint = Path(__file__).resolve().parents[2] / "tools/cairn/validate_voxel_motion.py"
        with tempfile.TemporaryDirectory(prefix="cairn_validator_test_") as directory:
            source = Path(directory) / "cubes.json"
            source.write_text(json.dumps({"cubes": [cube("a", [0, 0, 0]), cube("b", [.5, 0, 0])]}), encoding="utf-8")
            result = subprocess.run([sys.executable, str(entrypoint), "--input", str(source)],
                                    capture_output=True, text=True, timeout=10)
            self.assertEqual(result.returncode, 1, result.stderr)
            report = json.loads(result.stdout)
            self.assertEqual(report["rest_overlap_count"], 1)


if __name__ == "__main__":
    unittest.main()

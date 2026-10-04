"""Ground support and actual voxel clearance regressions for Cairn's legs."""

import math
from pathlib import Path
import unittest

from tools.cairn.leg_kinematics import check_source, leg_matrices, solve_leg


def transform_point(matrix, point):
    return tuple(sum(matrix[row][column] * point[column] for column in range(3))
                 + matrix[row][3] for row in range(3))


class CairnLegKinematicsTests(unittest.TestCase):
    def test_neutral_pose_keeps_authored_geometry_and_foot_support(self):
        for side in ("L", "R"):
            with self.subTest(side=side):
                pose = solve_leg(0, 0, 0, side=side)
                self.assertTrue(pose["reachable"])
                for field in ("thigh_x", "shin_x", "foot_x"):
                    self.assertAlmostEqual(pose[field], 0, places=7)

    def test_entire_stride_reaches_ankles_and_keeps_boot_soles_flat(self):
        for side in ("L", "R"):
            sign = 1 if side == "L" else -1
            for index in range(601):
                phase = (index / 600) % 1
                root_z = -.06 + .012 * math.cos(phase * math.tau * 2)
                if phase < .5:
                    y, lift = .2875 - 1.15 * phase, 0.0
                else:
                    p = (phase - .5) * 2
                    y, lift = -.2875 + .575 * p, .16 * math.sin(math.pi * p)
                pose = solve_leg(y, lift, root_z, side=side)
                self.assertTrue(pose["reachable"], (side, index))
                foot = leg_matrices(pose, root_z)["foot"]
                ankle = transform_point(foot, pose["pivots"]["ankle"])
                expected = (sign * .55, -.31 + y, .3 + lift)
                for actual, target in zip(ankle, expected):
                    self.assertAlmostEqual(actual, target, places=12)
                # Independently inspect actual sole vertices, not just angles.
                for sole_y in (-.3, .4):
                    sole = transform_point(foot, (sign * .55, sole_y, 0.0))
                    self.assertAlmostEqual(sole[2], lift, places=12)
                    self.assertAlmostEqual(sole[1], sole_y + y, places=12)

    def test_offset_rest_vectors_preserve_neutral_pose_on_matching_branch(self):
        pivots = {"hip": (.5, 0, 1.4), "knee": (.55, -.3, .9), "ankle": (.55, 0, .3)}
        pose = solve_leg(0, 0, 0, pivots=pivots, knee_direction="backward")
        for field in ("thigh_x", "shin_x", "foot_x"):
            self.assertAlmostEqual(pose[field], 0, places=12)
        ankle = transform_point(leg_matrices(pose, 0)["foot"], pivots["ankle"])
        for actual, expected in zip(ankle, pivots["ankle"]):
            self.assertAlmostEqual(actual, expected, places=12)

    def test_out_of_reach_target_is_reported_instead_of_claiming_support(self):
        pose = solve_leg(2, 0, 0)
        self.assertFalse(pose["reachable"])
        self.assertGreater(pose["target_error_m"], .5)

    def test_current_voxel_geometry_has_clearance_for_walk_and_attack_crouch(self):
        source = Path(__file__).resolve().parents[2] / "assets/characters/bosses/cairn/source/voxels.json"
        report = check_source(source, samples=120)
        self.assertEqual(report["frames_checked"], 242)
        self.assertEqual(report["rest_overlap_count"], 0)
        self.assertEqual(report["animated_overlap_count"], 0, report["bone_pair_summary"])
        self.assertTrue(report["pass"], report["issues"])


if __name__ == "__main__":
    unittest.main()

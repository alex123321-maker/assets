import unittest
import numpy as np
from tools.cairn.death_rubble import simulate, settle_supported_heap, supported_by_floor
from tools.cairn.author_death_motion import validate_linear_segments


class DeathRubbleTests(unittest.TestCase):
    def assert_safe(self, result):
        half = np.asarray(result["sizes"]) / 2
        a, b = np.triu_indices(len(half), 1)
        radius = (half[a] + half[b])[:, None]
        frames = result["frames"]
        for previous, current in zip(frames, frames[1:]):
            p = np.asarray(previous["centers"])
            q = np.asarray(current["centers"])
            # Exact slab intervals, rather than just endpoint checks: both
            # cubes move linearly between emitted collision keys.
            delta = p[a] - p[b]
            displacement = (q[a] - p[a]) - (q[b] - p[b])
            moving = np.abs(displacement) > 1e-12
            interior = radius - 1e-7
            impossible = (~moving) & (np.abs(delta) >= interior)
            divisor = np.where(moving, displacement, 1.0)
            t1 = (-interior - delta) / divisor
            t2 = (interior - delta) / divisor
            entry = np.max(np.where(moving, np.minimum(t1, t2), -np.inf), axis=1)
            departure = np.min(np.where(moving, np.maximum(t1, t2), np.inf), axis=1)
            intersect = (~np.any(impossible, axis=1)) & (np.maximum(entry, 0) < np.minimum(departure, 1))
            self.assertFalse(np.any(intersect), "Swept cube interiors overlap between keys")
            for fraction in (0.0, 0.25, 0.5, 0.75, 1.0):
                positions = p * (1 - fraction) + q * fraction
                self.assertTrue(np.all(positions[:, 2] >= half - 1e-7))
                self.assertFalse(np.any(np.all(np.abs(positions[a] - positions[b]) < radius - 1e-7, axis=1)))

    def test_stack_collapses_without_floor_or_cube_penetration(self):
        fragments = [{"id": f"{x}_{y}_{z}", "center": [x * .4, y * .4, (z + .5) * .4], "size": .4}
                     for z in range(6) for y in range(-1, 2) for x in range(-1, 2)]
        result = simulate(fragments, duration=3)
        self.assert_safe(result)
        initial = np.asarray(result["frames"][0]["centers"])
        final = np.asarray(result["frames"][-1]["centers"])
        self.assertLess(final[:, 2].mean(), initial[:, 2].mean() * .65)
        self.assertGreater(np.ptp(final[:, 0]) + np.ptp(final[:, 1]), np.ptp(initial[:, 0]) + np.ptp(initial[:, 1]))
        self.assertEqual(result, simulate(fragments, duration=3))

    def test_mixed_sizes_are_disjoint_through_complete_linear_sweeps(self):
        fragments = [{"id": "base", "center": [0, 0, .4], "size": .8}]
        fragments.extend({"id": f"cap{x}_{y}", "center": [x * .2, y * .2, .9], "size": .2}
                         for x in (-1.5, -.5, .5, 1.5) for y in (-1.5, -.5, .5, 1.5))
        fragments.append({"id": "crown", "center": [0, 0, 1.2], "size": .4})
        result = simulate(fragments, fps=60, duration=3)
        for frame in result['frames']:
            frame['centers'] = np.round(np.asarray(frame['centers']), decimals=10).tolist()
        self.assert_safe(result)
        validate_linear_segments(result)

    def test_validator_rejects_overlap_between_disjoint_endpoints(self):
        result = {'ids': ['a', 'b'], 'sizes': [1, 1], 'frames': [
            {'time': 0, 'centers': [[0, 0, .5], [1.2, 0, .5]]},
            {'time': 1, 'centers': [[0, 0, .5], [0, 1.2, .5]]}]}
        with self.assertRaisesRegex(ValueError, 'Swept overlap'):
            validate_linear_segments(result)

    def test_settling_falls_into_real_supported_heap_without_crossing(self):
        fragments = [{'id': f'{x}_{z}', 'center': [x*.4, 0, 1+(z+.5)*.4], 'size': .4}
                     for z in range(4) for x in (-1, 0, 1)]
        result = simulate(fragments, duration=.3)
        initial_tail = np.asarray(result['frames'][-1]['centers'])
        tail_start = len(result['frames'])
        settle_supported_heap(result)
        self.assert_safe(result)
        final = np.asarray(result['frames'][-1]['centers'])
        self.assertTrue(np.all(supported_by_floor(final, result['sizes'])))
        np.testing.assert_array_equal(initial_tail[:, :2], final[:, :2])
        for frame in result['frames'][tail_start:]:
            self.assertTrue(np.all(np.asarray(frame['centers'])[:, 2] <= initial_tail[:, 2] + 1e-10))
        self.assertEqual(result['frames'][-1]['centers'], result['frames'][-2]['centers'])

    def test_support_requires_vertical_face_area_and_chain_to_floor(self):
        centers = [[0, 0, .2], [0, 0, .6], [.4, 0, .6], [2, 0, 1.2]]
        np.testing.assert_array_equal(supported_by_floor(centers, [.4]*4), [True, True, False, False])

    def test_free_fall_and_floor_rebound(self):
        result = simulate([{"id": "stone", "center": [0, 0, 2], "size": .5}], duration=3)
        self.assert_safe(result)
        frames = result["frames"]
        at_half_second = min(frames, key=lambda f: abs(f["time"] - .5))
        self.assertAlmostEqual(at_half_second["centers"][0][2], 2 - 9.81 * .5 ** 2 / 2, delta=.05)
        heights = [f["centers"][0][2] for f in frames]
        self.assertTrue(any(b > a + .001 for a, b in zip(heights, heights[1:])))
        self.assertAlmostEqual(heights[-1], .25, places=7)

    def test_invalid_initial_intersections_rejected(self):
        with self.assertRaises(ValueError):
            simulate([{"id": "a", "center": [0, 0, .5], "size": 1},
                      {"id": "b", "center": [.3, 0, .5], "size": 1}])
        with self.assertRaises(ValueError):
            simulate([{"id": "a", "center": [0, 0, .2], "size": 1}])


if __name__ == "__main__":
    unittest.main()

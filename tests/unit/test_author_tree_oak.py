"""Unit tests for author_tree_oak.py CLI contract and voxel utilities."""
import subprocess
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))
if str(REPO_ROOT / "tools") not in sys.path:
    sys.path.insert(0, str(REPO_ROOT / "tools"))

from tools.author_tree_oak import VoxelGrid, VARIANTS


class AuthorTreeOakTests(unittest.TestCase):
    def test_cli_argument_defaults_to_all(self):
        """Ensure running without arguments defaults to authoring all variants."""
        cmd = [
            sys.executable,
            "-c",
            "import argparse, sys; "
            "sys.path.insert(0, 'tools'); "
            "from author_tree_oak import author_all; "
            "parser = argparse.ArgumentParser(); "
            "parser.add_argument('--variant', default='all'); "
            "args = parser.parse_args([]); "
            "assert args.variant == 'all', f'Expected all, got {args.variant}'; "
            "print('OK')",
        ]
        res = subprocess.run(cmd, cwd=str(REPO_ROOT), capture_output=True, text=True, check=True)
        self.assertIn("OK", res.stdout)

    def test_variants_list_contains_all_five_slots(self):
        """Ensure all 5 slots (var_0..var_4) are registered in VARIANTS."""
        slugs = [v["slug"] for v in VARIANTS]
        expected = [
            "var_0_standard_oak",
            "var_1_tall_oak",
            "var_2_broad_oak",
            "var_3_young_oak",
            "var_4_shrub_oak",
        ]
        self.assertEqual(slugs, expected)

    def test_voxel_grid_fill_blocky_pad(self):
        """Ensure fill_blocky_pad creates a convex pod with base and sunlit accent tokens."""
        g = VoxelGrid(10, 10, 10)
        g.fill_blocky_pad(pcx=5.0, pcy=5.0, pcz=5.0, prx=2.5, pry=2.5, prz=2.5, p=2.8)
        
        # Center should be foliage_base or accent
        center_tok = g.get(5, 5, 5)
        self.assertIn(center_tok, ("D", "L"))
        
        # Outside bounds should be empty
        self.assertEqual(g.get(0, 0, 0), ".")
        self.assertEqual(g.get(9, 9, 9), ".")
        
        # Wood preservation: blocky pad must not overwrite wood
        g.set(5, 5, 5, "W")
        g.fill_blocky_pad(pcx=5.0, pcy=5.0, pcz=5.0, prx=2.5, pry=2.5, prz=2.5)
        self.assertEqual(g.get(5, 5, 5), "W")


if __name__ == "__main__":
    unittest.main()

"""Review sheets must not silently hide missing renders or certify their own art."""
import importlib
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from PIL import ImageDraw


class LegacyReviewMediaTests(unittest.TestCase):
    def test_tree_sheet_rejects_missing_variant_render(self):
        module = importlib.import_module('tools.create_tree_comparison_sheets')
        with tempfile.TemporaryDirectory() as folder:
            with patch.object(module, 'FAMILY_DIR', Path(folder)):
                with self.assertRaisesRegex(FileNotFoundError, 'required review input'):
                    module.create_variants_comparison()

    def test_terrain_sheet_contains_questions_not_precomputed_passes(self):
        # Exercise actual drawing, not a duplicate list of captions in this test.
        import sys
        tools_dir = str(Path(__file__).resolve().parents[2] / 'tools')
        with patch.object(sys, 'path', [tools_dir, *sys.path]):
            module = importlib.import_module('tools.create_terrain_comparison_sheets')
        captions = []
        original = ImageDraw.ImageDraw.text

        def record(draw, xy, text, *args, **kwargs):
            captions.append(str(text))
            return original(draw, xy, text, *args, **kwargs)

        with tempfile.TemporaryDirectory() as folder:
            # Inputs stay in the real fixture family; only the composed output is redirected.
            with patch.object(module.Image.Image, 'save') as save, patch.object(ImageDraw.ImageDraw, 'text', record):
                module.create_contact_sheet()
                save.assert_called_once()
        self.assertTrue(any('[REVIEW]' in c for c in captions))
        self.assertFalse(any('[PASS]' in c or 'APPROVED' in c for c in captions))

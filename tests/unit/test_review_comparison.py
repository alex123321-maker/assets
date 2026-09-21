import copy
import json
import tempfile
import unittest
from pathlib import Path

from PIL import Image
from tools.review_comparison import compose, sha256, validate_pair


class ComparisonTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        settings = dict(camera_matrix=[[1, 0, 0, 0]], ortho_scale=6.51, lights=[],
                        world_color=[0, 0, 0], resolution=[640, 640],
                        color_management={'exposure': 0}, engine='test', blender_version='test')
        self.data = {'version': 1}
        for side, color in [('before', 'red'), ('after', 'green')]:
            source = self.root / f'{side}.json'
            source.write_text('{}')
            image = self.root / f'{side}.png'
            Image.new('RGB', (640, 640), color).save(image)
            self.data[side] = dict(source=source.name, source_sha256=sha256(source),
                                   image=image.name, image_sha256=sha256(image), settings=copy.deepcopy(settings))
        self.receipt = self.root / 'comparison.json'
        self.save()

    def save(self):
        self.receipt.write_text(json.dumps(self.data))

    def test_same_scene_composition_preserves_both_panels(self):
        target = self.root / 'pair.png'
        compose(self.root, self.receipt, target)
        with Image.open(target) as im:
            self.assertEqual(im.getpixel((100, 100)), (255, 0, 0))
            self.assertEqual(im.getpixel((800, 100)), (0, 128, 0))

    def test_mismatched_camera_or_color_management_is_rejected(self):
        for key, value in [('ortho_scale', 6.2775), ('color_management', {'exposure': 1})]:
            with self.subTest(key=key):
                original = self.data['after']['settings'][key]
                self.data['after']['settings'][key] = value
                self.save()
                with self.assertRaisesRegex(ValueError, 'settings differ'):
                    compose(self.root, self.receipt, self.root / 'pair.png')
                self.data['after']['settings'][key] = original

    def test_replaced_source_or_image_is_rejected(self):
        for name in ('after.json', 'after.png'):
            path = self.root / name
            original = path.read_bytes()
            path.write_bytes(b'replaced')
            with self.assertRaisesRegex(ValueError, 'Stale comparison'):
                validate_pair(self.root, self.receipt)
            path.write_bytes(original)

    def test_resolution_mismatch_is_rejected(self):
        self.data['after']['settings']['resolution'] = [12, 12]
        self.save()
        with self.assertRaisesRegex(ValueError, 'resolution'):
            validate_pair(self.root, self.receipt)


if __name__ == '__main__':
    unittest.main()

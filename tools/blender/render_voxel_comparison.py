"""Re-render two voxel sources in ONE frozen scene; no artistic verdicts."""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

import bpy
from mathutils import Vector

sys.path.insert(0, str(Path(__file__).resolve().parent))
from build_voxel_asset import build_objects, clear_scene, setup_review_scene, look_at

ROOT = Path(__file__).resolve().parents[2]


def snapshot(scene):
    # Capture actual settings after rendering each side, not a requested preset.
    return {
        'camera_matrix': [list(row) for row in scene.camera.matrix_world],
        'ortho_scale': scene.camera.data.ortho_scale,
        'lights': [{
            'type': o.data.type, 'energy': o.data.energy, 'color': list(o.data.color),
            'matrix': [list(row) for row in o.matrix_world],
        } for o in sorted(scene.objects, key=lambda o: o.name) if o.type == 'LIGHT'],
        'world_color': list(scene.world.color),
        'resolution': [scene.render.resolution_x, scene.render.resolution_y],
        'color_management': {key: getattr(scene.view_settings, key) for key in
                             ('view_transform', 'look', 'exposure', 'gamma')},
        'engine': scene.render.engine, 'blender_version': bpy.app.version_string,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--before', type=Path, required=True)
    parser.add_argument('--after', type=Path, required=True)
    parser.add_argument('--review-dir', type=Path, required=True)
    args = parser.parse_args(sys.argv[sys.argv.index('--') + 1:])
    paths = [p.resolve() for p in (args.before, args.after, args.review_dir)]
    if not all(p.is_relative_to(ROOT) for p in paths):
        raise ValueError('Comparison paths must stay inside repository')
    before, after, review_dir = paths
    clear_scene()
    groups = [build_objects(json.loads(p.read_text(encoding='utf-8')))[0] for p in (before, after)]
    if not all(groups):
        raise ValueError('Both comparison sources must produce geometry')
    bpy.context.view_layer.update()
    # Union bounds produce a single camera that fits both sources at the same scale.
    camera, center, extent = setup_review_scene(groups[0] + groups[1])
    camera.location = center + Vector((extent * 2.6, -extent * 2.6, extent * 2.2))
    look_at(camera, center)
    review_dir.mkdir(parents=True, exist_ok=True)
    receipt = {'version': 1}
    for side, source, active in zip(('before', 'after'), (before, after), groups):
        for group in groups:
            for obj in group:
                obj.hide_render = group is not active
        image = review_dir / f'comparison_{side}.png'
        bpy.context.scene.render.filepath = str(image)
        bpy.ops.render.render(write_still=True)
        receipt[side] = {
            'source': source.relative_to(ROOT).as_posix(),
            'source_sha256': hashlib.sha256(source.read_bytes().replace(b'\r\n', b'\n')).hexdigest(),
            'image': image.relative_to(ROOT).as_posix(),
            'image_sha256': hashlib.sha256(image.read_bytes()).hexdigest(),
            'settings': snapshot(bpy.context.scene),
        }
    (review_dir / 'comparison.json').write_text(json.dumps(receipt, indent=2) + '\n', encoding='utf-8')


if __name__ == '__main__':
    main()

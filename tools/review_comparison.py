"""Compose neutral comparisons only from a verified pair of fixed-scene renders."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

from PIL import Image, ImageDraw


def sha256(path: Path) -> str:
    raw = path.read_bytes()
    if path.suffix == '.json':
        raw = raw.replace(b'\r\n', b'\n')
    return hashlib.sha256(raw).hexdigest()


def checked_path(root: Path, name: str) -> Path:
    if not isinstance(name, str) or not name or Path(name).is_absolute():
        raise ValueError('Comparison paths must be repository-relative')
    path = (root / name).resolve()
    if not path.is_relative_to(root.resolve()):
        raise ValueError('Comparison path leaves repository')
    return path


def validate_pair(root: Path, receipt: Path) -> dict:
    data = json.loads(receipt.read_text(encoding='utf-8'))
    if data.get('version') != 1:
        raise ValueError('Unsupported comparison receipt')
    for side in ('before', 'after'):
        row = data[side]
        settings = row['settings']
        for field in ('camera_matrix', 'ortho_scale', 'lights', 'world_color',
                      'resolution', 'color_management', 'engine', 'blender_version'):
            if field not in settings:
                raise ValueError(f'Missing comparison render setting: {field}')
        for kind in ('source', 'image'):
            if sha256(checked_path(root, row[kind])) != row[kind + '_sha256']:
                raise ValueError(f'Stale comparison {side} {kind}')
        with Image.open(checked_path(root, row['image'])) as im:
            im.load()
            if list(im.size) != settings['resolution']:
                raise ValueError('Comparison resolution does not match image')
    if data['before']['settings'] != data['after']['settings']:
        raise ValueError('Comparison cameras/lighting/render settings differ')
    return data


def compose(root: Path, receipt: Path, output: Path) -> None:
    data = validate_pair(root, receipt)
    panels = []
    for side in ('before', 'after'):
        with Image.open(checked_path(root, data[side]['image'])) as im:
            panels.append(im.convert('RGB'))
    width, height = panels[0].size
    canvas = Image.new('RGB', (width * 2 + 48, height + 104), (24, 26, 30))
    draw = ImageDraw.Draw(canvas)
    draw.text((16, 12), 'BEFORE / AFTER | Shared camera, lighting and scale', fill='white')
    for i, (side, panel) in enumerate(zip(('before', 'after'), panels)):
        x = 16 + i * (width + 16)
        draw.text((x, 34), side.upper() + ' source: ' + data[side]['source_sha256'][:12], fill='white')
        canvas.paste(panel, (x, 56))
    draw.text((16, height + 72), 'Re-rendered source snapshots. Visual assessment is recorded separately.', fill='white')
    output.parent.mkdir(parents=True, exist_ok=True)
    canvas.save(output)

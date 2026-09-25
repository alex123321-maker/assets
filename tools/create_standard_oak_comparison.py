"""Re-render and compose Standard Oak before/after with fixed comparison settings."""
from pathlib import Path
import subprocess

from review_comparison import compose

ROOT = Path(__file__).resolve().parents[1]
PACKAGE = Path('assets/environment/tree_oak/var_0_standard_oak')


def generate_comparison() -> Path:
    subprocess.run([
        'blender', '--background', '--factory-startup', '--python-exit-code', '1', '--python',
        'tools/blender/render_voxel_comparison.py', '--',
        '--before', (PACKAGE / 'references/before_voxels.json').as_posix(),
        '--after', (PACKAGE / 'source/voxels.json').as_posix(),
        '--review-dir', (PACKAGE / 'review').as_posix(),
    ], cwd=ROOT, check=True)
    review = ROOT / PACKAGE / 'review'
    output = review / 'before_after.png'
    compose(ROOT, review / 'comparison.json', output)
    return output


if __name__ == '__main__':
    print(generate_comparison())

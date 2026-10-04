"""Author deterministic collision-safe death trajectories from the voxel source.

This is an explicit source-authoring utility, not a build recipe: the resulting
JSON is an immutable animation input until the artist regenerates it.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import sys
import time

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
from tools.cairn.death_rubble import simulate, settle_supported_heap, supported_by_floor
from tools.cairn.model_data import decode, fragments_for


def validate_linear_segments(result, tolerance=1e-7):
    """Analytic swept-volume and floor measurements, without art verdicts."""
    half = np.asarray(result['sizes'], dtype=float) / 2
    ia, ib = np.triu_indices(len(half), 1)
    radius = (half[ia] + half[ib])[:, None] - tolerance
    max_floor_penetration = 0.0
    checked = 0
    for previous, current in zip(result['frames'], result['frames'][1:]):
        p = np.asarray(previous['centers'], dtype=float)
        q = np.asarray(current['centers'], dtype=float)
        floor_penetration = max(float(np.max(half - p[:, 2])), float(np.max(half - q[:, 2])))
        max_floor_penetration = max(max_floor_penetration, floor_penetration)
        if floor_penetration > tolerance:
            raise ValueError(f'Floor penetration at {current["time"]}')
        delta = p[ia] - p[ib]
        displacement = (q[ia] - p[ia]) - (q[ib] - p[ib])
        candidates = np.flatnonzero(np.all(np.abs(delta) <= radius + np.abs(displacement), axis=1))
        delta, displacement = delta[candidates], displacement[candidates]
        pair_radius = radius[candidates]
        moving = np.abs(displacement) > 1e-12
        impossible = (~moving) & (np.abs(delta) >= pair_radius)
        divisor = np.where(moving, displacement, 1.0)
        first = (-pair_radius - delta) / divisor
        last = (pair_radius - delta) / divisor
        entry = np.max(np.where(moving, np.minimum(first, last), -np.inf), axis=1)
        departure = np.min(np.where(moving, np.maximum(first, last), np.inf), axis=1)
        overlap = (~np.any(impossible, axis=1)) & (np.maximum(entry, 0) < np.minimum(departure, 1))
        if np.any(overlap):
            pair = int(candidates[np.flatnonzero(overlap)[0]])
            raise ValueError(f'Swept overlap {result["ids"][ia[pair]]}/{result["ids"][ib[pair]]} during {previous["time"]}..{current["time"]}')
        checked += 1
    return {'checked_linear_segments': checked,
            'swept_penetration_tolerance_m': tolerance,
            'max_floor_penetration_m': max_floor_penetration}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', type=Path, default=ROOT / 'assets/characters/bosses/cairn/source/voxels.json')
    parser.add_argument('--output', type=Path, default=ROOT / 'assets/characters/bosses/cairn/source/death_motion.json')
    args = parser.parse_args()
    raw = args.source.read_bytes()
    spec = json.loads(raw)
    fragments, _ = fragments_for(decode(spec), spec['voxel_size_m'])
    inputs = [{k: fragment[k] for k in ('id', 'center', 'size')} for fragment in fragments]
    started = time.perf_counter()
    print(f'Simulating {len(inputs)} cubic fragments, gravity phase=2.1s, fps=30, seed=1701', flush=True)
    result = simulate(inputs, fps=30, duration=2.1, seed=1701)
    settle_supported_heap(result, fps=30)
    print(f'Simulation: {time.perf_counter()-started:.2f}s, {len(result["frames"])} key times, {result["metadata"]["collision_events"]} contact events', flush=True)
    result['schema_version'] = 1
    result['input_sha256'] = hashlib.sha256(raw.replace(b'\r\n',b'\n')).hexdigest()
    result['source'] = args.source.resolve().relative_to(ROOT).as_posix()
    # Centre precision is much finer than runtime float32 precision. Keep all
    # collision times intact, then validate the actual serialized coordinates.
    for frame in result['frames']:
        frame['centers'] = np.round(np.asarray(frame['centers']), decimals=10).tolist()
    result['metadata']['coordinate_decimal_places'] = 10
    result['metadata']['measurements'] = validate_linear_segments(result)
    first = np.asarray(result['frames'][0]['centers'])
    final = np.asarray(result['frames'][-1]['centers'])
    previous = np.asarray(result['frames'][-2]['centers'])
    sizes = np.asarray(result['sizes'])
    speed = np.linalg.norm(final - previous, axis=1) / (result['frames'][-1]['time'] - result['frames'][-2]['time'])
    support = supported_by_floor(final, sizes)
    result['metadata']['measurements'].update({
        'supported_to_floor_fragments': int(np.count_nonzero(support)),
        'unsupported_fragments': int(np.count_nonzero(~support)),
        'max_final_speed_m_s': float(speed.max()),
        'center_of_mass_initial_z_m': float(np.average(first[:, 2], weights=sizes ** 3)),
        'center_of_mass_final_z_m': float(np.average(final[:, 2], weights=sizes ** 3))})
    if not np.all(support) or speed.max() > 1e-7:
        raise ValueError('Final heap is unsupported or still moving')
    if hashlib.sha256(args.source.read_bytes().replace(b'\r\n',b'\n')).hexdigest() != result['input_sha256']:
        raise RuntimeError('Voxel source changed during simulation; rerun against final geometry')
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, separators=(',', ':')) + '\n', encoding='utf-8')
    print(f'Wrote {args.output}: {args.output.stat().st_size} bytes; total {time.perf_counter()-started:.2f}s', flush=True)


if __name__ == '__main__':
    main()

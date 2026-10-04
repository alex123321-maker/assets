"""Deterministic, axis-aligned cubic rubble with continuous collision detection.

Coordinates are Blender metres, Z up. Frames include collision times between
regular samples: retain their exact ``time * fps`` as fractional Blender keys
and use LINEAR interpolation. Decimating these keys invalidates swept safety.
No object physics, hidden support planes, rotation, or global lift is used.
"""
from __future__ import annotations

import math
import random
import numpy as np


def simulate(fragments, fps=30, duration=3.0, seed=1701):
    """Return ordered fragment IDs, safe linear frames, and solver metadata.

    Each frame contains time and centers in input order. The fragments retain
    their original sizes and identity. Axis-aligned impacts dissipate velocity;
    only floor impacts rebound, with low restitution, before settling.
    """
    if not fragments or fps <= 0 or duration <= 0:
        raise ValueError("Nonempty fragments and positive fps/duration required")
    ids = [f["id"] for f in fragments]
    if len(set(ids)) != len(ids):
        raise ValueError("Fragment IDs must be unique")
    p = np.asarray([f["center"] for f in fragments], dtype=float)
    sizes = np.asarray([f["size"] for f in fragments], dtype=float)
    if p.shape != (len(ids), 3) or not np.isfinite(p).all() or not np.isfinite(sizes).all() or np.any(sizes <= 0):
        raise ValueError("Finite centers and positive cubic sizes required")
    half = sizes / 2.0
    if np.any(p[:, 2] < half - 1e-8):
        raise ValueError("Initial cube intersects floor")
    ia, ib = np.triu_indices(len(ids), 1)
    radius = (half[ia] + half[ib])[:, None]
    if np.any(np.all(np.abs(p[ia] - p[ib]) < radius - 1e-8, axis=1)):
        raise ValueError("Initial cubes overlap")
    rng = random.Random(seed)
    theta = rng.uniform(-math.pi, math.pi)
    direction = np.array([math.cos(theta), math.sin(theta)])
    origin = np.average(p[:, :2], axis=0, weights=sizes ** 3)
    velocity = np.zeros_like(p)
    # Gradual lateral disassembly: outer stones spread out; upper layers slide
    # farther. Vertically aligned stones separate without an upward explosion.
    velocity[:, :2] = (p[:, :2] - origin) * 0.62 + p[:, 2, None] * direction[None, :] * 0.42
    frames = [{"time": 0.0, "centers": p.tolist()}]
    time = 0.0
    impacts = 0
    max_events = 200000
    steps = math.ceil(duration * fps * 2)
    dt = duration / steps
    epsilon = 1e-10

    def record(at):
        if at > frames[-1]["time"] + epsilon:
            frames.append({"time": float(at), "centers": p.tolist()})

    for _ in range(steps):
        velocity[:, 2] -= 9.81 * dt
        # Ground contact is actual floor contact; no raised support proxy.
        grounded = (p[:, 2] <= half + 1e-9) & (velocity[:, 2] < 0)
        velocity[grounded, 2] = 0.0
        velocity[grounded, :2] *= math.exp(-5.0 * dt)
        remaining = dt
        while remaining > epsilon:
            if impacts > max_events:
                raise RuntimeError("Rubble CCD event budget exceeded")
            delta = p[ia] - p[ib]
            relative = velocity[ia] - velocity[ib]
            # Conservative swept broad phase: most of the N*(N-1)/2 pairs
            # cannot approach a shared volume during this short interval.
            # Keeping the complete pair ordering makes trajectories stable.
            candidates = np.flatnonzero(np.all(np.abs(delta) <= radius + np.abs(relative) * remaining + 1e-9, axis=1))
            pair_a, pair_b = ia[candidates], ib[candidates]
            delta, relative = delta[candidates], relative[candidates]
            pair_radius = radius[candidates]
            moving = np.abs(relative) > epsilon
            # A stationary separating axis, including face contact, prevents
            # volumetric intersection for the whole linear segment.
            blocked_axis = (~moving) & (np.abs(delta) >= pair_radius - 1e-9)
            divisor = np.where(moving, relative, 1.0)
            a = (-pair_radius - delta) / divisor
            b = (pair_radius - delta) / divisor
            enter = np.where(moving, np.minimum(a, b), -np.inf)
            leave = np.where(moving, np.maximum(a, b), np.inf)
            entry = np.max(enter, axis=1)
            departure = np.min(leave, axis=1)
            valid = (~np.any(blocked_axis, axis=1)) & (entry >= -1e-9) & (entry <= departure + epsilon) & (departure > epsilon) & (entry <= remaining + epsilon)
            pair_times = np.where(valid, np.maximum(entry, 0.0), np.inf)
            descending = velocity[:, 2] < -epsilon
            floor_times = np.where(descending, np.maximum(0.0, (p[:, 2] - half) / np.where(descending, -velocity[:, 2], 1.0)), np.inf)
            next_time = min(remaining, float(np.min(pair_times, initial=np.inf)), float(np.min(floor_times, initial=np.inf)))
            if next_time > epsilon:
                p += velocity * next_time
                time += next_time
                remaining -= next_time
                record(time)
            hit_pairs = np.flatnonzero(pair_times <= next_time + epsilon)
            hit_floor = np.flatnonzero(floor_times <= next_time + epsilon)
            if not len(hit_pairs) and not len(hit_floor):
                break
            for pair in hit_pairs:
                axis = int(np.argmax(enter[pair]))
                velocity[pair_a[pair], axis] = 0.0
                velocity[pair_b[pair], axis] = 0.0
            for cube in hit_floor:
                speed = -velocity[cube, 2]
                velocity[cube, 2] = speed * 0.17 if speed > 0.8 else 0.0
                velocity[cube, :2] *= 0.64
                p[cube, 2] = half[cube]
            impacts += len(hit_pairs) + len(hit_floor)
        # Floating point intervals can end just below the requested sample.
        expected = (_ + 1) * dt
        if expected > time + epsilon:
            p += velocity * (expected - time)
            time = expected
            record(time)
    return {"ids": ids, "sizes": sizes.tolist(), "frames": frames,
            "metadata": {"fps": fps, "duration": duration, "seed": seed,
                         "gravity": 9.81, "floor_z": 0.0,
                         "rotation": "axis_aligned_zero", "interpolation": "LINEAR",
                         "retain_fractional_collision_keys": True,
                         "collision_events": impacts}}


def supported_by_floor(centers, sizes, tolerance=1e-7):
    """Return the actual vertical support chain, requiring positive XY area."""
    p = np.asarray(centers, dtype=float)
    half = np.asarray(sizes, dtype=float) / 2
    supported = np.zeros(len(half), dtype=bool)
    for i in np.argsort(p[:, 2]):
        beneath = np.abs((p[i, 2] - half[i]) - (p[:, 2] + half)) <= tolerance
        beneath &= np.all(np.abs(p[i, :2] - p[:, :2]) < (half[i] + half[:, None]) - tolerance, axis=1)
        beneath &= p[:, 2] < p[i, 2]
        supported[i] = p[i, 2] - half[i] <= tolerance or np.any(supported[beneath])
    return supported


def settle_supported_heap(result, fps=30, hold=.2):
    """Append a downward gravity-paced packing stage with actual floor support.

    Lateral scatter ends at this stage. The vertical order of every pair with
    overlapping XY projections stays unchanged. Compute each stone's lowest
    resting position from already placed lower stones, then animate all drops
    with the same increasing quadratic factor. Both ends and every interpolated
    position are disjoint; no cube rises or shifts through another cube.
    """
    p = np.asarray(result['frames'][-1]['centers'], dtype=float)
    sizes = np.asarray(result['sizes'], dtype=float)
    half = sizes / 2
    target = p.copy()
    placed = []
    for i in np.argsort(p[:, 2]):
        candidates = np.asarray(placed, dtype=int)
        if len(candidates):
            overlap = np.all(np.abs(p[i, :2] - p[candidates, :2]) < (half[i] + half[candidates, None]) - 1e-7, axis=1)
            candidates = candidates[overlap]
        support_height = float(np.max(target[candidates, 2] + half[candidates], initial=0.0))
        target[i, 2] = half[i] + support_height
        if target[i, 2] > p[i, 2] + 1e-7:
            raise ValueError('Packing would raise a stone: input cube volumes intersect')
        placed.append(int(i))
    drop = np.maximum(0, p[:, 2] - target[:, 2])
    maximum_drop = float(drop.max())
    duration = max(.35, math.sqrt(2 * maximum_drop / 9.81))
    start = result['frames'][-1]['time']
    steps = math.ceil(duration * fps * 2)
    for index in range(1, steps + 1):
        progress = index / steps
        centers = p.copy()
        centers[:, 2] = p[:, 2] - drop * progress ** 2
        if index == steps:
            centers = target.copy()
        result['frames'].append({'time': start + duration * progress, 'centers': centers.tolist()})
    result['frames'].append({'time': start + duration + hold, 'centers': target.tolist()})
    result['metadata'].update({'duration': start + duration + hold,
                               'gravity_ccd_duration': start,
                               'settling_strategy': 'downward_vertical_packing',
                               'settling_duration': duration,
                               'settled_hold_duration': hold,
                               'maximum_settling_drop_m': maximum_drop})
    if not np.all(supported_by_floor(target, sizes)):
        raise ValueError('Packing did not produce a complete floor support chain')
    return result

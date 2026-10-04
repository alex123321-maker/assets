"""Pure Python two-link Cairn leg IK with explicit rest-pivot conventions.

Blender coordinates: X lateral, +Y forward, Z up. Local bone X rotation is
world X in the authored rig (all bone tails point along +Y). ``solve_leg``
returns radians for thigh_x, shin_x and foot_x. Foot counterrotation leaves
its world orientation horizontal. Targets are relative to the rest ankle.

The recommended rear-edge profile moves *all three* pivots to Y=-0.31,
preserving vertical rest link vectors. Moving just the knee changes the rest
link angles and requires the general rest-angle correction implemented here.
"""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path


REAR_EDGE_Y = -0.31


def pivot_definitions(side="L", *, pivot_y=REAR_EDGE_Y):
    sign = 1.0 if side == "L" else -1.0
    if side not in ("L", "R"):
        raise ValueError("side must be L or R")
    return {"hip": (sign * .5, pivot_y, 1.4),
            "knee": (sign * .55, pivot_y, .9),
            "ankle": (sign * .55, pivot_y, .3)}


def solve_leg(y: float, lift: float, root_z: float, *, side="L",
              pivots=None, knee_direction="forward"):
    """Return a JSON-ready IK pose and target error, with no silent reach claim.

    For each rest vector v=(dy,dz), alpha=atan2(dy,-dz). The desired absolute
    thigh angle is beta +/- acos((L1²+d²-L2²)/(2 L1 d)). Subtract alpha1 to
    get thigh_x. Subtract alpha2-alpha1 from the desired relative lower-leg
    angle to get shin_x. Foot_x=-(thigh_x+shin_x).
    """
    values = (y, lift, root_z)
    if any(isinstance(value, bool) or not isinstance(value, (int, float))
           or not math.isfinite(value) for value in values):
        raise ValueError("leg target values must be finite numbers")
    pivots = pivots or pivot_definitions(side)
    hip, knee, ankle = (tuple(pivots[name]) for name in ("hip", "knee", "ankle"))
    if knee_direction not in ("forward", "backward"):
        raise ValueError("knee_direction must be forward or backward")
    v1 = (knee[1] - hip[1], knee[2] - hip[2])
    v2 = (ankle[1] - knee[1], ankle[2] - knee[2])
    l1, l2 = math.hypot(*v1), math.hypot(*v2)
    if min(l1, l2) <= 1e-12:
        raise ValueError("leg links must have positive length")
    rest1, rest2 = math.atan2(v1[0], -v1[1]), math.atan2(v2[0], -v2[1])
    target = (ankle[0], ankle[1] + y, ankle[2] + lift)
    hip_world = (hip[0], hip[1], hip[2] + root_z)
    dy, dz = target[1] - hip_world[1], target[2] - hip_world[2]
    target_distance = math.hypot(dy, dz)
    distance = min(l1 + l2, max(abs(l1 - l2) + 1e-12, target_distance))
    beta = math.atan2(dy, -dz)
    cosine = (l1 * l1 + distance * distance - l2 * l2) / (2 * l1 * distance)
    offset = math.acos(max(-1.0, min(1.0, cosine)))
    upper = beta + (offset if knee_direction == "forward" else -offset)
    knee_world = (knee[0], hip_world[1] + l1 * math.sin(upper),
                  hip_world[2] - l1 * math.cos(upper))
    reached_y = hip_world[1] + distance * math.sin(beta)
    reached_z = hip_world[2] - distance * math.cos(beta)
    lower = math.atan2(reached_y - knee_world[1], knee_world[2] - reached_z)
    thigh_x = upper - rest1
    shin_x = (lower - upper) - (rest2 - rest1)
    foot_x = -(thigh_x + shin_x)
    error = math.hypot(reached_y - target[1], reached_z - target[2])
    return {"thigh_x": thigh_x, "shin_x": shin_x, "foot_x": foot_x,
            "target_world": target, "ankle_world": (ankle[0], reached_y, reached_z),
            "knee_world": knee_world, "target_error_m": error,
            "reachable": error <= 1e-8, "pivots": pivots,
            "rest_link_angles": (rest1, rest2)}


def _multiply(a, b):
    return [[sum(a[i][k] * b[k][j] for k in range(4)) for j in range(4)] for i in range(4)]


def _translation(position):
    return [[1, 0, 0, position[0]], [0, 1, 0, position[1]],
            [0, 0, 1, position[2]], [0, 0, 0, 1]]


def _pivot_rotation(pivot, angle):
    c, s = math.cos(angle), math.sin(angle)
    rotation = [[1, 0, 0, 0], [0, c, -s, 0], [0, s, c, 0], [0, 0, 0, 1]]
    return _multiply(_multiply(_translation(pivot), rotation),
                     _translation(tuple(-v for v in pivot)))


def leg_matrices(pose, root_z):
    """Rest-world to posed-world matrices matching the hierarchical rig."""
    hip, knee, ankle = (pose["pivots"][name] for name in ("hip", "knee", "ankle"))
    thigh = _multiply(_translation((0, 0, root_z)), _pivot_rotation(hip, pose["thigh_x"]))
    shin = _multiply(thigh, _pivot_rotation(knee, pose["shin_x"]))
    foot = _multiply(shin, _pivot_rotation(ankle, pose["foot_x"]))
    return {"thigh": thigh, "shin": shin, "foot": foot}


def check_source(source: Path, *, pivot_y=REAR_EDGE_Y, samples=60):
    """Check actual lattice cube poses for walk and crouch; writes no files.

    This isolates leg kinematics: other body parts translate with root only.
    Collision findings remain failures; no body geometry is omitted.
    """
    try:
        from .validate_voxel_motion import validate_asset
    except ImportError:
        from validate_voxel_motion import validate_asset
    spec = json.loads(Path(source).read_text(encoding="utf-8"))
    step = spec["voxel_size_m"]
    cubes = []
    for name, part in spec["parts"].items():
        ox, oy, oz = part["origin_grid"]
        for iy, layer in enumerate(part["layers_y"]):
            for iz, row in enumerate(layer):
                for ix, token in enumerate(row):
                    if token != ".":
                        x, y, z = ox + ix, oy + iy, oz + iz
                        cubes.append({"id": f"{x}:{y}:{z}", "bone": name, "size": step,
                                      "center": [(x + .5) * step, -(z + .5) * step, (y + .5) * step]})
    frames, worst_error = [], 0.0
    for clip in ("walk", "crouch"):
        for index in range(samples + 1):
            t = index / samples
            root_z = -.06 + .012 * math.cos(t * math.tau * 2) if clip == "walk" else -.045 - .095 * t
            mappings = {name: _translation((0, 0, root_z)) for name in spec["parts"]}
            for side, phase in (("L", t), ("R", (t + .5) % 1)):
                if clip == "walk":
                    phase %= 1
                    if phase < .5:
                        y, lift = .2875 - 1.15 * phase, 0.0
                    else:
                        p = (phase - .5) * 2
                        y, lift = -.2875 + .575 * p, .16 * math.sin(math.pi * p)
                else:
                    y, lift = 0.0, 0.0
                pose = solve_leg(y, lift, root_z, side=side, pivots=pivot_definitions(side, pivot_y=pivot_y))
                worst_error = max(worst_error, pose["target_error_m"])
                mappings.update({f"{name}.{side}": matrix for name, matrix in leg_matrices(pose, root_z).items()})
            frames.append({"frame": f"{clip}:{index}", "bone_matrices": mappings})
    report = validate_asset(cubes, frames, max_issues=100_000)
    summary = {}
    for finding in report["issues"]:
        key = " / ".join(sorted(finding.get("bones", [])))
        item = summary.setdefault(key, {"count": 0, "maximum_depth_m": 0.0})
        item["count"] += 1
        if finding.get("depth_m", 0.0) > item["maximum_depth_m"]:
            item["maximum_depth_m"] = finding["depth_m"]
            item["worst_frame"] = finding.get("frame")
            item["worst_pair"] = finding.get("pair")
    report["bone_pair_summary"] = summary
    report["summary_complete"] = not report["issues_truncated"]
    report["issues"] = report["issues"][:30]
    report["issues_truncated"] = report["issue_count"] > len(report["issues"])
    report["maximum_target_error_m"] = worst_error
    report["pivot_y_m"] = pivot_y
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check-source", type=Path)
    parser.add_argument("--pivot-y", type=float, default=REAR_EDGE_Y)
    parser.add_argument("--samples", type=int, default=60)
    args = parser.parse_args()
    if args.samples < 1:
        parser.error("samples must be positive")
    if args.check_source:
        report = check_source(args.check_source, pivot_y=args.pivot_y, samples=args.samples)
        print(json.dumps(report, indent=2))
        return 0 if report["pass"] else 1
    else:
        print(json.dumps(solve_leg(0, 0, -.045), indent=2))
        return 0


if __name__ == "__main__":
    raise SystemExit(main())

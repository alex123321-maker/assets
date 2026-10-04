"""Validate cube occupancy and sampled motion without Blender or third-party deps.

``validate_asset(cubes, frames, tolerance=1e-5)`` returns a JSON-ready report.
Each cube is ``{id, center: [x,y,z], size: scalar, bone: name}``, in Blender
Z-up metres. A frame is either:

* ``{frame, bone_matrices: {bone: 4x4}}``: matrices deform rest-world points
  into posed-world points (world @ pose @ inverse(rest)); or
* ``{frame, cube_matrices: {id: 4x4}}``: each matrix maps a cube-local unit
  cube, centred at zero, into world space. Matrix columns include cube size.

Matrices must preserve cubes: translation, orthogonal rotation/reflection,
and uniform scale are allowed; shear and unequal axis scales are rejected.
Face/edge/point contact and penetration <= tolerance are allowed. Rest pairs
are all checked. For bone_matrices, same-bone pairs are invariant after rest
validation and need not be checked again. Per-cube matrices check all pairs.
Only the supplied samples are validated; this does not prove safety between
samples. No files are written by the import interface.
"""

from __future__ import annotations

import argparse
from collections import defaultdict
import itertools
import json
import math
from pathlib import Path
import statistics
from typing import Any, Iterable, Sequence


Vector = tuple[float, float, float]
IDENTITY_AXES: tuple[Vector, Vector, Vector] = (
    (1.0, 0.0, 0.0), (0.0, 1.0, 0.0), (0.0, 0.0, 1.0)
)


def _dot(a: Vector, b: Vector) -> float:
    return sum(x * y for x, y in zip(a, b))


def _cross(a: Vector, b: Vector) -> Vector:
    return (a[1] * b[2] - a[2] * b[1],
            a[2] * b[0] - a[0] * b[2],
            a[0] * b[1] - a[1] * b[0])


def _numbers(value: Any, count: int, label: str) -> tuple[float, ...]:
    if not isinstance(value, (list, tuple)) or len(value) != count:
        raise ValueError(f"{label} must have {count} numbers")
    if any(isinstance(x, bool) or not isinstance(x, (int, float))
           or not math.isfinite(x) for x in value):
        raise ValueError(f"{label} must contain finite numbers")
    return tuple(float(x) for x in value)


class Box:
    __slots__ = ("id", "bone", "center", "axes", "half_size", "low", "high")

    def __init__(self, cube_id: str, bone: str, center: Vector,
                 axes: tuple[Vector, Vector, Vector], half_size: float):
        self.id = cube_id
        self.bone = bone
        self.center = center
        self.axes = axes
        self.half_size = half_size
        extent = tuple(half_size * sum(abs(axis[i]) for axis in axes)
                       for i in range(3))
        self.low = tuple(center[i] - extent[i] for i in range(3))
        self.high = tuple(center[i] + extent[i] for i in range(3))


def _rest_boxes(cubes: Sequence[dict[str, Any]]) -> list[Box]:
    if not isinstance(cubes, (list, tuple)) or not cubes:
        raise ValueError("cubes must be a nonempty array")
    seen: set[str] = set()
    boxes = []
    for index, cube in enumerate(cubes):
        if not isinstance(cube, dict):
            raise ValueError(f"cube {index} must be an object")
        cube_id = cube.get("id")
        if not isinstance(cube_id, str) or not cube_id:
            raise ValueError(f"cube {index}: id must be a nonempty string")
        if cube_id in seen:
            raise ValueError(f"duplicate cube id: {cube_id}")
        seen.add(cube_id)
        bone = cube.get("bone")
        if not isinstance(bone, str) or not bone:
            raise ValueError(f"cube {cube_id}: bone must be a nonempty string")
        center = _numbers(cube.get("center"), 3, f"cube {cube_id} center")
        size = cube.get("size")
        if (isinstance(size, bool) or not isinstance(size, (int, float))
                or not math.isfinite(size) or size <= 0):
            raise ValueError(f"cube {cube_id}: size must be a positive scalar")
        boxes.append(Box(cube_id, bone, center, IDENTITY_AXES, float(size) / 2))
    return boxes


def _matrix(value: Any, label: str):
    if not isinstance(value, (list, tuple)) or len(value) != 4:
        raise ValueError(f"{label} must be a 4x4 row-major matrix")
    rows = tuple(_numbers(row, 4, label) for row in value)
    if any(abs(rows[3][i] - target) > 1e-8
           for i, target in enumerate((0.0, 0.0, 0.0, 1.0))):
        raise ValueError(f"{label} is not affine")
    columns = tuple(tuple(rows[r][c] for r in range(3)) for c in range(3))
    lengths = tuple(math.sqrt(_dot(axis, axis)) for axis in columns)
    if min(lengths) <= 1e-12:
        raise ValueError(f"{label} has a degenerate axis")
    axes = tuple(tuple(x / length for x in axis)
                 for axis, length in zip(columns, lengths))
    if any(abs(_dot(axes[a], axes[b])) > 1e-6
           for a, b in ((0, 1), (0, 2), (1, 2))):
        raise ValueError(f"{label} shears the cube")
    # Axis equality is relative: collision tolerance is measured in metres.
    if max(lengths) - min(lengths) > 1e-6 * max(lengths):
        raise ValueError(f"{label} scales cube axes unequally")
    return rows, axes, sum(lengths) / 3


def _posed_boxes(rest: Sequence[Box], frame: dict[str, Any],
                 tolerance: float) -> tuple[list[Box], bool]:
    if not isinstance(frame, dict):
        raise ValueError("each frame must be an object")
    has_bones, has_cubes = "bone_matrices" in frame, "cube_matrices" in frame
    if has_bones == has_cubes:
        raise ValueError("frame must supply exactly one of bone_matrices or cube_matrices")
    mappings = frame["bone_matrices" if has_bones else "cube_matrices"]
    if not isinstance(mappings, dict):
        raise ValueError("frame matrices must be an object")
    cached = {}
    boxes = []
    for box in rest:
        key = box.bone if has_bones else box.id
        if key not in mappings:
            raise ValueError(f"frame is missing matrix for {key}")
        if key not in cached:
            cached[key] = _matrix(mappings[key], f"matrix {key}")
        rows, axes, scale = cached[key]
        if has_bones:
            center = tuple(sum(rows[r][c] * box.center[c] for c in range(3))
                           + rows[r][3] for r in range(3))
            half_size = box.half_size * scale
        else:
            center = tuple(rows[r][3] for r in range(3))
            half_size = scale / 2
        boxes.append(Box(box.id, box.bone, center, axes, half_size))
    return boxes, has_bones


def penetration_depth(a: Box, b: Box, tolerance: float = 1e-5) -> float | None:
    """Return minimum SAT overlap (metres), or None for separated/contact boxes.

    Checks the six face axes and nine edge cross-product axes. All projections
    are normalized, so a reported depth is not distorted by a short cross axis.
    """
    delta = tuple(b.center[i] - a.center[i] for i in range(3))
    smallest = math.inf
    axes: Iterable[Vector] = itertools.chain(
        a.axes, b.axes, (_cross(x, y) for x in a.axes for y in b.axes))
    for axis in axes:
        length_squared = _dot(axis, axis)
        if length_squared <= 1e-24:
            continue  # Parallel edges do not define a separating axis.
        inv_length = 1.0 / math.sqrt(length_squared)
        normal = tuple(x * inv_length for x in axis)
        radius_a = a.half_size * sum(abs(_dot(normal, x)) for x in a.axes)
        radius_b = b.half_size * sum(abs(_dot(normal, x)) for x in b.axes)
        overlap = radius_a + radius_b - abs(_dot(delta, normal))
        if overlap <= tolerance:
            return None
        smallest = min(smallest, overlap)
    return smallest


def _candidate_pairs(boxes: Sequence[Box], tolerance: float,
                     skip_same_bone: bool):
    """Spatial hash broadphase; yields each positive-AABB-overlap pair once."""
    cell_size = statistics.median(box.half_size * 2 for box in boxes)
    buckets: dict[tuple[int, int, int], list[int]] = defaultdict(list)
    for index, box in enumerate(boxes):
        spans = [range(math.floor(box.low[i] / cell_size),
                       math.floor(box.high[i] / cell_size) + 1) for i in range(3)]
        bucket_count = math.prod(len(span) for span in spans)
        if bucket_count > 100_000:
            raise ValueError("cube size spread exceeds spatial-hash safety limit")
        cells = list(itertools.product(*spans))
        seen = set()
        for cell in cells:
            for previous in buckets[cell]:
                if previous in seen:
                    continue
                seen.add(previous)
                other = boxes[previous]
                if skip_same_bone and box.bone == other.bone:
                    continue
                if all(min(box.high[i], other.high[i])
                       - max(box.low[i], other.low[i]) > tolerance for i in range(3)):
                    yield other, box
        for cell in cells:
            buckets[cell].append(index)


def validate_asset(cubes: Sequence[dict[str, Any]],
                   frames: Sequence[dict[str, Any]] = (), *,
                   tolerance: float = 1e-5, max_issues: int = 100) -> dict[str, Any]:
    """Validate descriptors/rest occupancy and all supplied sampled matrices.

    Reports all issue counts but keeps at most max_issues detailed findings.
    Malformed descriptors or transforms produce pass=False with invalid_input.
    """
    report: dict[str, Any] = {
        "schema_version": 1, "pass": True, "tolerance_m": tolerance,
        "cube_count": 0, "frames_requested": 0, "frames_checked": 0, "rest_overlap_count": 0,
        "animated_overlap_count": 0, "aabb_candidates": 0, "sat_tests": 0,
        "issue_count": 0, "issues": [], "coverage": "supplied_samples_only",
    }

    issue_limit = max_issues if isinstance(max_issues, int) and max_issues > 0 else 100

    def issue(detail: dict[str, Any]):
        report["pass"] = False
        report["issue_count"] += 1
        if len(report["issues"]) < issue_limit:
            report["issues"].append(detail)

    def check(boxes: Sequence[Box], frame_label: Any, rest_check: bool,
              skip_same_bone: bool):
        for a, b in _candidate_pairs(boxes, tolerance, skip_same_bone):
            report["aabb_candidates"] += 1
            report["sat_tests"] += 1
            depth = penetration_depth(a, b, tolerance)
            if depth is not None:
                report["rest_overlap_count" if rest_check else "animated_overlap_count"] += 1
                issue({"code": "rest_overlap" if rest_check else "frame_overlap",
                       "frame": frame_label, "pair": [a.id, b.id],
                       "bones": [a.bone, b.bone], "depth_m": round(depth, 10)})

    try:
        if (isinstance(tolerance, bool) or not isinstance(tolerance, (int, float))
                or not math.isfinite(tolerance) or tolerance < 0):
            raise ValueError("tolerance must be a finite nonnegative number")
        if isinstance(max_issues, bool) or not isinstance(max_issues, int) or max_issues < 1:
            raise ValueError("max_issues must be a positive integer")
        if not isinstance(frames, (list, tuple)):
            raise ValueError("frames must be an array")
        report["frames_requested"] = len(frames)
        rest = _rest_boxes(cubes)
        report["cube_count"] = len(rest)
        check(rest, "rest", True, False)
        for index, frame in enumerate(frames):
            frame_label = frame.get("frame", index) if isinstance(frame, dict) else index
            try:
                posed, skip_same_bone = _posed_boxes(rest, frame, tolerance)
                check(posed, frame_label, False, skip_same_bone)
                report["frames_checked"] += 1
            except ValueError as exc:
                issue({"code": "invalid_input", "frame": frame_label, "message": str(exc)})
    except ValueError as exc:
        issue({"code": "invalid_input", "message": str(exc)})
    report["issues_truncated"] = report["issue_count"] > len(report["issues"])
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, required=True,
                        help="JSON with cubes and optional frames arrays")
    parser.add_argument("--output", type=Path, help="optional JSON report path")
    parser.add_argument("--tolerance", type=float, default=1e-5)
    parser.add_argument("--max-issues", type=int, default=100)
    args = parser.parse_args()
    try:
        payload = json.loads(args.input.read_text(encoding="utf-8"))
        if not isinstance(payload, dict):
            raise ValueError("input must be a JSON object")
        report = validate_asset(payload.get("cubes"), payload.get("frames", []),
                                tolerance=args.tolerance, max_issues=args.max_issues)
        output = json.dumps(report, ensure_ascii=False, indent=2) + "\n"
        if args.output:
            args.output.parent.mkdir(parents=True, exist_ok=True)
            args.output.write_text(output, encoding="utf-8")
        print(output, end="")
        return 0 if report["pass"] else 1
    except (OSError, ValueError, TypeError) as exc:
        print(json.dumps({"pass": False, "issues": [{"code": "input_error", "message": str(exc)}]}))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())

"""Verify Cairn's emitted GLB geometry/binding and non-decimated death motion.

Reads GLB/contract/death inputs. Import interface returns a JSON-ready report;
CLI optionally saves that report. Exact fractional CCD keys are required.
Optional swept verification uses the existing NumPy source-path validator on
the *emitted* positions, at the runtime cube tolerance of 1e-5 metres.
"""

from __future__ import annotations

import argparse
import bisect
from collections import defaultdict
import hashlib
import json
import math
from pathlib import Path
import struct


IDENTITY = [[float(row == column) for column in range(4)] for row in range(4)]
COMPONENTS = {5120: ("b", 1), 5121: ("B", 1), 5122: ("h", 2),
              5123: ("H", 2), 5125: ("I", 4), 5126: ("f", 4)}
COUNTS = {"SCALAR": 1, "VEC2": 2, "VEC3": 3, "VEC4": 4, "MAT4": 16}


def _multiply(a, b):
    return [[sum(a[i][k] * b[k][j] for k in range(4)) for j in range(4)] for i in range(4)]


def _point(matrix, point):
    return tuple(sum(matrix[i][j] * point[j] for j in range(3)) + matrix[i][3]
                 for i in range(3))


def _blender(point):
    return (point[0], -point[2], point[1])


def _gltf(point):
    return (point[0], point[2], -point[1])


def _column_matrix(values):
    return [[values[column * 4 + row] for column in range(4)] for row in range(4)]


def _node_matrix(node):
    if "matrix" in node:
        return _column_matrix(node["matrix"])
    x, y, z, w = node.get("rotation", [0, 0, 0, 1])
    scale = node.get("scale", [1, 1, 1])
    translation = node.get("translation", [0, 0, 0])
    rotation = [[1 - 2 * (y*y + z*z), 2 * (x*y - z*w), 2 * (x*z + y*w)],
                [2 * (x*y + z*w), 1 - 2 * (x*x + z*z), 2 * (y*z - x*w)],
                [2 * (x*z - y*w), 2 * (y*z + x*w), 1 - 2 * (x*x + y*y)]]
    return [[rotation[r][c] * scale[c] for c in range(3)] + [translation[r]]
            for r in range(3)] + [[0, 0, 0, 1]]


class Glb:
    def __init__(self, path):
        raw = Path(path).read_bytes()
        if len(raw) < 20 or raw[:4] != b"glTF":
            raise ValueError("not a GLB file")
        _, version, length = struct.unpack_from("<III", raw)
        if version != 2 or length != len(raw):
            raise ValueError("invalid GLB version/length")
        cursor, document, binary = 12, None, None
        while cursor < len(raw):
            size, kind = struct.unpack_from("<II", raw, cursor)
            cursor += 8
            content = raw[cursor:cursor + size]
            if len(content) != size:
                raise ValueError("truncated GLB chunk")
            if kind == 0x4E4F534A:
                document = json.loads(content)
            elif kind == 0x004E4942:
                binary = content
            cursor += size
        if document is None or binary is None:
            raise ValueError("GLB must contain JSON and binary chunks")
        if len(document.get("buffers", [])) != 1 or "uri" in document["buffers"][0]:
            raise ValueError("only self-contained single-buffer GLB is supported")
        self.document, self.binary = document, binary
        self.sha256 = hashlib.sha256(raw).hexdigest()
        self._accessors = {}
        self.parents = {}
        for index, node in enumerate(document.get("nodes", [])):
            for child in node.get("children", []):
                if child in self.parents:
                    raise ValueError("node has multiple parents")
                self.parents[child] = index
        self._globals = {}

    def accessor(self, index):
        if index in self._accessors:
            return self._accessors[index]
        accessor = self.document["accessors"][index]
        if "sparse" in accessor or "bufferView" not in accessor:
            raise ValueError("sparse/implicit accessors are unsupported by this verifier")
        view = self.document["bufferViews"][accessor["bufferView"]]
        if view.get("buffer", 0) != 0:
            raise ValueError("external accessor buffer")
        component = accessor["componentType"]
        fmt, width = COMPONENTS[component]
        count = COUNTS[accessor["type"]]
        stride = view.get("byteStride", width * count)
        offset = view.get("byteOffset", 0) + accessor.get("byteOffset", 0)
        if stride < width * count:
            raise ValueError("accessor stride is too short")
        values = []
        unpacker = struct.Struct("<" + fmt * count)
        for item in range(accessor["count"]):
            row = unpacker.unpack_from(self.binary, offset + item * stride)
            if accessor.get("normalized", False) and component != 5126:
                divisor = {5120: 127, 5121: 255, 5122: 32767, 5123: 65535, 5125: 4294967295}[component]
                row = tuple(max(-1.0, value / divisor) for value in row)
            values.append(row[0] if count == 1 else row)
        self._accessors[index] = values
        return values

    def global_matrix(self, index):
        if index not in self._globals:
            local = _node_matrix(self.document["nodes"][index])
            self._globals[index] = (_multiply(self.global_matrix(self.parents[index]), local)
                                    if index in self.parents else local)
        return self._globals[index]


def _float32(value):
    return struct.unpack("<f", struct.pack("<f", value))[0]


def verify_glb(glb_path, contract, death_motion, *, tolerance=1e-5, swept=True):
    glb = Glb(glb_path)
    document = glb.document
    report = {"pass": True, "glb_sha256": glb.sha256, "geometry": {}, "death": {},
              "issue_count": 0, "issues": [], "tolerance_m": tolerance}

    def issue(code, **details):
        report["pass"] = False
        report["issue_count"] += 1
        if len(report["issues"]) < 40:
            report["issues"].append({"code": code, **details})

    # Expected *closed* voxel faces include boundaries between fracture bones.
    cubes = contract["cubes"]
    step = cubes[0]["size"]
    occupied, expected_faces = {}, set()
    fragment_by_id = {fragment["id"]: fragment for fragment in contract["fragments"]}
    for cube in cubes:
        if abs(cube["size"] - step) > 1e-10:
            raise ValueError("geometry verification requires one canonical voxel size")
        key = tuple(round(value / step - .5) for value in cube["center"])
        if key in occupied:
            raise ValueError("duplicate rest occupancy in source contract")
        occupied[key] = cube["bone"]
    for key, bone in occupied.items():
        for axis in range(3):
            for sign in (-1, 1):
                neighbor = list(key)
                neighbor[axis] += sign
                if occupied.get(tuple(neighbor)) != bone:
                    expected_faces.add((bone, axis, sign, key))

    actual_faces = defaultdict(lambda: [0, 0.0])
    triangle_count, vertex_count = 0, 0
    bound_fragments = set()
    for node_index, node in enumerate(document.get("nodes", [])):
        if "mesh" not in node:
            continue
        if "skin" not in node:
            issue("unskinned_mesh", node=node.get("name", node_index))
            continue
        skin = document["skins"][node["skin"]]
        joints = skin["joints"]
        mesh_global = glb.global_matrix(node_index)
        if "inverseBindMatrices" not in skin:
            issue("missing_inverse_bind_matrices")
        else:
            binds = glb.accessor(skin["inverseBindMatrices"])
            if len(binds) != len(joints):
                issue("inverse_bind_count_mismatch")
            for joint, binding in zip(joints, binds):
                product = _multiply(glb.global_matrix(joint), _column_matrix(binding))
                error = max(abs(product[r][c] - mesh_global[r][c]) for r in range(4) for c in range(4))
                if error > tolerance:
                    issue("rest_skin_binding_mismatch", bone=document["nodes"][joint].get("name"), error=error)
        for primitive in document["meshes"][node["mesh"]]["primitives"]:
            attributes = primitive["attributes"]
            if primitive.get("mode", 4) != 4:
                issue("primitive_is_not_triangles")
                continue
            if not {"POSITION", "JOINTS_0", "WEIGHTS_0"}.issubset(attributes):
                issue("missing_skinned_vertex_attributes")
                continue
            positions = glb.accessor(attributes["POSITION"])
            joint_values = glb.accessor(attributes["JOINTS_0"])
            weights = glb.accessor(attributes["WEIGHTS_0"])
            vertex_count += len(positions)
            names, world_positions = [], []
            for index, position in enumerate(positions):
                influences = [(int(joint), weight) for joint, weight in zip(joint_values[index], weights[index]) if weight > 1e-6]
                if len(influences) != 1 or abs(sum(weights[index]) - 1) > 1e-6:
                    issue("vertex_is_not_rigidly_bound", vertex=index)
                    names.append(None)
                else:
                    name = document["nodes"][joints[influences[0][0]]].get("name")
                    names.append(name)
                    bound_fragments.add(name)
                    if name not in fragment_by_id:
                        issue("vertex_bound_to_unknown_fragment", bone=name)
                point = _blender(_point(mesh_global, position))
                world_positions.append(point)
                if any(abs(value / step - round(value / step)) * step > tolerance for value in point):
                    issue("vertex_off_voxel_lattice", vertex=index, point=point)
            indices = glb.accessor(primitive["indices"]) if "indices" in primitive else list(range(len(positions)))
            if len(indices) % 3:
                issue("triangle_index_count_invalid")
            for start in range(0, len(indices) - 2, 3):
                ids = indices[start:start + 3]
                triangle_count += 1
                bone = names[ids[0]]
                if bone is None or any(names[index] != bone for index in ids):
                    issue("triangle_crosses_rigid_bones")
                    continue
                points = [world_positions[index] for index in ids]
                a = [points[1][i] - points[0][i] for i in range(3)]
                b = [points[2][i] - points[0][i] for i in range(3)]
                normal = (a[1]*b[2] - a[2]*b[1], a[2]*b[0] - a[0]*b[2], a[0]*b[1] - a[1]*b[0])
                axis = max(range(3), key=lambda i: abs(normal[i]))
                length = math.sqrt(sum(value * value for value in normal))
                if length <= 1e-12:
                    issue("degenerate_triangle")
                    continue
                if any(abs(normal[i]) > tolerance * length for i in range(3) if i != axis):
                    issue("triangle_not_on_cube_face")
                    continue
                sign = 1 if normal[axis] > 0 else -1
                centroid = [sum(point[i] for point in points) / 3 for i in range(3)]
                plane = round(centroid[axis] / step)
                key = [math.floor(value / step) for value in centroid]
                key[axis] = plane - (1 if sign > 0 else 0)
                face = (bone, axis, sign, tuple(key))
                if any(abs(point[axis] - plane * step) > tolerance for point in points) or face not in expected_faces:
                    issue("unexpected_or_inward_voxel_face", bone=bone, cell=key, axis=axis, sign=sign)
                    continue
                actual_faces[face][0] += 1
                actual_faces[face][1] += length / 2
    for face in expected_faces:
        count, area = actual_faces[face]
        if count != 2 or abs(area - step * step) > tolerance * step:
            issue("missing_or_duplicate_closed_voxel_face", bone=face[0], cell=face[3], axis=face[1], sign=face[2], triangles=count, area_m2=area)
    missing_fragments = set(fragment_by_id) - bound_fragments
    if missing_fragments:
        issue("fragments_missing_from_mesh", count=len(missing_fragments), examples=sorted(missing_fragments)[:8])
    report["geometry"] = {"vertices_checked": vertex_count, "triangles_checked": triangle_count,
                           "expected_closed_voxel_faces": len(expected_faces),
                           "actual_closed_voxel_faces": len(actual_faces),
                           "rigid_fragment_bones_bound": len(bound_fragments)}

    animations = {animation.get("name"): animation for animation in document.get("animations", [])}
    for clip in contract["clips"]:
        if clip not in animations:
            issue("missing_animation", clip=clip)
    if "death" not in animations:
        report["death"] = {"checked": False}
        return report
    animation = animations["death"]
    death_channels = {}
    for channel in animation["channels"]:
        node = document["nodes"][channel["target"]["node"]]
        name = node.get("name")
        sampler = animation["samplers"][channel["sampler"]]
        times, values = glb.accessor(sampler["input"]), glb.accessor(sampler["output"])
        if name in fragment_by_id and channel["target"]["path"] == "translation":
            if name in death_channels:
                issue("duplicate_death_translation_channel", bone=name)
            death_channels[name] = (channel["target"]["node"], sampler, times, values)
        else:
            # Fragment rotation/scale and every parent transform must remain at
            # rest: swept death verification assumes translating rigid cubes.
            path = channel["target"]["path"]
            default = node.get(path, {"translation": [0, 0, 0], "rotation": [0, 0, 0, 1], "scale": [1, 1, 1]}.get(path))
            if default is not None and any(max(abs(a-b) for a,b in zip(row, default)) > tolerance for row in values):
                issue("death_fragment_orientation_is_not_rest" if name in fragment_by_id
                      else "death_parent_transform_is_not_rest", bone=name, path=path)
    # Blender stores key frame coordinates as float32 before glTF seconds.
    expected_times = [_float32(_float32(7.5 + frame["time"] * 30) / 30) for frame in death_motion["frames"]]
    if any(b <= a for a, b in zip(expected_times, expected_times[1:])):
        issue("source_ccd_times_collapse_in_float32")
    emitted_centers = [[None] * len(death_motion["ids"]) for _ in expected_times]
    actual_timeline, maximum_error, missing_keys = None, 0.0, 0
    actual_key_counts = []
    for fragment_index, name in enumerate(death_motion["ids"]):
        if name not in death_channels:
            issue("missing_death_translation", bone=name)
            continue
        node_index, sampler, times, values = death_channels[name]
        actual_key_counts.append(len(times))
        if len(times) != len(expected_times) + 1:
            issue("death_sampler_key_count_changed", bone=name,
                  expected=len(expected_times) + 1, actual=len(times))
        if sampler.get("interpolation", "LINEAR") != "LINEAR":
            issue("death_translation_is_not_linear", bone=name)
        if (len(times) != len(values)
                or not all(math.isfinite(time) for time in times)
                or not all(math.isfinite(value) for row in values for value in row)
                or any(b <= a for a, b in zip(times, times[1:]))):
            issue("invalid_death_sampler_timeline", bone=name)
            continue
        parent_matrix = glb.global_matrix(glb.parents[node_index]) if node_index in glb.parents else IDENTITY
        timeline = []
        for frame_index, expected in enumerate(expected_times):
            index = bisect.bisect_left(times, expected)
            candidates = [candidate for candidate in (index-1, index) if 0 <= candidate < len(times)]
            nearest = min(candidates, key=lambda candidate: abs(times[candidate]-expected)) if candidates else None
            # Float32 round-trip, not a tolerance large enough to hide decimation.
            if nearest is None or abs(times[nearest] - expected) > 2e-7:
                missing_keys += 1
                issue("missing_fractional_death_ccd_key", bone=name, time_s=expected)
                continue
            timeline.append(times[nearest])
            center = _blender(_point(parent_matrix, values[nearest]))
            emitted_centers[frame_index][fragment_index] = center
            reference = death_motion["frames"][frame_index]["centers"][fragment_index]
            error = max(abs(a-b) for a,b in zip(center, reference))
            maximum_error = max(maximum_error, error)
            if error > tolerance / 4:
                issue("death_trajectory_changed", bone=name, time_s=times[nearest], maximum_axis_error_m=error)
        if actual_timeline is None and len(timeline) == len(expected_times):
            actual_timeline = timeline
        elif len(timeline) == len(expected_times) and timeline != actual_timeline:
            issue("death_fragment_timelines_differ", bone=name)
        if times and abs(times[0]) > 2e-7:
            issue("missing_death_initial_hold", bone=name, first_time_s=times[0])
        elif times:
            initial_center = _blender(_point(parent_matrix, values[0]))
            reference_center = death_motion["frames"][0]["centers"][fragment_index]
            initial_error = max(abs(a-b) for a, b in zip(initial_center, reference_center))
            if initial_error > tolerance / 4:
                issue("death_initial_hold_is_not_rest", bone=name,
                      maximum_axis_error_m=initial_error)
    report["death"] = {"fractional_source_key_count": len(set(expected_times)),
                       "fragment_translation_channels": len(death_channels),
                       "emitted_translation_key_count_min": min(actual_key_counts, default=0),
                       "emitted_translation_key_count_max": max(actual_key_counts, default=0),
                       "missing_ccd_keys": missing_keys,
                       "maximum_world_center_error_m": maximum_error,
                       "emitted_duration_s": max((times[-1] for _, _, times, _ in death_channels.values() if times), default=0)}
    complete = actual_timeline is not None and all(all(center is not None for center in frame) for frame in emitted_centers)
    if swept and complete and missing_keys == 0:
        try:
            try:
                from .author_death_motion import validate_linear_segments
            except ImportError:
                from author_death_motion import validate_linear_segments
            emitted = {"ids": death_motion["ids"], "sizes": death_motion["sizes"],
                       "frames": [{"time": time, "centers": centers}
                                  for time, centers in zip(actual_timeline, emitted_centers)]}
            report["death"]["emitted_swept_validation"] = validate_linear_segments(emitted, tolerance=tolerance)
        except ValueError as error:
            issue("emitted_death_swept_intersection", message=str(error))
    else:
        report["death"]["emitted_swept_validation"] = {"checked": False, "reason": "incomplete emitted CCD timeline" if swept else "disabled by caller"}
    report["issues_truncated"] = report["issue_count"] > len(report["issues"])
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--asset", type=Path, default=Path("assets/characters/bosses/cairn"))
    parser.add_argument("--output", type=Path)
    parser.add_argument("--no-swept", action="store_true", help="diagnostic only; do not use for final build")
    args = parser.parse_args()
    try:
        contract = json.loads((args.asset / "source/rig_contract.json").read_text())
        death_motion = json.loads((args.asset / "source/death_motion.json").read_text())
        report = verify_glb(args.asset / "output/model.glb", contract, death_motion, swept=not args.no_swept)
        result = json.dumps(report, indent=2) + "\n"
        if args.output:
            args.output.parent.mkdir(parents=True, exist_ok=True)
            args.output.write_text(result, encoding="utf-8")
        print(result, end="")
        return 0 if report["pass"] else 1
    except (OSError, ValueError, KeyError, IndexError, struct.error) as error:
        print(json.dumps({"pass": False, "input_error": str(error)}))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())

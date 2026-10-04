"""Actual binary GLB fixtures for rigid cube and CCD export verification."""

import json
from pathlib import Path
import struct
import tempfile
import unittest

from tools.cairn.verify_glb_motion import verify_glb, _float32


def fixture(path, *, omit_event=False, shifted=False, rotate=False,
            wrong_hold=False, missing_face=False, wrong_binding=False,
            floor_penetration=False):
    blob = bytearray()
    views, accessors = [], []

    def accessor(rows, kind, component=5126):
        count = {"SCALAR": 1, "VEC3": 3, "VEC4": 4, "MAT4": 16}[kind]
        fmt = {5126: "f", 5123: "H"}[component]
        while len(blob) % 4:
            blob.append(0)
        offset = len(blob)
        for row in rows:
            values = (row,) if count == 1 else row
            blob.extend(struct.pack("<" + fmt * count, *values))
        views.append({"buffer": 0, "byteOffset": offset, "byteLength": len(blob)-offset})
        accessors.append({"bufferView": len(views)-1, "componentType": component,
                          "count": len(rows), "type": kind})
        return len(accessors)-1

    faces = [
        [(0,0,0),(0,0,1),(0,1,1),(0,1,0)],
        [(1,0,0),(1,1,0),(1,1,1),(1,0,1)],
        [(0,0,0),(1,0,0),(1,0,1),(0,0,1)],
        [(0,1,0),(0,1,1),(1,1,1),(1,1,0)],
        [(0,0,0),(0,1,0),(1,1,0),(1,0,0)],
        [(0,0,1),(1,0,1),(1,1,1),(0,1,1)],
    ]
    convert = lambda p: (p[0], p[2], -p[1])
    positions = [convert(p) for face in faces for p in face]
    indices = [index for f in range(5 if missing_face else 6)
               for index in (4*f,4*f+1,4*f+2,4*f,4*f+2,4*f+3)]
    attributes = {"POSITION": accessor(positions, "VEC3"),
                  "JOINTS_0": accessor([(0,0,0,0)]*24, "VEC4", 5123),
                  "WEIGHTS_0": accessor([(1,0,0,0)]*24, "VEC4")}
    index_accessor = accessor(indices, "SCALAR", 5123)
    binding = [1,0,0,0,0,1,0,0,0,0,1,0,-.5,-.5,.5,1]
    if wrong_binding:
        binding[12] += .01
    bind_accessor = accessor([binding], "MAT4")
    source_times = [0, .012345, .3]
    centers = [[.5,.5,.5],[.55,.5,.5],[.8,.5,.5]]
    if floor_penetration:
        centers[-1][2] = .4
    motion = {"ids": ["rubble_0000"], "sizes": [1],
              "frames": [{"time": time, "centers": [center]}
                         for time, center in zip(source_times, centers)]}
    selected = [0,2] if omit_event else [0,1,2]
    times = [0] + [_float32(_float32(7.5+source_times[i]*30)/30) for i in selected]
    values = [convert(centers[0])] + [convert(centers[i]) for i in selected]
    if shifted:
        values[2] = tuple(v + (.001 if axis == 0 else 0)
                          for axis,v in enumerate(values[2]))
    if wrong_hold:
        values[0] = (.51,.5,-.5)
    sampler = {"input": accessor(times,"SCALAR"),
               "output": accessor(values,"VEC3"),"interpolation":"LINEAR"}
    animation = {"name":"death","samplers":[sampler],
                 "channels":[{"sampler":0,"target":{"node":1,"path":"translation"}}]}
    if rotate:
        animation["samplers"].append({"input":accessor([0,.55],"SCALAR"),
            "output":accessor([(0,0,0,1),(0,0,.1,.9949874)],"VEC4"),
            "interpolation":"LINEAR"})
        animation["channels"].append({"sampler":1,"target":{"node":1,"path":"rotation"}})
    document = {"asset":{"version":"2.0"},
        "nodes":[{"name":"body","mesh":0,"skin":0},
                 {"name":"rubble_0000","translation":[.5,.5,-.5]}],
        "meshes":[{"primitives":[{"attributes":attributes,"indices":index_accessor}]}],
        "skins":[{"joints":[1],"inverseBindMatrices":bind_accessor}],
        "animations":[animation],"buffers":[{"byteLength":len(blob)}],
        "bufferViews":views,"accessors":accessors}
    raw_json = json.dumps(document,separators=(",",":")).encode()
    raw_json += b" " * (-len(raw_json) % 4)
    blob += b"\x00" * (-len(blob) % 4)
    raw = struct.pack("<III",0x46546C67,2,12+8+len(raw_json)+8+len(blob))
    raw += struct.pack("<II",len(raw_json),0x4E4F534A)+raw_json
    raw += struct.pack("<II",len(blob),0x004E4942)+blob
    path.write_bytes(raw)
    contract = {"cubes":[{"id":"cell","center":[.5,.5,.5],"size":1,"bone":"rubble_0000"}],
                "fragments":[{"id":"rubble_0000"}],"clips":{"death":{}}}
    return contract, motion


class CairnGlbMotionTests(unittest.TestCase):
    def verify_fixture(self, **options):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory)/"cube.glb"
            contract,motion = fixture(path,**options)
            return verify_glb(path,contract,motion)

    def assert_issue(self, code, **options):
        report = self.verify_fixture(**options)
        self.assertFalse(report["pass"])
        self.assertIn(code,{issue["code"] for issue in report["issues"]})

    def test_exact_fractional_keys_rigid_geometry_and_swept_motion(self):
        report = self.verify_fixture()
        self.assertTrue(report["pass"],report["issues"])
        self.assertEqual(report["geometry"]["actual_closed_voxel_faces"],6)
        self.assertEqual(report["death"]["missing_ccd_keys"],0)
        self.assertEqual(report["death"]["emitted_swept_validation"]["checked_linear_segments"],2)

    def test_decimated_ccd_event_is_rejected(self):
        self.assert_issue("missing_fractional_death_ccd_key",omit_event=True)

    def test_changed_exported_trajectory_is_rejected(self):
        self.assert_issue("death_trajectory_changed",shifted=True)

    def test_rotation_cannot_bypass_translating_cube_swept_check(self):
        self.assert_issue("death_fragment_orientation_is_not_rest",rotate=True)

    def test_initial_hold_must_match_source_rest_center(self):
        self.assert_issue("death_initial_hold_is_not_rest",wrong_hold=True)

    def test_missing_voxel_surface_is_rejected(self):
        self.assert_issue("missing_or_duplicate_closed_voxel_face",missing_face=True)

    def test_actual_skin_bind_matrix_is_checked(self):
        self.assert_issue("rest_skin_binding_mismatch",wrong_binding=True)

    def test_swept_checker_reads_actual_emitted_positions(self):
        self.assert_issue("emitted_death_swept_intersection",floor_penetration=True)


if __name__ == "__main__":
    unittest.main()

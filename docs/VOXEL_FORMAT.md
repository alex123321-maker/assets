# Voxel Source Format v1

Файл: `source/voxels.json`

## Schema overview

```json
{
  "version": 1,
  "name": "rock_demo",
  "voxel_size": 0.15,
  "origin": "bottom_center",
  "materials": {
    "S": {
      "name": "stone",
      "base_color": [0.45, 0.47, 0.50, 1.0],
      "roughness": 0.9,
      "metallic": 0.0
    }
  },
  "layers": [
    {
      "y": 0,
      "rows": [
        ".......",
        "..SSS..",
        ".SSSSS.",
        ".SSSSS.",
        "..SSS..",
        "......."
      ]
    }
  ]
}
```

## Rules

- `version` currently must be `1`.
- `voxel_size` is world-space size in Blender units.
- `origin`: baseline supports `bottom_center`.
- `.` means empty voxel.
- Every non-dot token must exist in `materials`.
- All rows across all layers have equal length (X).
- All layers have equal row count (Z).
- Y layers must be unique and non-negative.
- Missing Y values between explicit layers are treated as empty.
- Disconnected geometry is allowed only when intentional.
- Material token is a single character in v1.

## Axis mapping

```text
X → left/right across characters in a row
Y → layer height
Z → rows from back to front
```

## Export behavior

A face is emitted only if the neighboring cell in that direction is empty/outside the grid.

Therefore:
- no internal faces between occupied voxels;
- visible block steps remain;
- output is not a set of individual cubes.

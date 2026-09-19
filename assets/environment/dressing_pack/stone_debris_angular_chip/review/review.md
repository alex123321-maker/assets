# Build Verification: stone_debris_angular_chip

## Objective Build Verification
- [x] Required review renders generated (iso.png, front.png, side.png, top.png at 512x512).
- [x] Export validated (model.glb, glTF 2.0, 6364 bytes, 3 mesh primitives).
- [x] Material count is within budget (3 materials <= 4).
- [x] Triangle count verified (66 tris <= 500 budget).
- [x] Internal faces culled (31 visible faces).
- [x] Ground contact flat at z=0, origin bottom_center.
- [x] Low-poly blocky silhouette matching visual dressing contract.

## Metrics
- Occupied voxels: 5
- Triangles: 66
- Visible faces: 31
- Mesh objects: 3
- Materials: 3
- Grid dimensions: 4x2x4 (voxel_size: 0.1m)
- World dimensions: 0.40m x 0.20m x 0.40m
- Engine: BLENDER_EEVEE (5.2.1 LTS)

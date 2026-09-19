# Build Verification: stone_debris_fine_scatter

## Objective Build Verification
- [x] Required review renders generated (iso.png, front.png, side.png, top.png at 512x512).
- [x] Export validated (model.glb, glTF 2.0, 14480 bytes, 2 mesh primitives).
- [x] Material count is within budget (2 materials <= 4).
- [x] Triangle count verified (240 tris <= 500 budget).
- [x] Internal faces culled (117 visible faces).
- [x] Ground contact flat at z=0, origin bottom_center.
- [x] Low-poly blocky silhouette matching visual dressing contract.

## Metrics
- Occupied voxels: 7
- Triangles: 240
- Visible faces: 117
- Mesh objects: 2
- Materials: 2
- Grid dimensions: 6x1x6 (voxel_size: 0.1m)
- World dimensions: 0.60m x 0.10m x 0.60m
- Engine: BLENDER_EEVEE (5.2.1 LTS)

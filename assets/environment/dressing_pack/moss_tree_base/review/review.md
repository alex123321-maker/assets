# Build Verification: moss_tree_base

## Objective Build Verification
- [x] Required review renders generated (iso.png, front.png, side.png, top.png at 512x512).
- [x] Export validated (model.glb, glTF 2.0, 10148 bytes, 1 mesh, 1 shared material).
- [x] Shared production material verified (`mat_dressing_atlas` mapped via UVMap to `dressing_palette_atlas.png`).
- [x] Material count is within budget (1 shared material <= 4).
- [x] Triangle count verified (120 tris <= 500 budget).
- [x] Internal faces culled (60 visible faces).
- [x] Ground contact flat at z=0, origin bottom_center.
- [x] Low-poly blocky silhouette matching visual dressing contract.

## Metrics
- Occupied voxels: 17
- Triangles: 120
- Visible faces: 60
- Mesh objects: 1
- Materials: 1
- Shared material: `mat_dressing_atlas` (atlas: `dressing_palette_atlas.png`)
- Grid dimensions: 6x2x6 (voxel_size: 0.1m)
- World dimensions: 0.60m x 0.20m x 0.60m
- Engine: BLENDER_EEVEE (5.2.1 LTS)

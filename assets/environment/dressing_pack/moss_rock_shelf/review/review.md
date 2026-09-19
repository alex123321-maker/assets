# Build Verification: moss_rock_shelf

## Objective Build Verification
- [x] Required review renders generated (iso.png, front.png, side.png, top.png at 512x512).
- [x] Export validated (model.glb, glTF 2.0, 18040 bytes, 1 mesh, 1 shared material).
- [x] Shared production material verified (`mat_dressing_atlas` mapped via UVMap to baseColor & metallic-roughness atlases).
- [x] Material count is within budget (1 shared material <= 4).
- [x] Triangle count verified (198 tris <= 500 budget).
- [x] Internal faces culled (131 visible faces).
- [x] Ground contact flat at z=0, origin bottom_center.
- [x] Low-poly blocky silhouette matching visual dressing contract.

## Metrics
- Occupied voxels: 27
- Triangles: 198
- Visible faces: 131
- Mesh objects: 1
- Materials: 1
- Shared material: `mat_dressing_atlas` (albedo atlas: `dressing_palette_atlas.png`, roughness atlas: `dressing_roughness_atlas.png`)
- Grid dimensions: 6x3x5 (voxel_size: 0.1m)
- Nominal grid size: 0.60m x 0.30m x 0.50m
- Exported mesh AABB: 0.492m x 0.315m x 0.392m
- Exported bounds: min=[-0.296, 0.000, -0.146], max=[0.196, 0.315, 0.246]
- Engine: BLENDER_EEVEE (5.2.1 LTS)

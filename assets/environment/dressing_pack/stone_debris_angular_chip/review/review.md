# Build Verification: stone_debris_angular_chip

## Objective Build Verification
- [x] Required review renders generated (iso.png, front.png, side.png, top.png at 512x512).
- [x] Export validated (model.glb, glTF 2.0, 12408 bytes, 1 mesh, 1 shared material).
- [x] Shared production material verified (`mat_dressing_atlas` mapped via UVMap to baseColor & metallic-roughness atlases).
- [x] Material count is within budget (1 shared material <= 4).
- [x] Triangle count verified (152 tris <= 500 budget).
- [x] Internal faces culled (71 visible faces).
- [x] Ground contact flat at z=0, origin bottom_center.
- [x] Low-poly blocky silhouette matching visual dressing contract.

## Metrics
- Occupied voxels: 13
- Triangles: 152
- Visible faces: 71
- Mesh objects: 1
- Materials: 1
- Shared material: `mat_dressing_atlas` (albedo atlas: `dressing_palette_atlas.png`, roughness atlas: `dressing_roughness_atlas.png`)
- Grid dimensions: 5x4x5 (voxel_size: 0.1m)
- Nominal grid size: 0.50m x 0.40m x 0.50m
- Exported mesh AABB: 0.400m x 0.400m x 0.400m
- Exported bounds: min=[-0.150, 0.000, -0.150], max=[0.250, 0.400, 0.250]
- Engine: BLENDER_EEVEE (5.2.1 LTS)

# Build Verification: flower_red_cluster

## Objective Build Verification
- [x] Required review renders generated (iso.png, front.png, side.png, top.png at 512x512).
- [x] Export validated (model.glb, glTF 2.0, 30188 bytes, 1 mesh, 1 shared material).
- [x] Shared production material verified (`mat_dressing_atlas` mapped via UVMap to baseColor & metallic-roughness atlases).
- [x] Material count is within budget (1 shared material <= 4).
- [x] Triangle count verified (408 tris <= 500 budget).
- [x] Internal faces culled (204 visible faces).
- [x] Ground contact flat at z=0, origin bottom_center.
- [x] Low-poly blocky silhouette matching visual dressing contract.

## Metrics
- Occupied voxels: 34
- Triangles: 408
- Visible faces: 204
- Mesh objects: 1
- Materials: 1
- Shared material: `mat_dressing_atlas` (albedo atlas: `dressing_palette_atlas.png`, roughness atlas: `dressing_roughness_atlas.png`)
- Grid dimensions: 5x5x5 (voxel_size: 0.1m)
- World dimensions: 0.50m x 0.50m x 0.50m
- Engine: BLENDER_EEVEE (5.2.1 LTS)

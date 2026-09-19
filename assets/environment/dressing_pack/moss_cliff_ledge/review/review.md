# Build Verification: moss_cliff_ledge

## Objective Build Verification
- [x] Required review renders generated (iso.png, front.png, side.png, top.png at 512x512).
- [x] Export validated (model.glb, glTF 2.0, 20904 bytes, 1 mesh, 1 shared material).
- [x] Shared production material verified (`mat_dressing_atlas` mapped via UVMap to baseColor & metallic-roughness atlases).
- [x] Material count is within budget (1 shared material <= 4).
- [x] Triangle count verified (224 tris <= 500 budget).
- [x] Internal faces culled (160 visible faces).
- [x] Origin at edge_anchor (z=0 cliff ledge surface plane, with 3D hanging tendrils extending below to -0.26m).
- [x] Low-poly blocky silhouette matching visual dressing contract.

## Metrics
- Occupied voxels: 26
- Triangles: 224
- Visible faces: 160
- Mesh objects: 1
- Materials: 1
- Shared material: `mat_dressing_atlas` (albedo atlas: `dressing_palette_atlas.png`, roughness atlas: `dressing_roughness_atlas.png`)
- Origin / Pivot: `edge_anchor`
- Grid dimensions: 6x3x5 (voxel_size: 0.1m)
- Nominal grid size: 0.60m x 0.30m x 0.50m
- Exported mesh AABB: 0.592m x 0.575m x 0.392m
- Exported bounds: min=[-0.296, -0.260, -0.246], max=[0.296, 0.315, 0.146]
- Engine: BLENDER_EEVEE (5.2.1 LTS)

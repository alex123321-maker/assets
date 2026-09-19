# Request: Cliff Ledge Moss Cascade

## Metadata
- **Asset Name**: `moss_cliff_ledge`
- **Subfamily**: Moss / Low Vegetation
- **Issue**: #7 Environment dressing pack
- **Source Mode**: `voxel_static`
- **Voxel Size**: 0.1m (10 cm step)
- **Origin / Pivot**: `edge_anchor` at z=0 (cliff ledge surface plane with negative hanging stalactite tendrils extending down to -0.26m)

## Role & Description
Trailing stepped overhang patch designed specifically for cliff edges and terrace rims.
Spawned via edge/ledge placement rules (rather than flat ground scatter) with its anchor resting on the cliff top surface.

## Visual & Runtime Constraints
- Chunky readable blocky silhouette;
- Ledge surface contact at z=0 with 3D hanging stalactite tendrils extending below ground plane;
- No collision shapes, no scripts;
- MultiMesh / batching ready with shared `material_dressing_atlas`;
- Shared palette `moss` integration;
- Triangle budget <= 500 tris.

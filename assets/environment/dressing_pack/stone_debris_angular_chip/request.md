# Request: Stone Debris Angular Chip

## Metadata
- **Asset Name**: `stone_debris_angular_chip`
- **Subfamily**: Stone Debris
- **Issue**: #7 Environment dressing pack
- **Source Mode**: `voxel_static`
- **Voxel Size**: 0.1m (10 cm step)
- **Origin / Pivot**: `bottom_center` at z=0 (ground contact)

## Role & Description
Sharp diagonal triangular cleave with steep 3-layer pointed pinnacle.
Designed for mass scatter-placement across Cube Siege biomes (Forest, Plains, Mountain).

## Visual & Runtime Constraints
- Chunky readable blocky silhouette;
- Flat clean ground contact at z=0;
- No collision shapes, no scripts;
- MultiMesh / batching ready with shared `material_dressing_atlas`;
- Shared palette `stone_debris` integration;
- Triangle budget <= 500 tris.

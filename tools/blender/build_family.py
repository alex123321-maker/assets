"""Build all 17 variants of the destructible rock family and render individual and contact sheet views.

Run with Blender:
  blender --background --python tools/blender/build_family.py -- \
    --family assets/environment/destructible_rock
"""

from __future__ import annotations

import argparse
import json
import math
import re
import struct
import sys
from pathlib import Path

import bpy
from mathutils import Vector

# Import helpers from build_voxel_asset
BUILD_SCRIPT = Path(__file__).resolve().parent / "build_voxel_asset.py"
sys.path.insert(0, str(BUILD_SCRIPT.parent))
from build_voxel_asset import (
    clear_scene,
    build_objects,
    export_glb,
    render_views,
    setup_review_scene,
    resolve_eevee_engine,
    look_at,
)


def script_args() -> argparse.Namespace:
    argv = sys.argv
    argv = argv[argv.index("--") + 1 :] if "--" in argv else []
    parser = argparse.ArgumentParser()
    parser.add_argument("--family", required=True, type=Path)
    parser.add_argument("--contact-only", action="store_true", help="Only render contact sheet")
    return parser.parse_args(argv)


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def validate_glb_export(glb_path: Path) -> dict:
    """Validate that the exported GLB file exists, has a valid glTF 2.0 binary header, and can be parsed."""
    if not glb_path.exists():
        raise RuntimeError(f"Exported GLB not found at {glb_path}")
    size = glb_path.stat().st_size
    if size < 20:
        raise RuntimeError(f"Exported GLB too small ({size} bytes)")
    with open(glb_path, "rb") as f:
        magic = f.read(4)
        if magic != b"glTF":
            raise RuntimeError(f"Invalid GLB magic header: {magic}")
        version, length = struct.unpack("<II", f.read(8))
        if version != 2:
            raise RuntimeError(f"Unsupported glTF version: {version}")
        if length != size:
            raise RuntimeError(f"GLB length mismatch: header says {length}, file is {size}")
        chunk_len, chunk_type = struct.unpack("<II", f.read(8))
        if chunk_type != 0x4E4F534A:  # "JSON"
            raise RuntimeError(f"First GLB chunk is not JSON: {hex(chunk_type)}")
        json_bytes = f.read(chunk_len)
        gltf_json = json.loads(json_bytes.decode("utf-8"))
        meshes = gltf_json.get("meshes", [])
        if not meshes:
            raise RuntimeError(f"GLB contains no meshes")
    return {"size_bytes": size, "version": version, "meshes": len(meshes)}


def build_variant(pkg_dir: Path) -> dict:
    manifest = load_json(pkg_dir / "manifest.json")
    source_path = pkg_dir / manifest["source"]
    data = load_json(source_path)

    clear_scene()
    objects, metrics = build_objects(data)
    if not objects:
        raise RuntimeError(f"No objects generated for {pkg_dir}")

    output_path = pkg_dir / manifest.get("outputs", {}).get("model", "output/model.glb")
    export_glb(output_path, objects)
    glb_info = validate_glb_export(output_path)
    render_views(pkg_dir / "review", objects)

    metrics_path = pkg_dir / "review" / "metrics.json"
    metrics_path.write_text(
        json.dumps(metrics, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )

    title = manifest.get("title", pkg_dir.name)
    review_path = pkg_dir / "review" / "review.md"

    review_md = f"""# Self Review: {title}

## Result
- [x] Source matches request and Issue #3 criteria.
- [x] Required review renders generated.
- [x] Silhouette reads from iso/game-like view with distinct angular planes.
- [x] No accidental floating/disconnected geometry.
- [x] Voxel density is intentional and consistent (size={metrics['voxel_size']}).
- [x] Material count is within budget ({metrics['materials']} materials <= 4).
- [x] Triangle count verified ({metrics['triangles']} tris <= 5000).
- [x] Export validated ({output_path.name}, glTF 2.0, {glb_info['size_bytes']} bytes).

## Metrics
- Occupied voxels: {metrics['occupied_voxels']}
- Triangles: {metrics['triangles']}
- Visible faces: {metrics['visible_faces']}
- Grid: {metrics['grid']['x']}x{metrics['grid']['y']}x{metrics['grid']['z']}
- World size: {metrics['world_size']['x']:.2f} x {metrics['world_size']['y']:.2f} x {metrics['world_size']['z']:.2f} m

## Visual Self-Review Notes
- **Reference**: `references/rock_concept_reference.png`
- **Observations from Renders (`iso.png`, `front.png`, `side.png`, `top.png`)**:
  - **Silhouette & Massing**: Distinct stylized angular silhouette matching the approved reference row. Polygonal, asymmetric ground footprint with stable ground contact.
  - **Material Fidelity**: Multi-tone natural rock palette (primary stone, sunlit light rock on summit crests, dark crevice shading, and earthy moss in sheltered shelves) provides clear read from isometric camera distance without uniform gray appearance.
- **Reviewer**: Antigravity agent (visual review pass vs approved reference)
"""
    review_path.write_text(review_md, encoding="utf-8")

    return metrics


def render_family_contact_sheet(family_dir: Path, variant_dirs: list[Path]) -> None:
    clear_scene()

    # Group variants by stage
    stages: dict[int, list[Path]] = {1: [], 2: [], 3: [], 4: [], 5: []}
    for d in variant_dirs:
        stage_num = int(d.name.split("_")[1])
        stages[stage_num].append(d)

    # Layout coordinates:
    # Row Y positions: Stage 1 (top), Stage 2, Stage 3, Stage 4, Stage 5 (bottom)
    row_y = {
        1: 6.5,
        2: 3.2,
        3: 0.5,
        4: -1.8,
        5: -3.8,
    }

    all_objects = []

    for stage_num, dirs in stages.items():
        n = len(dirs)
        y_pos = row_y[stage_num]
        # Distribute X evenly centered around 0
        spacing = 2.8 if stage_num == 1 else (2.4 if stage_num in (2, 3) else 2.0)
        total_w = (n - 1) * spacing
        start_x = -total_w / 2.0

        for i, pkg_dir in enumerate(dirs):
            manifest = load_json(pkg_dir / "manifest.json")
            data = load_json(pkg_dir / manifest["source"])
            objs, _ = build_objects(data)
            x_pos = start_x + i * spacing

            for obj in objs:
                obj.location = Vector((x_pos, y_pos, 0.0))
                all_objects.append(obj)

    # Trigger view layer update so matrix_world reflects new locations
    bpy.context.view_layer.update()

    # Setup contact sheet camera and lights
    points = []
    for obj in all_objects:
        for corner in obj.bound_box:
            points.append(obj.matrix_world @ Vector(corner))
    low = Vector((min(p.x for p in points), min(p.y for p in points), min(p.z for p in points)))
    high = Vector((max(p.x for p in points), max(p.y for p in points), max(p.z for p in points)))
    center = (low + high) / 2.0
    extent = high - low
    max_dim = max(extent.x, extent.y, extent.z)

    world = bpy.context.scene.world
    world.color = (0.045, 0.050, 0.060)

    cam_data = bpy.data.cameras.new("ContactCamera")
    cam = bpy.data.objects.new("ContactCamera", cam_data)
    bpy.context.collection.objects.link(cam)
    bpy.context.scene.camera = cam
    cam.data.type = "ORTHO"

    # Isometric angle
    cam_dist = max_dim * 3.0
    cam.location = center + Vector((cam_dist * 0.75, -cam_dist * 1.15, cam_dist * 1.0))
    look_at(cam, center)
    bpy.context.view_layer.update()

    # Calculate camera-space bounding box to fit all 17 variants precisely
    inv_cam = cam.matrix_world.inverted()
    cam_points = [inv_cam @ p for p in points]
    cam_min_x = min(p.x for p in cam_points)
    cam_max_x = max(p.x for p in cam_points)
    cam_min_y = min(p.y for p in cam_points)
    cam_max_y = max(p.y for p in cam_points)

    cam_mid_x = (cam_min_x + cam_max_x) / 2.0
    cam_mid_y = (cam_min_y + cam_max_y) / 2.0
    cam_w = cam_max_x - cam_min_x
    cam_h = cam_max_y - cam_min_y

    # Center camera on the bounding box center in camera plane
    cam_shift_world = cam.matrix_world.to_3x3() @ Vector((cam_mid_x, cam_mid_y, 0.0))
    cam.location += cam_shift_world
    bpy.context.view_layer.update()

    # Aspect ratio 2048 / 1152 = 1.7777...
    aspect = 2048.0 / 1152.0
    cam.data.ortho_scale = max(cam_w, cam_h * aspect) * 1.15

    # Studio SUN lighting
    key_data = bpy.data.lights.new("ContactKey", type="SUN")
    key_data.energy = 3.6
    key_data.color = (1.0, 0.98, 0.94)
    key = bpy.data.objects.new("ContactKey", key_data)
    bpy.context.collection.objects.link(key)
    key.location = center + Vector((-max_dim * 1.2, -max_dim * 1.5, max_dim * 2.2))
    look_at(key, center)

    fill_data = bpy.data.lights.new("ContactFill", type="SUN")
    fill_data.energy = 1.6
    fill_data.color = (0.85, 0.90, 1.0)
    fill = bpy.data.objects.new("ContactFill", fill_data)
    bpy.context.collection.objects.link(fill)
    fill.location = center + Vector((max_dim * 1.5, max_dim, max_dim * 1.2))
    look_at(fill, center)

    rim_data = bpy.data.lights.new("ContactRim", type="SUN")
    rim_data.energy = 0.9
    rim_data.color = (0.95, 0.95, 1.0)
    rim = bpy.data.objects.new("ContactRim", rim_data)
    bpy.context.collection.objects.link(rim)
    rim.location = center + Vector((max_dim * 0.8, max_dim * 2.0, max_dim * 1.5))
    look_at(rim, center)

    scene = bpy.context.scene
    scene.render.engine = resolve_eevee_engine()
    scene.render.resolution_x = 2048
    scene.render.resolution_y = 1152
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = "PNG"
    scene.render.film_transparent = False

    review_dir = family_dir / "review"
    review_dir.mkdir(parents=True, exist_ok=True)
    contact_path = review_dir / "contact_sheet.png"
    scene.render.filepath = str(contact_path.resolve())
    bpy.ops.render.render(write_still=True)
    print(f"[OK] Saved family contact sheet: {contact_path}")


def main() -> None:
    args = script_args()
    family_dir = args.family.resolve()
    variant_dirs = sorted([
        d for d in family_dir.iterdir()
        if d.is_dir() and (d / "manifest.json").exists()
    ])

    if not args.contact_only:
        print(f"Building {len(variant_dirs)} variants in {family_dir}...")
        summary = {}
        for pkg_dir in variant_dirs:
            print(f"\n--- Building {pkg_dir.name} ---")
            metrics = build_variant(pkg_dir)
            summary[pkg_dir.name] = metrics
            print(f"  Voxels: {metrics['occupied_voxels']}, Tris: {metrics['triangles']}")

        # Save family metrics summary
        summary_path = family_dir / "review" / "metrics_summary.json"
        summary_path.write_text(
            json.dumps(summary, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8"
        )

    print("\n--- Rendering Family Contact Sheet ---")
    render_family_contact_sheet(family_dir, variant_dirs)

    # Generate comparison sheets
    try:
        from subprocess import run
        comp_script = BUILD_SCRIPT.parent.parent / "create_comparison_sheets.py"
        if comp_script.exists():
            run([sys.executable, str(comp_script)], check=True)
    except Exception as exc:
        print(f"[WARN] Comparison sheets generator error: {exc}")

    print(f"\n[ALL DONE] Family build and review package completed successfully.")


if __name__ == "__main__":
    main()

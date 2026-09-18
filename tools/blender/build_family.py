"""Build all 17 variants of the destructible rock family and render individual and contact sheet views.

Run with Blender:
  blender --background --python tools/blender/build_family.py -- \
    --family assets/environment/destructible_rock
"""

from __future__ import annotations

import argparse
import json
import math
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
    return parser.parse_args(argv)


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


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
    render_views(pkg_dir / "review", objects)

    metrics_path = pkg_dir / "review" / "metrics.json"
    metrics_path.write_text(
        json.dumps(metrics, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
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
    world.color = (0.02, 0.02, 0.03)

    cam_data = bpy.data.cameras.new("ContactCamera")
    cam = bpy.data.objects.new("ContactCamera", cam_data)
    bpy.context.collection.objects.link(cam)
    bpy.context.scene.camera = cam
    cam.data.type = "ORTHO"
    cam.data.ortho_scale = extent.x * 1.25

    # Isometric angle
    cam_dist = max_dim * 3.0
    cam.location = center + Vector((cam_dist * 0.75, -cam_dist * 1.15, cam_dist * 1.0))
    look_at(cam, center)

    # Lighting
    key_data = bpy.data.lights.new("ContactKey", type="AREA")
    key_data.energy = 2500.0
    key_data.shape = "DISK"
    key_data.size = max_dim * 2.5
    key = bpy.data.objects.new("ContactKey", key_data)
    bpy.context.collection.objects.link(key)
    key.location = center + Vector((-max_dim * 2.0, -max_dim * 2.5, max_dim * 3.0))
    look_at(key, center)

    fill_data = bpy.data.lights.new("ContactFill", type="AREA")
    fill_data.energy = 900.0
    fill_data.size = max_dim * 2.0
    fill = bpy.data.objects.new("ContactFill", fill_data)
    bpy.context.collection.objects.link(fill)
    fill.location = center + Vector((max_dim * 2.5, max_dim * 1.5, max_dim * 2.0))
    look_at(fill, center)

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

    print(f"Building {len(variant_dirs)} variants in {family_dir}...")
    summary = {}
    for pkg_dir in variant_dirs:
        print(f"\n--- Building {pkg_dir.name} ---")
        metrics = build_variant(pkg_dir)
        summary[pkg_dir.name] = metrics
        print(f"  Voxels: {metrics['occupied_voxels']}, Tris: {metrics['triangles']}")

    print("\n--- Rendering Family Contact Sheet ---")
    render_family_contact_sheet(family_dir, variant_dirs)

    # Save family metrics summary
    summary_path = family_dir / "review" / "metrics_summary.json"
    summary_path.write_text(
        json.dumps(summary, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8"
    )
    print(f"\n[ALL DONE] Family build complete. Metrics summary saved to {summary_path}")


if __name__ == "__main__":
    main()

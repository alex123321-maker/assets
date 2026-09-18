#!/usr/bin/env python3
"""Create a new asset package from the repository template."""

from __future__ import annotations

import argparse
import json
import shutil
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("category", help="e.g. environment, characters, props")
    parser.add_argument("name", help="asset folder/name")
    parser.add_argument(
        "--type",
        default="voxel_static",
        choices=["voxel_static", "voxel_rigged", "blender_unique", "vfx"],
    )
    args = parser.parse_args()

    root = Path(__file__).resolve().parents[1]
    template = root / "assets" / "_template"
    target = root / "assets" / args.category / args.name

    if target.exists():
        raise SystemExit(f"Target already exists: {target}")

    shutil.copytree(template, target)

    manifest_path = target / "manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["name"] = args.name
    manifest["type"] = args.type

    if args.type in {"blender_unique", "voxel_rigged"}:
        manifest["source"] = "source/model.blend"
    elif args.type == "vfx":
        manifest["source"] = "source"
    else:
        manifest["source"] = "source/voxels.json"

    manifest_path.write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )

    print(target)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

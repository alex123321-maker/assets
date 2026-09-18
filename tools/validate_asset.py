#!/usr/bin/env python3
"""Validate an asset package without requiring Blender."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REQUIRED_MANIFEST = {"name", "type", "version", "source"}
SUPPORTED_TYPES = {"voxel_static", "voxel_rigged", "blender_unique", "vfx"}


class ValidationError(Exception):
    pass


def load_json(path: Path) -> dict:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise ValidationError(f"Missing file: {path}") from exc
    except json.JSONDecodeError as exc:
        raise ValidationError(f"Invalid JSON in {path}: {exc}") from exc


def validate_voxels(path: Path) -> dict:
    data = load_json(path)
    if data.get("version") != 1:
        raise ValidationError(f"{path}: version must be 1")

    voxel_size = data.get("voxel_size")
    if not isinstance(voxel_size, (int, float)) or voxel_size <= 0:
        raise ValidationError(f"{path}: voxel_size must be > 0")

    if data.get("origin", "bottom_center") != "bottom_center":
        raise ValidationError(f"{path}: only origin='bottom_center' is supported in v1")

    materials = data.get("materials")
    if not isinstance(materials, dict) or not materials:
        raise ValidationError(f"{path}: materials must be a non-empty object")

    for token, material in materials.items():
        if not isinstance(token, str) or len(token) != 1 or token == ".":
            raise ValidationError(f"{path}: material token {token!r} must be one non-dot character")
        if not isinstance(material, dict) or not material.get("name"):
            raise ValidationError(f"{path}: material {token!r} requires a name")
        color = material.get("base_color", [0.5, 0.5, 0.5, 1.0])
        if not isinstance(color, list) or len(color) != 4:
            raise ValidationError(f"{path}: material {token!r} base_color must have 4 values")

    layers = data.get("layers")
    if not isinstance(layers, list) or not layers:
        raise ValidationError(f"{path}: layers must be a non-empty array")

    seen_y: set[int] = set()
    width = None
    depth = None
    occupied = 0

    for layer in layers:
        if not isinstance(layer, dict):
            raise ValidationError(f"{path}: every layer must be an object")
        y = layer.get("y")
        rows = layer.get("rows")
        if not isinstance(y, int) or y < 0:
            raise ValidationError(f"{path}: layer y must be a non-negative integer")
        if y in seen_y:
            raise ValidationError(f"{path}: duplicate layer y={y}")
        seen_y.add(y)

        if not isinstance(rows, list) or not rows:
            raise ValidationError(f"{path}: layer y={y} rows must be non-empty")

        if depth is None:
            depth = len(rows)
        elif len(rows) != depth:
            raise ValidationError(f"{path}: all layers must have the same Z row count")

        for row in rows:
            if not isinstance(row, str):
                raise ValidationError(f"{path}: rows must be strings")
            if width is None:
                width = len(row)
                if width == 0:
                    raise ValidationError(f"{path}: rows cannot be empty")
            elif len(row) != width:
                raise ValidationError(f"{path}: all rows must have equal X width")

            for token in row:
                if token == ".":
                    continue
                if token not in materials:
                    raise ValidationError(f"{path}: unknown material token {token!r}")
                occupied += 1

    if occupied == 0:
        raise ValidationError(f"{path}: asset contains no occupied voxels")

    return {
        "width": width,
        "height": max(seen_y) + 1,
        "depth": depth,
        "occupied_voxels": occupied,
        "materials": len(materials),
        "voxel_size": float(voxel_size),
    }


def validate_asset(asset_dir: Path) -> dict:
    if not asset_dir.is_dir():
        raise ValidationError(f"Asset directory not found: {asset_dir}")

    request = asset_dir / "request.md"
    if not request.is_file():
        raise ValidationError(f"Missing request.md: {request}")

    manifest_path = asset_dir / "manifest.json"
    manifest = load_json(manifest_path)
    missing = REQUIRED_MANIFEST - set(manifest)
    if missing:
        raise ValidationError(f"{manifest_path}: missing fields: {sorted(missing)}")

    if manifest["version"] != 1:
        raise ValidationError(f"{manifest_path}: version must be 1")
    if manifest["type"] not in SUPPORTED_TYPES:
        raise ValidationError(
            f"{manifest_path}: unsupported type {manifest['type']!r}; "
            f"expected one of {sorted(SUPPORTED_TYPES)}"
        )

    source_path = asset_dir / manifest["source"]
    if not source_path.exists():
        raise ValidationError(f"Manifest source does not exist: {source_path}")

    result = {
        "name": manifest["name"],
        "type": manifest["type"],
        "source": str(source_path),
    }

    if manifest["type"] == "voxel_static":
        voxel_metrics = validate_voxels(source_path)
        result["voxel_source"] = voxel_metrics

        budgets = manifest.get("budgets", {})
        max_materials = budgets.get("max_materials")
        if isinstance(max_materials, int) and voxel_metrics["materials"] > max_materials:
            raise ValidationError(
                f"Material budget exceeded: {voxel_metrics['materials']} > {max_materials}"
            )

    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("asset", type=Path, help="Path to asset package")
    args = parser.parse_args()

    try:
        result = validate_asset(args.asset.resolve())
    except ValidationError as exc:
        print(f"[FAIL] {exc}", file=sys.stderr)
        return 1

    print("[PASS] asset package is valid")
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

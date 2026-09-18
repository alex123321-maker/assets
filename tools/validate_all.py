#!/usr/bin/env python3
"""Validate every committed asset package that has a manifest.json."""

from __future__ import annotations

import sys
from pathlib import Path

from validate_asset import ValidationError, validate_asset


def main() -> int:
    root = Path(__file__).resolve().parents[1]
    manifests = sorted((root / "assets").rglob("manifest.json"))
    if not manifests:
        print("[FAIL] no asset manifests found", file=sys.stderr)
        return 1

    failed = False
    for manifest in manifests:
        asset_dir = manifest.parent
        try:
            result = validate_asset(asset_dir)
            print(f"[PASS] {asset_dir.relative_to(root)} ({result['type']})")
        except ValidationError as exc:
            failed = True
            print(f"[FAIL] {asset_dir.relative_to(root)}: {exc}", file=sys.stderr)

    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())

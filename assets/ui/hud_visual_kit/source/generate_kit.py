#!/usr/bin/env python3
"""Source runner for hud_visual_kit asset package.

Can be run directly from any working directory:
    python assets/ui/hud_visual_kit/source/generate_kit.py
"""
from __future__ import annotations

import sys
from pathlib import Path

# Dynamically locate repository root containing GEMINI.md or .git
current = Path(__file__).resolve()
repo_root = None
for parent in current.parents:
    if (parent / "GEMINI.md").exists() or (parent / ".git").exists():
        repo_root = parent
        break

if repo_root is None:
    repo_root = current.parents[4]

tools_dir = repo_root / "tools"
if str(tools_dir) not in sys.path:
    sys.path.insert(0, str(tools_dir))

from author_hud_visual_kit import main

if __name__ == "__main__":
    sys.exit(main())

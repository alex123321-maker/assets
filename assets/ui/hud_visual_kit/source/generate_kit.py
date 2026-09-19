#!/usr/bin/env python3
"""Source runner for hud_visual_kit asset package."""
import sys
from pathlib import Path

# Add tools to sys.path
tools_dir = Path(__file__).resolve().parent.parent.parent.parent / "tools"
sys.path.insert(0, str(tools_dir))

from author_hud_visual_kit import main

if __name__ == "__main__":
    sys.exit(main())

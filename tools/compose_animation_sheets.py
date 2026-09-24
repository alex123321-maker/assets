"""Compose animation filmstrip sheets from rendered keyframe images.
Runs in system Python (using Pillow).

Usage:
  python tools/compose_animation_sheets.py --asset assets/characters/zombie
"""

from __future__ import annotations
import argparse
import sys
from pathlib import Path
from PIL import Image

def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--asset", required=True, type=Path, help="Path to character package")
    return parser.parse_args()

def main():
    args = parse_args()
    review_dir = args.asset / "review"
    temp_dir = review_dir / "_temp_frames"

    if not temp_dir.exists():
        print(f"Warning: {temp_dir} does not exist. No frames to composite.")
        return 0

    actions = ["idle", "move", "attack", "hit", "death"]
    for act in actions:
        frame_files = sorted(temp_dir.glob(f"{act}_f*.png"))
        if not frame_files:
            print(f"No frames found for {act}")
            continue

        frame_w, frame_h = 256, 256
        strip = Image.new("RGBA", (frame_w * len(frame_files), frame_h), (18, 20, 24, 255))
        for idx, fpath in enumerate(frame_files):
            with Image.open(fpath) as im:
                if im.size != (frame_w, frame_h):
                    im = im.resize((frame_w, frame_h), Image.Resampling.BOX)
                strip.paste(im, (idx * frame_w, 0))
            fpath.unlink()

        out_path = review_dir / f"anim_{act}.png"
        strip.save(str(out_path.resolve()))
        print(f"Composited {out_path.name} from {len(frame_files)} frames.")

    # Clean up temp dir
    try:
        temp_dir.rmdir()
    except OSError:
        pass

    return 0

if __name__ == "__main__":
    sys.exit(main())

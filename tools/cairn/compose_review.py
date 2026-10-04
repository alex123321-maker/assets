"""Compose neutral Cairn review comparisons and media from real render images.

Requires Pillow; videos use installed FFmpeg with a shared finite deadline.
Original references/rendered frames are preserved. The source frame numbers
determine playback timing; resampling to 30 fps repeats sampled images and is
playback evidence only, not evidence of runtime performance.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path
import re
import shutil
import statistics
import subprocess
import tempfile
import time

from PIL import Image, ImageDraw, ImageFont, ImageOps


BACKGROUND = (24, 28, 31)
TEXT_COLOR = (218, 220, 223)
LABEL_HEIGHT = 36
FRAME_PATTERN = re.compile(r"frame_(\d+)\.png$", re.IGNORECASE)


def _hash(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _image(path: Path) -> Image.Image:
    with Image.open(path) as source:
        source.load()
        return source.convert("RGBA")


def _crop(image: Image.Image, bounds: tuple[int, int, int, int], label: str):
    x0, y0, x1, y1 = bounds
    if not (0 <= x0 < x1 <= image.width and 0 <= y0 < y1 <= image.height):
        raise ValueError(f"{label} crop {bounds} lies outside {image.size}")
    return image.crop(bounds)


def _tile(image: Image.Image, label: str, width: int, height: int) -> Image.Image:
    canvas = Image.new("RGB", (width, height + LABEL_HEIGHT), BACKGROUND)
    fitted = ImageOps.contain(image, (width, height), Image.Resampling.LANCZOS)
    position = ((width - fitted.width) // 2, (height - fitted.height) // 2)
    canvas.paste(fitted, position, fitted.getchannel("A"))
    draw = ImageDraw.Draw(canvas)
    draw.text((12, height + 7), label, fill=TEXT_COLOR,
              font=ImageFont.load_default(size=17))
    return canvas


def compose_comparisons(review_dir: Path, reference: Path, *,
                        front_crop=(0, 0, 382, 580),
                        iso_crop=(452, 568, 904, 1197), tile_size=640):
    source = _image(reference)
    rows = []
    for view, bounds in (("front", front_crop), ("iso", iso_crop)):
        reference_view = _crop(source, bounds, view)
        model_view = _image(review_dir / f"{view}.png")
        rows.append((_tile(reference_view, f"Reference | {view}", tile_size, tile_size),
                     _tile(model_view, f"Model | {view}", tile_size, tile_size)))
    result = Image.new("RGB", (tile_size * 2, (tile_size + LABEL_HEIGHT) * 2), BACKGROUND)
    for row, pair in enumerate(rows):
        for column, tile in enumerate(pair):
            result.paste(tile, (column * tile_size, row * (tile_size + LABEL_HEIGHT)))
    result.save(review_dir / "reference_comparison.png")

    result = Image.new("RGB", (tile_size * 2, tile_size + LABEL_HEIGHT), BACKGROUND)
    for column, variant in enumerate(("a", "b")):
        image = _image(review_dir / f"blockout_{variant}_iso.png")
        result.paste(_tile(image, f"Blockout {variant.upper()} | iso", tile_size, tile_size),
                     (column * tile_size, 0))
    result.save(review_dir / "blockout_comparison.png")
    return {"reference": {"filename": reference.name, "sha256": _hash(reference),
                           "front_crop_px": list(front_crop), "iso_crop_px": list(iso_crop)},
            "stills": ["reference_comparison.png", "blockout_comparison.png"],
            "aspect_ratio_preserved": True}


def _frame_files(directory: Path) -> list[tuple[int, Path]]:
    if not directory.is_dir():
        raise ValueError(f"missing rendered frame directory: {directory}")
    frames = []
    for path in directory.iterdir():
        match = FRAME_PATTERN.fullmatch(path.name)
        if match and path.is_file():
            frames.append((int(match.group(1)), path))
    frames.sort(key=lambda item: item[0])
    if not frames:
        raise ValueError(f"no frame_NNNN.png renders in {directory}")
    if len({index for index, _ in frames}) != len(frames):
        raise ValueError(f"duplicate numerical frame indices in {directory}")
    return frames


def _filmstrip(frames: list[tuple[int, Path]], output: Path, clip: str,
               sample_count=8, tile_size=240):
    if len(frames) <= sample_count:
        indices = list(range(len(frames)))
    else:
        indices = [round(i * (len(frames) - 1) / (sample_count - 1))
                   for i in range(sample_count)]
    strip = Image.new("RGB", (tile_size * len(indices), tile_size + LABEL_HEIGHT), BACKGROUND)
    for column, index in enumerate(indices):
        frame, path = frames[index]
        tile = _tile(_image(path), f"{clip} | frame {frame}", tile_size, tile_size)
        strip.paste(tile, (column * tile_size, 0))
    strip.save(output)
    return [frames[index][0] for index in indices]


def _concat_quote(path: Path) -> str:
    # FFconcat escaping is independent of shell escaping; commands use argv.
    return "'" + path.resolve().as_posix().replace("'", "'\\''") + "'"


def _video(frames: list[tuple[int, Path]], output: Path, *, source_fps: float,
           output_fps: int, ffmpeg: str, deadline: float):
    intervals = [frames[i + 1][0] - frames[i][0] for i in range(len(frames) - 1)]
    last_interval = statistics.median(intervals) if intervals else 1
    durations = [interval / source_fps for interval in intervals] + [last_interval / source_fps]
    lines = ["ffconcat version 1.0"]
    size = None
    for (_, path), duration in zip(frames, durations):
        with Image.open(path) as image:
            image.verify()
            dimensions = image.size
        if size is None:
            size = dimensions
        elif dimensions != size:
            raise ValueError(f"mixed frame image dimensions in {output.stem}")
        lines.extend([f"file {_concat_quote(path)}", f"duration {duration:.12f}"])
    lines.append(f"file {_concat_quote(frames[-1][1])}")
    remaining = deadline - time.monotonic()
    if remaining <= 0:
        raise TimeoutError("shared review-media deadline expired before FFmpeg")
    with tempfile.TemporaryDirectory(prefix="cairn_review_media_") as directory:
        concat = Path(directory) / "frames.ffconcat"
        concat.write_text("\n".join(lines) + "\n", encoding="utf-8")
        command = [ffmpeg, "-hide_banner", "-loglevel", "error", "-y", "-f", "concat", "-safe", "0",
                   "-i", str(concat), "-t", f"{sum(durations):.12f}", "-vf",
                   f"pad=ceil(iw/2)*2:ceil(ih/2)*2,fps={output_fps}",
                   "-c:v", "libx264", "-preset", "fast", "-crf", "18", "-pix_fmt", "yuv420p",
                   "-threads", "1", "-map_metadata", "-1", "-fflags", "+bitexact",
                   "-flags:v", "+bitexact", "-movflags", "+faststart", str(output)]
        result = subprocess.run(command, timeout=min(60, remaining), capture_output=True,
                                text=True, encoding="utf-8", errors="replace")
        if result.returncode:
            raise RuntimeError(f"FFmpeg failed for {output.name}: {result.stderr.strip()}")
    return {"video": output.name, "provided_frame_count": len(frames),
            "source_frame_indices": [index for index, _ in frames],
            "source_fps": source_fps, "output_fps": output_fps,
            "sampling_intervals_frames": intervals,
            "preview_duration_s": round(sum(durations), 9),
            "input_dimensions_px": list(size),
            "evidence_scope": "playback_from_supplied_render_samples; no runtime performance claim"}


def compose_review(review_dir: Path, reference: Path, *, frames_dir: Path | None = None,
                   clips=("idle", "move", "attack_0", "attack_1", "death"),
                   front_crop=(0, 0, 382, 580), iso_crop=(452, 568, 904, 1197),
                   source_fps=30.0, output_fps=30, timeout_seconds=180,
                   stills_only=False):
    if not math.isfinite(source_fps) or source_fps <= 0:
        raise ValueError("source_fps must be finite and positive")
    if not 24 <= output_fps <= 30:
        raise ValueError("output_fps must be 24..30")
    if not math.isfinite(timeout_seconds) or timeout_seconds <= 0:
        raise ValueError("timeout_seconds must be finite and positive")
    deadline = time.monotonic() + timeout_seconds
    review_dir = Path(review_dir)
    frames_dir = Path(frames_dir) if frames_dir else review_dir / "frames"
    report = compose_comparisons(review_dir, Path(reference), front_crop=front_crop, iso_crop=iso_crop)
    report["animations"] = {}
    if not stills_only:
        ffmpeg = shutil.which("ffmpeg")
        if not ffmpeg:
            raise RuntimeError("FFmpeg executable unavailable")
        for clip in clips:
            if not re.fullmatch(r"[A-Za-z0-9_-]+", clip):
                raise ValueError(f"invalid clip name: {clip}")
            frames = _frame_files(frames_dir / clip)
            sampled = _filmstrip(frames, review_dir / f"anim_{clip}.png", clip)
            media = _video(frames, review_dir / f"anim_{clip}.mp4", source_fps=source_fps,
                           output_fps=output_fps, ffmpeg=ffmpeg, deadline=deadline)
            media["filmstrip"] = f"anim_{clip}.png"
            media["filmstrip_frame_indices"] = sampled
            media["source_frame_sha256"] = {path.name: _hash(path) for _, path in frames}
            report["animations"][clip] = media
    (review_dir / "media_manifest.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--review-dir", type=Path, required=True)
    parser.add_argument("--reference", type=Path, required=True)
    parser.add_argument("--frames-dir", type=Path)
    parser.add_argument("--clips", nargs="+", default=["idle", "move", "attack_0", "attack_1", "death"])
    parser.add_argument("--reference-front-crop", nargs=4, type=int, default=(0, 0, 382, 580))
    parser.add_argument("--reference-iso-crop", nargs=4, type=int, default=(452, 568, 904, 1197))
    parser.add_argument("--source-fps", type=float, default=30.0)
    parser.add_argument("--fps", type=int, default=30)
    parser.add_argument("--timeout-seconds", type=float, default=180)
    parser.add_argument("--stills-only", action="store_true")
    args = parser.parse_args()
    try:
        report = compose_review(args.review_dir, args.reference, frames_dir=args.frames_dir,
                                clips=args.clips, front_crop=tuple(args.reference_front_crop),
                                iso_crop=tuple(args.reference_iso_crop), source_fps=args.source_fps,
                                output_fps=args.fps, timeout_seconds=args.timeout_seconds,
                                stills_only=args.stills_only)
        print(json.dumps({"stills": report["stills"], "clips": list(report["animations"])}))
        return 0
    except (OSError, ValueError, RuntimeError, TimeoutError, subprocess.TimeoutExpired) as exc:
        print(json.dumps({"media_error": str(exc)}))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())

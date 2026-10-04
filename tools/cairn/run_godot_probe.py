"""Create an isolated Godot 4.6 asset preview and run a bounded pose probe.

Never touches the adjacent game checkout or deletes shared scratch directories.
The temporary project is retained in .local/cairn_runtime for inspection.
"""
from __future__ import annotations

import argparse
import os
from pathlib import Path
import shutil
import subprocess
import time
import uuid

ROOT = Path(__file__).resolve().parents[2]
DEFAULT_GODOT = Path(r"D:\ProgramFiles\godot\Godot_v4.6.1-stable_win64_console.exe")
PROJECT = '''config_version=5

[application]
config/name="Cairn Asset Preview"
run/main_scene="res://runtime/cairn_preview.tscn"
config/features=PackedStringArray("4.6", "GL Compatibility")

[display]
window/size/viewport_width=960
window/size/viewport_height=720
window/size/window_width_override=960
window/size/window_height_override=720

[rendering]
renderer/rendering_method="gl_compatibility"
renderer/rendering_method.mobile="gl_compatibility"
environment/defaults/default_clear_color=Color(0.11, 0.14, 0.13, 1)

[physics]
common/physics_ticks_per_second=30
'''


def run(command: list[str], log_path: Path, deadline: float) -> subprocess.CompletedProcess[str]:
    remaining = deadline - time.monotonic()
    if remaining <= 0:
        raise TimeoutError("Cairn runtime probe exceeded its total deadline")
    flags = subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0
    try:
        result = subprocess.run(command, capture_output=True, text=True,
                                encoding="utf-8", errors="replace", timeout=remaining,
                                creationflags=flags)
    except subprocess.TimeoutExpired as error:
        stdout = error.stdout or b""
        stderr = error.stderr or b""
        if isinstance(stdout, bytes):
            stdout = stdout.decode("utf-8", "replace")
        if isinstance(stderr, bytes):
            stderr = stderr.decode("utf-8", "replace")
        log_path.write_text(stdout + stderr + "\nTIMEOUT\n", encoding="utf-8")
        raise TimeoutError(f"TIMEOUT; log: {log_path}") from error
    log_path.write_text(result.stdout + result.stderr, encoding="utf-8")
    if result.returncode != 0 or "SCRIPT ERROR:" in result.stderr or "Parse Error:" in result.stderr:
        raise RuntimeError(f"Command failed ({result.returncode}); log: {log_path}\n{result.stderr[-4000:]}")
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--asset", type=Path, default=Path("assets/characters/bosses/cairn"))
    parser.add_argument("--godot", type=Path, default=Path(os.environ.get("GODOT_BIN", str(DEFAULT_GODOT))))
    parser.add_argument("--output", type=Path)
    parser.add_argument("--render", action="store_true", help="Render real Godot screenshots instead of the headless structure probe")
    parser.add_argument("--movie", action="store_true", help="Render all evaluated frames and encode runtime_preview.mp4 with ffmpeg")
    parser.add_argument("--check-only", action="store_true", help="Parse scripts; does not need a model and does not claim runtime checks")
    parser.add_argument("--timeout", type=float, default=300.0, help="Total command deadline, including import/probe/encoding")
    args = parser.parse_args()
    if not 0.0 < args.timeout <= 300.0:
        parser.error("--timeout must be greater than zero and at most 300 seconds")
    asset = args.asset.resolve()
    output = (args.output or asset / "review" / "godot").resolve()
    output.mkdir(parents=True, exist_ok=True)
    godot = args.godot.resolve()
    if not godot.is_file():
        raise FileNotFoundError(f"Godot executable not found: {godot}")
    deadline = time.monotonic() + args.timeout
    project = ROOT / ".local" / "cairn_runtime" / uuid.uuid4().hex
    project.mkdir(parents=True, exist_ok=False)
    shutil.copytree(asset / "source" / "runtime", project / "runtime")
    shutil.copy2(Path(__file__).with_name("godot_probe.gd"), project / "godot_probe.gd")
    (project / "project.godot").write_text(PROJECT, encoding="utf-8")
    model = asset / "output" / "model.glb"
    if model.is_file():
        shutil.copy2(model, project / "cairn.glb")
    elif not args.check_only:
        raise FileNotFoundError(f"Model has not been built: {model}")
    print(f"Isolated preview project: {project}", flush=True)
    run([str(godot), "--headless", "--path", str(project), "--editor", "--quit"],
        output / "import.log", deadline)
    for script in ["runtime/cairn_motion_modifier.gd", "runtime/cairn_preview.gd", "godot_probe.gd"]:
        run([str(godot), "--headless", "--path", str(project), "--check-only", "--script", "res://" + script],
            output / (Path(script).stem + "_parse.log"), deadline)
    if args.check_only:
        print("Cairn runtime scripts parsed; model behavior has not been checked.")
        return
    command = [str(godot), "--path", str(project), "--fixed-fps", "30",
               "--disable-vsync", "--audio-driver", "Dummy",
               "--rendering-method", "gl_compatibility", "--resolution", "960x720",
               "--script", "res://godot_probe.gd"]
    rendered = args.render or args.movie
    if not rendered:
        command.append("--headless")
    command += ["--", "--output=" + str(output)]
    if not rendered:
        command.append("--no-render")
    if args.movie:
        command.append("--frames=" + str(project / "frames"))
    result = run(command, output / "probe.log", deadline)
    if "CAIRN_PROBE_COMPLETE" not in result.stdout:
        raise RuntimeError(f"Runtime completion marker missing; see {output / 'probe.log'}")
    if args.movie:
        ffmpeg = shutil.which("ffmpeg")
        if not ffmpeg:
            raise FileNotFoundError("ffmpeg is required for --movie; rendered frames were retained in the isolated project")
        run([ffmpeg, "-y", "-fflags", "+bitexact", "-framerate", "30", "-i", str(project / "frames" / "frame_%05d.png"),
             "-map_metadata", "-1", "-c:v", "libx264", "-threads", "1", "-flags:v", "+bitexact",
             "-pix_fmt", "yuv420p", "-crf", "18", "-movflags", "+faststart",
             str(output / "runtime_preview.mp4")], output / "encode.log", deadline)
    print(result.stdout.strip())
    print(f"Runtime evidence: {output}")


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""Build-bound evidence and browser review packets. No AI verdicts are generated."""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import shutil
import struct
import subprocess
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import quote

ROOT = Path(__file__).resolve().parents[1]
IMAGE_SUFFIXES = {".png", ".jpg", ".jpeg", ".webp"}
TEXT_SUFFIXES = {".py", ".json", ".md", ".txt", ".svg", ".tres", ".tscn", ".gd",
                 ".yaml", ".yml", ".toml", ".glsl", ".vert", ".frag", ".csv"}


class QualityError(ValueError):
    pass


def nonempty(value: object) -> bool:
    return isinstance(value, str) and bool(value.strip())


def read_json(path: Path) -> dict:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        raise QualityError(f"Cannot read {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise QualityError(f"Expected JSON object: {path}")
    return value


def write_json(path: Path, value: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def digest(value: object) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, ensure_ascii=False).encode()).hexdigest()


def content_hash(name: str, raw: bytes) -> str:
    # Git commonly converts CRLF on Windows and LF on CI. Binary image/GLB bytes
    # remain exact; text differences other than line endings still invalidate evidence.
    if Path(name).suffix.lower() in TEXT_SUFFIXES:
        raw = raw.replace(b"\r\n", b"\n")
    return hashlib.sha256(raw).hexdigest()


def file_hash(path: Path) -> str:
    return content_hash(path.name, path.read_bytes())


def local_path(root: Path, name: str) -> Path:
    if not isinstance(name, str) or not name or Path(name).is_absolute():
        raise QualityError(f"Expected repository-relative path: {name!r}")
    path = (root / name).resolve()
    if not path.is_relative_to(root.resolve()):
        raise QualityError(f"Path leaves repository: {name}")
    return path


def collect(root: Path, names: list[str]) -> dict[str, str]:
    if not isinstance(names, list) or not names:
        raise QualityError("File lists must not be empty")
    result = {}
    for name in names:
        path = local_path(root, name)
        if not path.exists():
            raise QualityError(f"Missing evidence/input: {name}")
        files = sorted(path.rglob("*")) if path.is_dir() else [path]
        found = False
        for item in files:
            if not item.is_file() or "__pycache__" in item.parts or item.suffix == ".pyc":
                continue
            if not item.resolve().is_relative_to(root.resolve()):
                raise QualityError(f"Linked file leaves repository: {item}")
            result[item.relative_to(root).as_posix()] = file_hash(item)
            found = True
        if not found:
            raise QualityError(f"Empty evidence/input directory: {name}")
    return result


def load_contract(root: Path, package: Path) -> dict:
    contract = read_json(package / "quality.json")
    if contract.get("version") != 1:
        raise QualityError("quality.json version must be 1")
    for key in ("inputs", "artifacts", "commands", "criteria"):
        if not isinstance(contract.get(key), list) or not contract[key]:
            raise QualityError(f"Fill quality.json {key} before building")
    for command in contract["commands"]:
        if not isinstance(command, list) or not command or not all(isinstance(x, str) and x for x in command):
            raise QualityError("Commands must be nonempty argument arrays (no shell command strings)")
        executable = command[0].replace("\\", "/").rsplit("/", 1)[-1].lower()
        if executable in {"blender", "blender.exe"} and any(x in command for x in ("--python", "--python-expr")):
            options = command[:command.index("--")] if "--" in command else command
            try:
                flag_index = options.index("--python-exit-code")
                exit_code = int(options[flag_index + 1])
                script_index = min(options.index(x) for x in ("--python", "--python-expr") if x in options)
                if flag_index > script_index:
                    exit_code = 0  # Blender executes Python actions in argument order.
            except (ValueError, IndexError):
                exit_code = 0
            if not 1 <= exit_code <= 255:
                raise QualityError("Blender Python recipes require --python-exit-code 1 before --python/--python-expr; otherwise script failures can return success")
    ids = set()
    for criterion in contract["criteria"]:
        if not isinstance(criterion, dict) or not nonempty(criterion.get("id")) or not nonempty(criterion.get("target")):
            raise QualityError("Each visual criterion needs an id and a concrete target")
        if criterion["id"] in ids:
            raise QualityError(f"Duplicate criterion: {criterion['id']}")
        ids.add(criterion["id"])
        if not isinstance(criterion.get("evidence"), list) or not criterion["evidence"]:
            raise QualityError(f"Declare image evidence for {criterion['id']}")
    references = contract.get("references")
    if not isinstance(references, list):
        raise QualityError("references must be a list")
    if not references and not str(contract.get("reference_free_reason", "")).strip():
        raise QualityError("Declare references, or explain the request-only art direction")
    for ref in references:
        if not isinstance(ref, dict):
            raise QualityError("Each reference must be an object")
        if ref.get("status") not in {"approved", "candidate"} or not ref.get("provenance"):
            raise QualityError("References need candidate/approved status and provenance")
        if ref["status"] == "approved" and not ref.get("approval"):
            raise QualityError("Approved reference requires an actual user/Issue decision citation")
        if not re.fullmatch(r"[0-9a-f]{64}", str(ref.get("sha256", ""))):
            raise QualityError("Reference requires sha256 captured when its identity is recorded")
        if file_hash(local_path(root, ref["path"])) != ref["sha256"]:
            raise QualityError(f"Reference changed: {ref['path']}; reconcile the design decision explicitly")
    return contract


def input_state(root: Path, package: Path, contract: dict) -> dict:
    names = contract["inputs"] + [r["path"] for r in contract["references"]]
    names += [(package / "quality.json").relative_to(root).as_posix()]
    for filename in ("request.md", "manifest.json"):
        if (package / filename).exists():
            names.append((package / filename).relative_to(root).as_posix())
    if (package / "manifest.json").exists():
        manifest = read_json(package / "manifest.json")
        source = local_path(root, (package / manifest["source"]).relative_to(root).as_posix())
        names.append(source.relative_to(root).as_posix())
    # Include entry scripts even when a recipe author forgets them in inputs.
    # Imported helpers/resources still must be declared explicitly.
    for command in contract["commands"]:
        for argument in command:
            if argument.endswith(".py") and not Path(argument).is_absolute():
                script = local_path(root, argument)
                if script.is_file():
                    names.append(argument)
    return collect(root, names)


def glb_metrics(path: Path) -> dict:
    """Read primitive counts from the export, not the generator's metrics report."""
    raw = path.read_bytes()
    if len(raw) < 20 or raw[:4] != b"glTF":
        raise QualityError(f"Invalid GLB header: {path}")
    version, length, chunk_length, chunk_type = struct.unpack_from("<IIII", raw, 4)
    if version != 2 or length != len(raw) or chunk_type != 0x4E4F534A or chunk_length > len(raw) - 20:
        raise QualityError(f"Invalid GLB structure: {path}")
    try:
        data = json.loads(raw[20:20 + chunk_length])
        triangles = 0
        used_materials = set()
        for mesh in data["meshes"]:
            for primitive in mesh["primitives"]:
                if primitive.get("mode", 4) != 4:
                    raise QualityError(f"Triangle-list GLB required for budget check: {path}")
                accessor = primitive.get("indices", primitive["attributes"]["POSITION"])
                count = data["accessors"][accessor]["count"]
                if not isinstance(count, int) or count <= 0 or count % 3:
                    raise QualityError(f"Invalid triangle count in {path}")
                triangles += count // 3
                used_materials.add(primitive.get("material", "default"))
        if not triangles:
            raise QualityError(f"Empty GLB: {path}")
        return {"triangles": triangles, "materials": len(used_materials)}
    except (KeyError, IndexError, TypeError, ValueError) as exc:
        raise QualityError(f"Cannot inspect GLB {path}: {exc}") from exc


def inspect_artifacts(root: Path, contract: dict, artifacts: dict) -> dict:
    measurements = {}
    for name in artifacts:
        path = local_path(root, name)
        if path.suffix.lower() in IMAGE_SUFFIXES:
            try:
                from PIL import Image
                with Image.open(path) as im:
                    im.verify()
            except (ImportError, OSError, ValueError) as exc:
                raise QualityError(f"Cannot decode image {name}: {exc}") from exc
        if path.suffix.lower() != ".glb":
            continue
        actual = glb_metrics(path)
        measurements[name] = actual
        owner = next((p for p in path.parents if (p / "manifest.json").is_file() and p.is_relative_to(root)), None)
        if owner is None:
            raise QualityError(f"GLB has no owning manifest: {name}")
        manifest = read_json(owner / "manifest.json")
        for field in ("triangles", "materials"):
            budget = manifest.get("budgets", {}).get(f"max_{field}")
            if isinstance(budget, int) and actual[field] > budget:
                raise QualityError(f"{name}: {field} {actual[field]} exceeds budget {budget}")
        metrics = owner / "review" / "metrics.json"
        if metrics.is_file():
            if metrics.relative_to(root).as_posix() not in artifacts:
                raise QualityError(f"Metrics used for validation must be included in artifacts: {metrics}")
            reported = read_json(metrics)
            if reported.get("triangles") != actual["triangles"]:
                raise QualityError(f"{name}: triangle count disagrees with metrics.json")
            if "materials" in reported and reported["materials"] != actual["materials"]:
                raise QualityError(f"{name}: material count disagrees with metrics.json")
    for criterion in contract["criteria"]:
        for name in criterion["evidence"]:
            if name not in artifacts or Path(name).suffix.lower() not in IMAGE_SUFFIXES:
                raise QualityError(f"{criterion['id']}: image not in built artifacts: {name}")
    return measurements


def check_manifest_outputs(root: Path, package: Path, artifacts: dict) -> None:
    """A recipe cannot certify a partial delivery by leaving exports out of its list."""
    manifest_path = package / "manifest.json"
    if not manifest_path.exists():
        return
    manifest = read_json(manifest_path)
    outputs = manifest.get("outputs", {})
    if not isinstance(outputs, dict):
        raise QualityError("manifest outputs must be an object of paths")
    prefix = package.relative_to(root).as_posix()
    names = []
    for relative in outputs.values():
        if not isinstance(relative, str):
            raise QualityError("Each manifest output must be a file/directory path")
        names.append(f"{prefix}/{relative}")
    for view in manifest.get("review", {}).get("required_views", []):
        names.append(f"{prefix}/review/{view}.png")
    for name in names:
        for required in collect(root, [name]):
            if required not in artifacts:
                raise QualityError(f"Declared output/view omitted from build artifacts: {required}")


def inspect_comparisons(root: Path, contract: dict, inputs: dict, artifacts: dict) -> None:
    comparisons = contract.get("comparisons", [])
    if not isinstance(comparisons, list):
        raise QualityError("comparisons must be a list of render receipts")
    if not comparisons:
        return
    try:
        from .review_comparison import validate_pair
    except ImportError:
        from review_comparison import validate_pair
    for name in comparisons:
        if not isinstance(name, str) or name not in artifacts:
            raise QualityError("Comparison receipt must be a built artifact")
        try:
            pair = validate_pair(root, local_path(root, name))
            for side in ("before", "after"):
                if pair[side]["source"] not in inputs or pair[side]["image"] not in artifacts:
                    raise QualityError("Comparison sources/images must be tracked inputs/artifacts")
        except (KeyError, TypeError, ValueError, OSError) as exc:
            raise QualityError(f"Invalid comparison {name}: {exc}") from exc


def build(root: Path, package: Path) -> dict:
    evidence_path = package / "review" / "evidence.json"
    evidence_path.unlink(missing_ok=True)  # A failed run must not leave a valid old build receipt.
    contract = load_contract(root, package)
    before = input_state(root, package, contract)
    protected = {package / "review" / name: (package / "review" / name).read_bytes()
                 if (package / "review" / name).exists() else None
                 for name in ("visual_review.json", "review.md")}
    try:
        for command in contract["commands"]:
            print(f"Running: {command}", flush=True)
            subprocess.run(command, cwd=root, check=True, shell=False)
    finally:
        changed = []
        for path, original in protected.items():
            current = path.read_bytes() if path.exists() else None
            if current != original:
                changed.append(path.name)
                if original is None:
                    path.unlink(missing_ok=True)
                else:
                    path.parent.mkdir(parents=True, exist_ok=True)
                    path.write_bytes(original)
        if changed:
            raise QualityError(f"Build wrote protected reviews: {changed}; originals restored. Record observations after build.")
    after = input_state(root, package, contract)
    if after != before:
        raise QualityError("Build changed its inputs/request/reference. Author first, then rebuild frozen inputs.")
    artifacts = collect(root, contract["artifacts"])
    check_manifest_outputs(root, package, artifacts)
    if set(before) & set(artifacts):
        raise QualityError("Inputs and generated artifacts must be separate")
    forbidden = {evidence_path.resolve(), (package / "review" / "visual_review.json").resolve()}
    if any(local_path(root, name) in forbidden for name in artifacts):
        raise QualityError("Do not include evidence.json or visual_review.json in artifacts")
    measurements = inspect_artifacts(root, contract, artifacts)
    inspect_comparisons(root, contract, before, artifacts)
    record = {"version": 1, "hash_policy": "sha256-text-lf-v1", "built_at": datetime.now(timezone.utc).isoformat(),
              "inputs": before, "artifacts": artifacts, "measurements": measurements}
    record["digest"] = digest(record)
    write_json(evidence_path, record)
    review_path = package / "review" / "visual_review.json"
    if not review_path.exists():
        write_json(review_path, {"evidence_digest": record["digest"], "reviewer": "",
            "inspected_images": [], "criteria": [
                {"id": c["id"], "status": "not_reviewed", "observation": ""} for c in contract["criteria"]],
            "gameplay": {"status": "not_checked", "evidence": [], "notes": ""},
            "known_deviations": [], "feedback_resolution": []})
    return record


def check(root: Path, package: Path, require_review: bool = False, *, draft: bool = False) -> dict:
    contract = load_contract(root, package)
    record = read_json(package / "review" / "evidence.json")
    if record.get("version") != 1 or record.get("hash_policy") != "sha256-text-lf-v1":
        raise QualityError("Unsupported evidence receipt version/hash policy; rebuild")
    claimed = record.get("digest")
    if claimed != digest({k: v for k, v in record.items() if k != "digest"}):
        raise QualityError("Evidence receipt is malformed")
    if record.get("inputs") != input_state(root, package, contract):
        raise QualityError("STALE BUILD: inputs/recipe/references changed; run quality_gate.py build")
    artifacts = collect(root, contract["artifacts"])
    check_manifest_outputs(root, package, artifacts)
    if record.get("artifacts") != artifacts:
        raise QualityError("STALE EVIDENCE: exports/images/metrics changed; rebuild")
    if record.get("measurements") != inspect_artifacts(root, contract, artifacts):
        raise QualityError("Export measurements differ from build receipt")
    inspect_comparisons(root, contract, record["inputs"], artifacts)
    if not require_review:
        return record
    review = read_json(package / "review" / "visual_review.json")
    if review.get("evidence_digest") != claimed:
        raise QualityError("STALE VISUAL REVIEW: inspect current images and record current digest")
    if not draft and not nonempty(review.get("reviewer")):
        raise QualityError("Visual review must identify its actual author/model")
    inspected = review.get("inspected_images", [])
    required = {n for c in contract["criteria"] for n in c["evidence"]}
    required.update(r["path"] for r in contract["references"] if Path(r["path"]).suffix.lower() in IMAGE_SUFFIXES)
    if not isinstance(inspected, list) or not all(isinstance(n, str) for n in inspected):
        raise QualityError("inspected_images must contain image paths")
    if not draft and not required.issubset(set(inspected)):
        raise QualityError("Visual review does not list every required inspected image/reference")
    rows = review.get("criteria", [])
    if not isinstance(rows, list) or not all(isinstance(c, dict) for c in rows) or len(rows) != len(contract["criteria"]):
        raise QualityError("Visual review must cover exactly the declared criteria")
    if not all(nonempty(c.get("id")) for c in rows):
        raise QualityError("Visual review criterion ids must be strings")
    by_id = {c["id"]: c for c in rows}
    if len(by_id) != len(rows) or set(by_id) != {c["id"] for c in contract["criteria"]}:
        raise QualityError("Visual review must cover exactly the declared criteria without duplicates")
    for criterion in contract["criteria"]:
        result = by_id.get(criterion["id"], {})
        allowed = {"pass", "fail", "not_reviewed"} if draft else {"pass"}
        if result.get("status") not in allowed or (result.get("status") != "not_reviewed" and not nonempty(result.get("observation"))):
            raise QualityError(f"Visual criterion not passed with observation: {criterion['id']}")
        if result.get("status") != "not_reviewed" and not set(criterion["evidence"]).issubset(inspected):
            raise QualityError(f"Missing inspected images for observed criterion: {criterion['id']}")
    gameplay = review.get("gameplay", {})
    if gameplay.get("status") not in {"checked", "mockup_only", "not_checked"}:
        raise QualityError("Invalid gameplay review status")
    if gameplay.get("status") in {"checked", "mockup_only"}:
        if not gameplay.get("evidence") or any(n not in artifacts for n in gameplay["evidence"]):
            raise QualityError("Gameplay review requires built evidence")
    if not draft and contract.get("require_engine_review") and gameplay.get("status") != "checked":
        raise QualityError("This request requires an engine review; a mockup is insufficient")
    if not draft and not nonempty(gameplay.get("notes")):
        raise QualityError("Explain the missing engine verification")
    return record


def verify_clean(root: Path, package: Path) -> dict:
    """Run the real recipe with only declared inputs, without touching the working asset."""
    original = check(root, package)
    relative = package.relative_to(root)
    with tempfile.TemporaryDirectory(prefix="asset-clean-build-") as folder:
        isolated = Path(folder).resolve()
        for name in original["inputs"]:
            destination = local_path(isolated, name)
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(local_path(root, name), destination)
        isolated_package = isolated / relative
        # Preserve reviewer documents so builders cannot silently manufacture replacements.
        for name in ("review.md", "visual_review.json"):
            source = package / "review" / name
            if source.exists():
                destination = isolated_package / "review" / name
                destination.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(source, destination)
        rebuilt = build(isolated, isolated_package)
        if set(rebuilt["artifacts"]) != set(original["artifacts"]):
            raise QualityError("Clean build produced a different artifact set")
        if rebuilt["measurements"] != original["measurements"]:
            raise QualityError("Clean build changed exported measurements")
        changed = [name for name, value in rebuilt["artifacts"].items()
                   if value != original["artifacts"][name]]
        image_differences = {}
        mismatches = []
        receipts = load_contract(root, package).get("comparisons", [])
        for name in changed:
            if Path(name).suffix.lower() in IMAGE_SUFFIXES:
                from PIL import Image, ImageChops, ImageStat
                with Image.open(root / name) as a, Image.open(isolated / name) as b:
                    if a.size != b.size:
                        mismatches.append(name)
                        continue
                    difference = ImageChops.difference(a.convert("RGBA"), b.convert("RGBA"))
                    maximum = max(high for low, high in difference.getextrema())
                    mean = max(ImageStat.Stat(difference).mean)
                    image_differences[name] = {"max": maximum, "mean": mean}
                    # Measured EEVEE repeat renders differ sparsely by 1-2 steps.
                    # The mean bound rejects even a uniform one-step color shift.
                    if maximum > 2 or mean > 0.001:
                        mismatches.append(name)
            elif name not in receipts:
                mismatches.append(name)
        if mismatches:
            raise QualityError(f"Clean build differs from committed evidence beyond image rounding tolerance: {mismatches}; image deltas: {image_differences}")
    return {"regenerated_artifacts": len(original["artifacts"]),
            "byte_different_artifacts": changed,
            "image_max_channel_delta_8bit": image_differences,
            "note": "All outputs regenerated from declared inputs; image deltas <=2/255 max and <=0.001/255 channel mean, other artifacts exact (comparison receipts validated separately). Not artistic approval."}


def initialize(root: Path, package: Path) -> None:
    path = package / "quality.json"
    if path.exists():
        raise QualityError(f"Already exists: {path}")
    prefix = package.relative_to(root).as_posix()
    manifest = read_json(package / "manifest.json")
    views = manifest.get("review", {}).get("required_views", ["iso", "front", "side", "top"])
    images = [f"{prefix}/review/{v}.png" for v in views]
    refs = []
    for ref in sorted((package / "references").glob("*")):
        if ref.suffix.lower() in IMAGE_SUFFIXES:
            refs.append({"path": ref.relative_to(root).as_posix(), "sha256": file_hash(ref),
                         "status": "candidate", "provenance": "", "approval": ""})
    write_json(path, {"version": 1,
        "inputs": [f"{prefix}/{manifest['source']}", "tools/blender/build_voxel_asset.py"],
        "commands": [], "references": refs, "reference_free_reason": "",
        "artifacts": [f"{prefix}/output", *images, f"{prefix}/review/metrics.json"],
        "require_engine_review": False,
        "criteria": [{"id": key, "target": "", "evidence": images[:1]} for key in
                     ("silhouette", "proportions", "materials", "game_scale")]})


def git(root: Path, *args: str) -> str:
    return subprocess.check_output(["git", *args], cwd=root, text=True, encoding="utf-8").strip()


def packet(root: Path, package: Path, revision: str, repository: str, *, draft: bool = False) -> str:
    if not re.fullmatch(r"[\w.-]+/[\w.-]+", repository):
        raise QualityError("Repository must be owner/name")
    record = check(root, package, require_review=True, draft=draft)
    sha = git(root, "rev-parse", "--verify", revision + "^{commit}")
    paths = dict(record["inputs"], **record["artifacts"])
    for extra in ("review/evidence.json", "review/visual_review.json"):
        p = package / extra
        paths[p.relative_to(root).as_posix()] = file_hash(p)
    for name, expected in paths.items():
        try:
            raw = subprocess.check_output(["git", "show", f"{sha}:{name}"], cwd=root, stderr=subprocess.DEVNULL)
        except subprocess.CalledProcessError as exc:
            raise QualityError(f"Commit does not contain {name}; commit evidence before making packet") from exc
        if content_hash(name, raw) != expected:
            raise QualityError(f"Working evidence differs from {sha[:12]}: {name}")
    base = f"https://github.com/{repository}/blob/{sha}/"
    link = lambda name: base + quote(name, safe="/")
    contract = load_contract(root, package)
    review = read_json(package / "review" / "visual_review.json")
    lines = [f"# Asset review: {package.name}", "", f"Commit: `{sha}`", f"Evidence: `{record['digest']}`", "",
        "DRAFT — NOT ACCEPTED. Failed/unreviewed criteria below require review." if draft else "Author self-review recorded — independent art acceptance still required.",
        "Open docs/REVIEW.md at this commit. Inspect images before reading the author's visual conclusions.",
        "Green checks confirm recorded evidence, not beauty or engine performance. State inaccessible images explicitly.", "",
        "## Reference and target"]
    for ref in contract["references"]:
        lines += [f"- {ref['status']}: [{ref['path']}]({link(ref['path'])}); origin: {ref['provenance']}; approval: {ref.get('approval', '')}"]
    if not contract["references"]:
        lines += [contract["reference_free_reason"]]
    for c in contract["criteria"]:
        lines += [f"- **{c['id']}**: {c['target']}"]
    lines += ["", "## Author-reported status (not an independent verdict)"]
    for c in review["criteria"]:
        lines += [f"- {c['id']}: **{c['status']}**"]
    lines += [f"Engine: **{review['gameplay']['status']}**", ""]
    lines += ["", "## Images (open original size)"]
    image_names = {n for c in contract["criteria"] for n in c["evidence"]}
    image_names.update(r["path"] for r in contract["references"] if Path(r["path"]).suffix.lower() in IMAGE_SUFFIXES)
    for name in sorted(image_names):
        lines += [f"[{name}]({link(name)})", f"![{Path(name).name}]({link(name)}?raw=true)", ""]
    for name in contract.get("comparisons", []):
        lines += [f"Comparison camera/light settings and source/image hashes: [{name}]({link(name)})", ""]
    lines += ["## Export measurements", "```json", json.dumps(record["measurements"], indent=2), "```", "",
        "## Evidence and author's review (read after images)"]
    for name in ["docs/REVIEW.md", *(str((package / p).relative_to(root).as_posix()) for p in
                   ("quality.json", "review/evidence.json", "review/visual_review.json"))]:
        lines += [f"- [{name}]({link(name)})"]
    lines += ["", "Return: reviewed SHA; Technical / Art / Engine verdicts separately; inspected image paths;",
        "each active finding's ID, visible symptom, request criterion, and observable acceptance condition.",
        "Do not replace a macro-shape finding with a request for more bevel/noise. Resolve old findings against current evidence."]
    return "\n".join(lines) + "\n"


def check_all(root: Path, base_ref: str | None = None) -> int:
    contracts = sorted((root / "assets").rglob("quality.json"))
    errors = []
    for contract in contracts:
        try:
            check(root, contract.parent, require_review=True)
            print(f"[PASS] {contract.parent.relative_to(root)}: evidence fresh, visual observations recorded (not independently judged)")
        except (QualityError, OSError, ValueError) as exc:
            errors.append(f"{contract.parent.relative_to(root)}: {exc}")
    if base_ref:
        # Base is the PR base SHA, not a checkout-dependent branch name.
        names = git(root, "diff", "--name-only", "--diff-filter=A", base_ref, "HEAD", "--", "assets").splitlines()
        for name in names:
            if name.endswith("/manifest.json") and not name.startswith("assets/_template/"):
                if not (root / name).with_name("quality.json").exists():
                    errors.append(f"New package missing quality.json: {name}")
        old = git(root, "ls-tree", "-r", "--name-only", base_ref, "--", "assets").splitlines()
        for name in old:
            if name.endswith("/quality.json") and (root / name).parent.exists() and not (root / name).exists():
                errors.append(f"Do not remove an existing quality contract: {name}")
    legacy = [p for p in (root / "assets").rglob("manifest.json")
              if p.parent.name != "_template" and not p.with_name("quality.json").exists()]
    print(f"Legacy packages without new quality evidence: {len(legacy)} (not certified; migration is explicit)")
    for error in errors:
        print(f"[FAIL] {error}", file=sys.stderr)
    return int(bool(errors))


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="action", required=True)
    for action in ("init", "build", "verify-clean", "check", "packet"):
        p = sub.add_parser(action)
        p.add_argument("package", type=Path)
        if action == "check":
            p.add_argument("--require-review", action="store_true")
        if action == "packet":
            p.add_argument("--draft", action="store_true", help="Export honest failed/unreviewed criteria; never implies acceptance")
            p.add_argument("--revision", default="HEAD")
            p.add_argument("--repository", required=True)
            p.add_argument("--output", type=Path, required=True)
    p = sub.add_parser("check-all")
    p.add_argument("--base-ref")
    args = parser.parse_args()
    try:
        if args.action == "check-all":
            return check_all(ROOT, args.base_ref)
        package = args.package.resolve()
        if not package.is_relative_to(ROOT / "assets"):
            raise QualityError("Package must be inside this repository's assets directory")
        if args.action == "init":
            initialize(ROOT, package)
        elif args.action == "build":
            build(ROOT, package)
        elif args.action == "check":
            check(ROOT, package, args.require_review)
        elif args.action == "verify-clean":
            print(json.dumps(verify_clean(ROOT, package), ensure_ascii=False, indent=2))
        else:
            content = packet(ROOT, package, args.revision, args.repository, draft=args.draft)
            args.output.parent.mkdir(parents=True, exist_ok=True)
            args.output.write_text(content, encoding="utf-8")
        print(f"[OK] {args.action}: {package.name} (no automatic art approval)")
        return 0
    except (QualityError, OSError, ValueError, subprocess.CalledProcessError) as exc:
        print(f"[FAIL] {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())

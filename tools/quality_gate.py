#!/usr/bin/env python3
"""Build-bound evidence and browser review packets. No AI verdicts are generated."""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import struct
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import quote

ROOT = Path(__file__).resolve().parents[1]
IMAGE_SUFFIXES = {".png", ".jpg", ".jpeg", ".webp"}
TEXT_SUFFIXES = {".py", ".json", ".md", ".txt", ".svg", ".tres", ".tscn", ".gd",
                 ".yaml", ".yml", ".toml", ".glsl", ".vert", ".frag", ".csv"}


class QualityError(ValueError):
    pass


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
    ids = set()
    for criterion in contract["criteria"]:
        if not isinstance(criterion, dict) or not criterion.get("id") or not str(criterion.get("target", "")).strip():
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
            reported = read_json(metrics)
            if reported.get("triangles") != actual["triangles"]:
                raise QualityError(f"{name}: triangle count disagrees with metrics.json")
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


def build(root: Path, package: Path) -> dict:
    contract = load_contract(root, package)
    before = input_state(root, package, contract)
    evidence_path = package / "review" / "evidence.json"
    evidence_path.unlink(missing_ok=True)  # A failed run must not leave a valid old build receipt.
    for command in contract["commands"]:
        print(f"Running: {command}", flush=True)
        subprocess.run(command, cwd=root, check=True, shell=False)
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


def check(root: Path, package: Path, require_review: bool = False) -> dict:
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
    if not require_review:
        return record
    review = read_json(package / "review" / "visual_review.json")
    if review.get("evidence_digest") != claimed:
        raise QualityError("STALE VISUAL REVIEW: inspect current images and record current digest")
    if not str(review.get("reviewer", "")).strip():
        raise QualityError("Visual review must identify its actual author/model")
    inspected = review.get("inspected_images", [])
    required = {n for c in contract["criteria"] for n in c["evidence"]}
    required.update(r["path"] for r in contract["references"] if Path(r["path"]).suffix.lower() in IMAGE_SUFFIXES)
    if not isinstance(inspected, list) or not required.issubset(set(inspected)):
        raise QualityError("Visual review does not list every required inspected image/reference")
    rows = review.get("criteria", [])
    if not isinstance(rows, list) or not all(isinstance(c, dict) for c in rows) or len(rows) != len(contract["criteria"]):
        raise QualityError("Visual review must cover exactly the declared criteria")
    by_id = {c.get("id"): c for c in rows}
    for criterion in contract["criteria"]:
        result = by_id.get(criterion["id"], {})
        if result.get("status") != "pass" or not str(result.get("observation", "")).strip():
            raise QualityError(f"Visual criterion not passed with observation: {criterion['id']}")
    gameplay = review.get("gameplay", {})
    if gameplay.get("status") not in {"checked", "mockup_only", "not_checked"}:
        raise QualityError("Invalid gameplay review status")
    if gameplay.get("status") in {"checked", "mockup_only"}:
        if not gameplay.get("evidence") or any(n not in artifacts for n in gameplay["evidence"]):
            raise QualityError("Gameplay review requires built evidence")
    if contract.get("require_engine_review") and gameplay.get("status") != "checked":
        raise QualityError("This request requires an engine review; a mockup is insufficient")
    if gameplay.get("status") != "checked" and not str(gameplay.get("notes", "")).strip():
        raise QualityError("Explain the missing engine verification")
    return record


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


def packet(root: Path, package: Path, revision: str, repository: str) -> str:
    if not re.fullmatch(r"[\w.-]+/[\w.-]+", repository):
        raise QualityError("Repository must be owner/name")
    record = check(root, package, require_review=True)
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
    lines = [f"# Asset review: {package.name}", "", f"Commit: `{sha}`", f"Evidence: `{record['digest']}`", "",
        "Open docs/REVIEW.md at this commit. Inspect images before reading the author's visual conclusions.",
        "Green checks confirm recorded evidence, not beauty or engine performance. State inaccessible images explicitly.", "",
        "## Reference and target"]
    for ref in contract["references"]:
        lines += [f"- {ref['status']}: [{ref['path']}]({link(ref['path'])}); origin: {ref['provenance']}; approval: {ref.get('approval', '')}"]
    if not contract["references"]:
        lines += [contract["reference_free_reason"]]
    for c in contract["criteria"]:
        lines += [f"- **{c['id']}**: {c['target']}"]
    lines += ["", "## Images (open original size)"]
    image_names = {n for c in contract["criteria"] for n in c["evidence"]}
    image_names.update(r["path"] for r in contract["references"] if Path(r["path"]).suffix.lower() in IMAGE_SUFFIXES)
    for name in sorted(image_names):
        lines += [f"[{name}]({link(name)})", f"![{Path(name).name}]({link(name)}?raw=true)", ""]
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
    for action in ("init", "build", "check", "packet"):
        p = sub.add_parser(action)
        p.add_argument("package", type=Path)
        if action == "check":
            p.add_argument("--require-review", action="store_true")
        if action == "packet":
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
        else:
            content = packet(ROOT, package, args.revision, args.repository)
            args.output.parent.mkdir(parents=True, exist_ok=True)
            args.output.write_text(content, encoding="utf-8")
        print(f"[OK] {args.action}: {package.name} (no automatic art approval)")
        return 0
    except (QualityError, OSError, ValueError, subprocess.CalledProcessError) as exc:
        print(f"[FAIL] {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())

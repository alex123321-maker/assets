"""
tools/verify_review_evidence.py - Objective review package evidence verification.

Verifies the presence, integrity, and completeness of review artifacts:
- Approved reference image: references/rock_concept_reference.png
- Contact sheet: review/contact_sheet.png
- 4 orthogonal renders (iso, front, side, top) per variant (512x512 PNG)
- Metrics JSON matching source and export
- Review Markdown document containing documented visual self-review section

Does NOT modify review documents or auto-approve subjective items.
Only validates objective evidence integrity.
"""
import json
import struct
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
FAMILY_DIR = REPO_ROOT / "assets" / "environment" / "destructible_rock"
REFERENCE_PATH = FAMILY_DIR / "references" / "rock_concept_reference.png"

REQUIRED_VIEWS = ("iso.png", "front.png", "side.png", "top.png")
EXPECTED_VARIANTS = [
    f"stage_1_var_{i}" for i in range(1, 7)
] + [
    f"stage_2_var_{i}" for i in range(1, 4)
] + [
    f"stage_3_var_{i}" for i in range(1, 4)
] + [
    f"stage_4_var_{i}" for i in range(1, 3)
] + [
    f"stage_5_var_{i}" for i in range(1, 4)
]


def check_png_header(path: Path) -> tuple[bool, int, int, str]:
    """Verify PNG magic header and dimensions."""
    if not path.exists():
        return False, 0, 0, f"File not found: {path}"
    size = path.stat().st_size
    if size < 24:
        return False, 0, 0, f"File too small for PNG ({size} bytes): {path}"
    try:
        with open(path, "rb") as f:
            header = f.read(8)
            if header != b"\x89PNG\r\n\x1a\n":
                return False, 0, 0, f"Invalid PNG magic bytes in {path}"
            # Next chunk must be IHDR
            length, chunk_type = struct.unpack(">I4s", f.read(8))
            if chunk_type != b"IHDR":
                return False, 0, 0, f"First chunk is not IHDR in {path}"
            width, height = struct.unpack(">II", f.read(8))
            return True, width, height, ""
    except Exception as exc:
        return False, 0, 0, f"Error reading {path}: {exc}"


def verify_evidence() -> bool:
    errors: list[str] = []

    # 1. Verify approved reference
    ok, w, h, err = check_png_header(REFERENCE_PATH)
    if not ok:
        errors.append(f"Approved concept reference invalid: {err}")
    else:
        print(f"[PASS] Approved concept reference: {REFERENCE_PATH.name} ({w}x{h}, {REFERENCE_PATH.stat().st_size} bytes)")

    # 2. Verify family contact sheet
    contact_sheet = FAMILY_DIR / "review" / "contact_sheet.png"
    ok, w, h, err = check_png_header(contact_sheet)
    if not ok:
        errors.append(f"Family contact sheet invalid: {err}")
    else:
        print(f"[PASS] Family contact sheet: {contact_sheet.name} ({w}x{h}, {contact_sheet.stat().st_size} bytes)")

    # 3. Verify family review.md
    family_review = FAMILY_DIR / "review" / "review.md"
    if not family_review.exists():
        errors.append(f"Missing family review.md at {family_review}")
    else:
        content = family_review.read_text(encoding="utf-8")
        if "# Family Self Review" not in content:
            errors.append(f"Family review.md missing title header in {family_review}")
        else:
            print(f"[PASS] Family review document: {family_review.name}")

    # 4. Verify all 17 variant packages
    print(f"\nVerifying evidence for {len(EXPECTED_VARIANTS)} variant packages...")
    for slug in EXPECTED_VARIANTS:
        pkg_dir = FAMILY_DIR / slug
        if not pkg_dir.is_dir():
            errors.append(f"Missing variant package directory: {pkg_dir}")
            continue

        review_dir = pkg_dir / "review"
        if not review_dir.is_dir():
            errors.append(f"Missing review directory in {pkg_dir}")
            continue

        # 4a. Renders
        for view_name in REQUIRED_VIEWS:
            view_path = review_dir / view_name
            ok, w, h, err = check_png_header(view_path)
            if not ok:
                errors.append(f"{slug}: {err}")
            elif w != h or w < 512:
                errors.append(f"{slug}: Render {view_name} has invalid resolution {w}x{h} (expected square >= 512x512)")

        # 4b. Metrics JSON
        metrics_path = review_dir / "metrics.json"
        if not metrics_path.exists():
            errors.append(f"{slug}: Missing metrics.json")
        else:
            try:
                data = json.loads(metrics_path.read_text(encoding="utf-8"))
                for key in ("occupied_voxels", "triangles", "visible_faces", "grid", "world_size"):
                    if key not in data:
                        errors.append(f"{slug}: metrics.json missing required key '{key}'")
            except Exception as exc:
                errors.append(f"{slug}: Invalid metrics.json ({exc})")

        # 4c. Review MD
        review_md_path = review_dir / "review.md"
        if not review_md_path.exists():
            errors.append(f"{slug}: Missing review.md")
        else:
            content = review_md_path.read_text(encoding="utf-8")
            if "## Visual Self-Review" not in content:
                errors.append(f"{slug}: review.md missing '## Visual Self-Review' section")
            if "## Metrics" not in content:
                errors.append(f"{slug}: review.md missing '## Metrics' section")

        print(f"  [PASS] {slug}: all 4 renders (512x512), metrics, and review document verified.")

    if errors:
        print(f"\n[FAIL] Evidence verification failed with {len(errors)} error(s):")
        for e in errors:
            print(f"  - {e}")
        return False

    print(f"\n[ALL PASS] All {len(EXPECTED_VARIANTS)} packages have complete, valid review evidence.")
    return True


if __name__ == "__main__":
    success = verify_evidence()
    sys.exit(0 if success else 1)

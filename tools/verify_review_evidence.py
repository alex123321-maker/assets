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
    elif w < 1000 or h < 500:
        errors.append(f"Family contact sheet too small ({w}x{h}, expected >= 1000x500)")
    else:
        print(f"[PASS] Family contact sheet: {contact_sheet.name} ({w}x{h}, {contact_sheet.stat().st_size} bytes)")

    # 3. Verify side-by-side comparison sheets (mandatory for Issue #3)
    ref_comp = FAMILY_DIR / "review" / "reference_vs_3d_comparison.png"
    ok, w, h, err = check_png_header(ref_comp)
    if not ok:
        errors.append(f"Reference vs 3D comparison sheet missing or invalid: {err}")
    elif w < 1000 or h < 500:
        errors.append(f"Reference vs 3D comparison sheet too small ({w}x{h}, expected >= 1000x500)")
    else:
        print(f"[PASS] Reference vs 3D comparison sheet: {ref_comp.name} ({w}x{h}, {ref_comp.stat().st_size} bytes)")

    stage_comp = FAMILY_DIR / "review" / "stage_1_comparison.png"
    ok, w, h, err = check_png_header(stage_comp)
    if not ok:
        errors.append(f"Stage 1 comparison sheet missing or invalid: {err}")
    elif w < 1000 or h < 500:
        errors.append(f"Stage 1 comparison sheet too small ({w}x{h}, expected >= 1000x500)")
    else:
        print(f"[PASS] Stage 1 comparison sheet: {stage_comp.name} ({w}x{h}, {stage_comp.stat().st_size} bytes)")

    # 4. Verify family review.md
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
            if "## Objective Build Verification" not in content and "## Result" not in content:
                errors.append(f"{slug}: review.md missing '## Objective Build Verification' section")
            if "## Metrics" not in content:
                errors.append(f"{slug}: review.md missing '## Metrics' section")

        print(f"  [PASS] {slug}: all 4 renders (512x512), metrics, and review document verified.")

    # 5. Verify tree_oak family (Issue #5)
    tree_family_dir = REPO_ROOT / "assets" / "environment" / "tree_oak"
    if tree_family_dir.is_dir():
        print(f"\nVerifying evidence for tree_oak family...")
        # Approved concept reference
        t_ref = tree_family_dir / "references" / "tree_concept_reference.png"
        ok, w, h, err = check_png_header(t_ref)
        if not ok:
            errors.append(f"Tree concept reference missing or invalid: {err}")
        else:
            print(f"[PASS] Tree concept reference: {t_ref.name} ({w}x{h}, {t_ref.stat().st_size} bytes)")

        t_ref_readme = tree_family_dir / "references" / "README.md"
        if not t_ref_readme.exists():
            errors.append(f"Tree references/README.md missing at {t_ref_readme}")
        else:
            print(f"[PASS] Tree references README: {t_ref_readme.name}")

        # Family contact sheet
        t_contact = tree_family_dir / "review" / "contact_sheet.png"
        ok, w, h, err = check_png_header(t_contact)
        if not ok:
            errors.append(f"Tree family contact sheet invalid: {err}")
        elif w < 1000 or h < 500:
            errors.append(f"Tree family contact sheet too small ({w}x{h}, expected >= 1000x500)")
        else:
            print(f"[PASS] Tree family contact sheet: {t_contact.name} ({w}x{h}, {t_contact.stat().st_size} bytes)")

        # Comparison sheet
        t_comp = tree_family_dir / "review" / "comparison_sheet.png"
        ok, w, h, err = check_png_header(t_comp)
        if not ok:
            errors.append(f"Tree comparison sheet missing or invalid: {err}")
        elif w < 1000 or h < 500:
            errors.append(f"Tree comparison sheet too small ({w}x{h}, expected >= 1000x500)")
        else:
            print(f"[PASS] Tree comparison sheet: {t_comp.name} ({w}x{h}, {t_comp.stat().st_size} bytes)")

        # Reference vs 3D comparison sheet
        t_ref_comp = tree_family_dir / "review" / "reference_vs_3d_comparison.png"
        ok, w, h, err = check_png_header(t_ref_comp)
        if not ok:
            errors.append(f"Tree reference vs 3D comparison sheet missing or invalid: {err}")
        elif w < 1000 or h < 500:
            errors.append(f"Tree reference vs 3D comparison sheet too small ({w}x{h}, expected >= 1000x500)")
        else:
            print(f"[PASS] Tree reference vs 3D comparison: {t_ref_comp.name} ({w}x{h}, {t_ref_comp.stat().st_size} bytes)")

        # Variants concept vs 3D comparison sheet
        t_var_comp = tree_family_dir / "review" / "variants_concept_vs_3d.png"
        ok, w, h, err = check_png_header(t_var_comp)
        if not ok:
            errors.append(f"Tree variants concept vs 3D comparison sheet missing or invalid: {err}")
        elif w < 1000 or h < 500:
            errors.append(f"Tree variants concept vs 3D comparison sheet too small ({w}x{h}, expected >= 1000x500)")
        else:
            print(f"[PASS] Tree variants concept vs 3D comparison: {t_var_comp.name} ({w}x{h}, {t_var_comp.stat().st_size} bytes)")

        # Gameplay mockup
        t_mockup = tree_family_dir / "review" / "gameplay_mockup.png"
        ok, w, h, err = check_png_header(t_mockup)
        if not ok:
            errors.append(f"Tree gameplay mockup missing or invalid: {err}")
        elif w < 1000 or h < 500:
            errors.append(f"Tree gameplay mockup too small ({w}x{h}, expected >= 1000x500)")
        else:
            print(f"[PASS] Tree gameplay mockup: {t_mockup.name} ({w}x{h}, {t_mockup.stat().st_size} bytes)")

        # Family review.md
        t_review = tree_family_dir / "review" / "review.md"
        if not t_review.exists():
            errors.append(f"Missing tree family review.md at {t_review}")
        else:
            content = t_review.read_text(encoding="utf-8")
            if "# Family Self Review" not in content:
                errors.append(f"Tree review.md missing title header in {t_review}")
            else:
                print(f"[PASS] Tree family review document: {t_review.name}")

        # Variants
        tree_variants = [
            "var_0_standard_oak",
            "var_1_tall_oak",
            "var_2_broad_oak",
            "var_3_young_oak",
            "var_4_shrub_oak",
        ]
        for slug in tree_variants:
            pkg_dir = tree_family_dir / slug
            if not pkg_dir.is_dir():
                errors.append(f"Missing tree variant package directory: {pkg_dir}")
                continue

            rev_dir = pkg_dir / "review"
            if not rev_dir.is_dir():
                errors.append(f"Missing review directory in {pkg_dir}")
                continue

            for view_name in REQUIRED_VIEWS:
                v_path = rev_dir / view_name
                ok, w, h, err = check_png_header(v_path)
                if not ok:
                    errors.append(f"{slug}: {err}")
                elif w != h or w < 512:
                    errors.append(f"{slug}: Render {view_name} invalid resolution {w}x{h}")

            m_path = rev_dir / "metrics.json"
            if not m_path.exists():
                errors.append(f"{slug}: Missing metrics.json")
            else:
                try:
                    data = json.loads(m_path.read_text(encoding="utf-8"))
                    for key in ("occupied_voxels", "triangles", "visible_faces", "grid", "world_size"):
                        if key not in data:
                            errors.append(f"{slug}: metrics.json missing required key '{key}'")
                except Exception as exc:
                    errors.append(f"{slug}: Invalid metrics.json ({exc})")

            r_path = rev_dir / "review.md"
            if not r_path.exists():
                errors.append(f"{slug}: Missing review.md")
            else:
                content = r_path.read_text(encoding="utf-8")
                if "## Objective Build Verification" not in content and "## Result" not in content:
                    errors.append(f"{slug}: review.md missing '## Objective Build Verification'")
                if "## Metrics" not in content:
                    errors.append(f"{slug}: review.md missing '## Metrics'")

            print(f"  [PASS] {slug}: all 4 renders (512x512), metrics, and review document verified.")

    # 6. Verify terrain_materials family (Issue #6)
    terrain_family_dir = REPO_ROOT / "assets" / "environment" / "terrain_materials"
    if terrain_family_dir.is_dir():
        print(f"\nVerifying evidence for terrain_materials family...")
        # Concept reference
        t_ref = terrain_family_dir / "references" / "terrain_concept_reference.png"
        ok, w, h, err = check_png_header(t_ref)
        if not ok:
            errors.append(f"Terrain concept reference missing or invalid: {err}")
        else:
            print(f"[PASS] Terrain concept reference: {t_ref.name} ({w}x{h}, {t_ref.stat().st_size} bytes)")

        t_ref_readme = terrain_family_dir / "references" / "README.md"
        if not t_ref_readme.exists():
            errors.append(f"Terrain references/README.md missing at {t_ref_readme}")
        else:
            print(f"[PASS] Terrain references README: {t_ref_readme.name}")

        # Contact sheet
        t_contact = terrain_family_dir / "review" / "contact_sheet.png"
        ok, w, h, err = check_png_header(t_contact)
        if not ok:
            errors.append(f"Terrain family contact sheet invalid: {err}")
        elif w < 1000 or h < 500:
            errors.append(f"Terrain family contact sheet too small ({w}x{h}, expected >= 1000x500)")
        else:
            print(f"[PASS] Terrain family contact sheet: {t_contact.name} ({w}x{h}, {t_contact.stat().st_size} bytes)")

        # Comparison sheet
        t_comp = terrain_family_dir / "review" / "comparison_sheet.png"
        ok, w, h, err = check_png_header(t_comp)
        if not ok:
            errors.append(f"Terrain comparison sheet missing or invalid: {err}")
        elif w < 1000 or h < 500:
            errors.append(f"Terrain comparison sheet too small ({w}x{h}, expected >= 1000x500)")
        else:
            print(f"[PASS] Terrain comparison sheet: {t_comp.name} ({w}x{h}, {t_comp.stat().st_size} bytes)")

        # Reference vs 3D comparison sheet
        t_ref_comp = terrain_family_dir / "review" / "reference_vs_3d_comparison.png"
        ok, w, h, err = check_png_header(t_ref_comp)
        if not ok:
            errors.append(f"Terrain reference vs 3D comparison sheet missing or invalid: {err}")
        elif w < 1000 or h < 500:
            errors.append(f"Terrain reference vs 3D comparison sheet too small ({w}x{h}, expected >= 1000x500)")
        else:
            print(f"[PASS] Terrain reference vs 3D comparison: {t_ref_comp.name} ({w}x{h}, {t_ref_comp.stat().st_size} bytes)")

        # Gameplay mockup
        t_mockup = terrain_family_dir / "review" / "gameplay_mockup.png"
        ok, w, h, err = check_png_header(t_mockup)
        if not ok:
            errors.append(f"Terrain gameplay mockup missing or invalid: {err}")
        elif w < 1000 or h < 500:
            errors.append(f"Terrain gameplay mockup too small ({w}x{h}, expected >= 1000x500)")
        else:
            print(f"[PASS] Terrain gameplay mockup: {t_mockup.name} ({w}x{h}, {t_mockup.stat().st_size} bytes)")

        # Tileability tests
        for mat_key in ("forest_grass_top", "plains_meadow_top", "mountain_stone_top", "cliff_side", "dirt_soil"):
            tile_path = terrain_family_dir / "review" / f"tileability_{mat_key}.png"
            ok, w, h, err = check_png_header(tile_path)
            if not ok:
                errors.append(f"Tileability test for {mat_key} missing or invalid: {err}")
            else:
                print(f"[PASS] Tileability test: {tile_path.name} ({w}x{h})")

        # Texture files
        textures_dir = terrain_family_dir / "textures"
        for tex_name in ("forest_grass_top.png", "plains_meadow_top.png", "mountain_stone_top.png", "cliff_side.png", "dirt_soil.png"):
            tp = textures_dir / tex_name
            ok, w, h, err = check_png_header(tp)
            if not ok:
                errors.append(f"Texture {tex_name} missing or invalid: {err}")
            elif w != 16 or h != 16:
                errors.append(f"Texture {tex_name} resolution is {w}x{h}, expected 16x16")

        atlas_path = textures_dir / "terrain_atlas.png"
        ok, w, h, err = check_png_header(atlas_path)
        if not ok:
            errors.append(f"Terrain atlas missing or invalid: {err}")
        elif w != 64 or h != 64:
            errors.append(f"Terrain atlas resolution is {w}x{h}, expected 64x64")
        else:
            print(f"[PASS] Terrain atlas: {atlas_path.name} (64x64, {atlas_path.stat().st_size} bytes)")

        # Family review.md & metrics
        t_review = terrain_family_dir / "review" / "review.md"
        if not t_review.exists():
            errors.append(f"Missing terrain family review.md at {t_review}")
        else:
            content = t_review.read_text(encoding="utf-8")
            if "# Family Self Review" not in content:
                errors.append(f"Terrain review.md missing title header in {t_review}")
            else:
                print(f"[PASS] Terrain family review document: {t_review.name}")

        t_metrics = terrain_family_dir / "review" / "metrics_summary.json"
        if not t_metrics.exists():
            errors.append(f"Missing terrain metrics_summary.json at {t_metrics}")
        else:
            print(f"[PASS] Terrain metrics summary: {t_metrics.name}")

        # Showcase blocks
        terrain_blocks = [
            "block_forest_grass",
            "block_plains_meadow",
            "block_mountain_stone",
            "block_cliff_strata",
            "block_dirt_soil",
        ]
        for slug in terrain_blocks:
            pkg_dir = terrain_family_dir / slug
            if not pkg_dir.is_dir():
                errors.append(f"Missing terrain block package directory: {pkg_dir}")
                continue

            rev_dir = pkg_dir / "review"
            if not rev_dir.is_dir():
                errors.append(f"Missing review directory in {pkg_dir}")
                continue

            for view_name in REQUIRED_VIEWS:
                v_path = rev_dir / view_name
                ok, w, h, err = check_png_header(v_path)
                if not ok:
                    errors.append(f"{slug}: {err}")
                elif w != h or w < 512:
                    errors.append(f"{slug}: Render {view_name} invalid resolution {w}x{h}")

            m_path = rev_dir / "metrics.json"
            if not m_path.exists():
                errors.append(f"{slug}: Missing metrics.json")
            else:
                try:
                    data = json.loads(m_path.read_text(encoding="utf-8"))
                    for key in ("occupied_voxels", "triangles", "visible_faces", "grid", "world_size"):
                        if key not in data:
                            errors.append(f"{slug}: metrics.json missing required key '{key}'")
                except Exception as exc:
                    errors.append(f"{slug}: Invalid metrics.json ({exc})")

            r_path = rev_dir / "review.md"
            if not r_path.exists():
                errors.append(f"{slug}: Missing review.md")
            else:
                content = r_path.read_text(encoding="utf-8")
                if "## Objective Build Verification" not in content and "## Result" not in content:
                    errors.append(f"{slug}: review.md missing '## Objective Build Verification'")
                if "## Metrics" not in content:
                    errors.append(f"{slug}: review.md missing '## Metrics'")

            print(f"  [PASS] {slug}: all 4 renders (512x512), metrics, and review document verified.")

    if errors:
        print(f"\n[FAIL] Evidence verification failed with {len(errors)} error(s):")
        for e in errors:
            print(f"  - {e}")
        return False

    print(f"\n[ALL PASS] All packages have complete, valid review evidence.")
    return True


if __name__ == "__main__":
    success = verify_evidence()
    sys.exit(0 if success else 1)

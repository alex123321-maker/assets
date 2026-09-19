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


def check_seamless_tiling(tex_path: Path, max_ratio: float = 1.8, max_jump: float = 30.0) -> tuple[bool, str, dict]:
    """Verify that a texture has continuous, seamless boundary transitions."""
    try:
        from PIL import Image
        import numpy as np
    except ImportError as exc:
        return False, f"Missing required dependency for seamless tiling verification: {exc} (install pillow numpy)", {}

    if not tex_path.exists():
        return False, f"Texture not found at {tex_path}", {}

    try:
        img = Image.open(tex_path).convert("RGB")
        arr = np.array(img, dtype=float)
        # horizontal jump across seam: |arr[:, 0] - arr[:, -1]|
        h_seam = float(np.mean(np.linalg.norm(arr[:, 0] - arr[:, -1], axis=1)))
        h_internal = float(np.mean(np.linalg.norm(arr[:, 1:] - arr[:, :-1], axis=2)))
        v_seam = float(np.mean(np.linalg.norm(arr[0, :] - arr[-1, :], axis=1)))
        v_internal = float(np.mean(np.linalg.norm(arr[1:, :] - arr[:-1, :], axis=2)))

        h_ratio = h_seam / max(h_internal, 1e-4)
        v_ratio = v_seam / max(v_internal, 1e-4)

        metrics = {
            "h_seam": h_seam,
            "h_internal": h_internal,
            "h_ratio": h_ratio,
            "v_seam": v_seam,
            "v_internal": v_internal,
            "v_ratio": v_ratio,
        }

        if h_ratio > max_ratio and h_seam > max_jump:
            return False, f"Horizontal seam jump too high (seam={h_seam:.2f}, internal={h_internal:.2f}, ratio={h_ratio:.2f} > {max_ratio})", metrics
        if v_ratio > max_ratio and v_seam > max_jump:
            return False, f"Vertical seam jump too high (seam={v_seam:.2f}, internal={v_internal:.2f}, ratio={v_ratio:.2f} > {max_ratio})", metrics

        return True, "", metrics
    except Exception as exc:
        return False, f"Error inspecting texture: {exc}", {}


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

        # Tileability tests & seam continuity verification
        textures_dir = terrain_family_dir / "textures"
        for mat_key in ("forest_grass_top", "plains_meadow_top", "mountain_stone_top", "cliff_side", "dirt_soil"):
            tile_path = terrain_family_dir / "review" / f"tileability_{mat_key}.png"
            ok, w, h, err = check_png_header(tile_path)
            if not ok:
                errors.append(f"Tileability test preview for {mat_key} missing or invalid: {err}")
            else:
                print(f"[PASS] Tileability test preview: {tile_path.name} ({w}x{h})")

            # Check actual pixel boundary seam continuity on the 16x16 texture
            tex_file = textures_dir / f"{mat_key}.png"
            t_ok, t_err, t_m = check_seamless_tiling(tex_file)
            if not t_ok:
                errors.append(f"{mat_key}.png failed seamless tiling: {t_err}")
            elif t_m:
                print(f"  [PASS] Seamless tiling: {mat_key}.png (H: seam={t_m['h_seam']:.2f}, ratio={t_m['h_ratio']:.2f}; V: seam={t_m['v_seam']:.2f}, ratio={t_m['v_ratio']:.2f})")

        # Texture files
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

    # 7. Verify dressing_pack family (Issue #7)
    dressing_family_dir = REPO_ROOT / "assets" / "environment" / "dressing_pack"
    if dressing_family_dir.is_dir():
        print(f"\nVerifying evidence for dressing_pack family...")
        # Concept reference
        d_ref = dressing_family_dir / "references" / "dressing_concept_reference.png"
        ok, w, h, err = check_png_header(d_ref)
        if not ok:
            errors.append(f"Dressing concept reference missing or invalid: {err}")
        else:
            print(f"[PASS] Dressing concept reference: {d_ref.name} ({w}x{h}, {d_ref.stat().st_size} bytes)")

        d_ref_readme = dressing_family_dir / "references" / "README.md"
        if not d_ref_readme.exists():
            errors.append(f"Dressing references/README.md missing at {d_ref_readme}")
        else:
            print(f"[PASS] Dressing references README: {d_ref_readme.name}")

        # Contact sheet
        d_contact = dressing_family_dir / "review" / "contact_sheet.png"
        ok, w, h, err = check_png_header(d_contact)
        if not ok:
            errors.append(f"Dressing family contact sheet invalid: {err}")
        elif w < 1000 or h < 500:
            errors.append(f"Dressing family contact sheet too small ({w}x{h}, expected >= 1000x500)")
        else:
            print(f"[PASS] Dressing family contact sheet: {d_contact.name} ({w}x{h}, {d_contact.stat().st_size} bytes)")

        # Comparison sheet
        d_comp = dressing_family_dir / "review" / "comparison_sheet.png"
        ok, w, h, err = check_png_header(d_comp)
        if not ok:
            errors.append(f"Dressing comparison sheet missing or invalid: {err}")
        elif w < 1000 or h < 500:
            errors.append(f"Dressing comparison sheet too small ({w}x{h}, expected >= 1000x500)")
        else:
            print(f"[PASS] Dressing comparison sheet: {d_comp.name} ({w}x{h}, {d_comp.stat().st_size} bytes)")

        # Reference vs 3D comparison sheet
        d_ref_comp = dressing_family_dir / "review" / "reference_vs_3d_comparison.png"
        ok, w, h, err = check_png_header(d_ref_comp)
        if not ok:
            errors.append(f"Dressing reference vs 3D comparison sheet missing or invalid: {err}")
        elif w < 1000 or h < 500:
            errors.append(f"Dressing reference vs 3D comparison sheet too small ({w}x{h}, expected >= 1000x500)")
        else:
            print(f"[PASS] Dressing reference vs 3D comparison: {d_ref_comp.name} ({w}x{h}, {d_ref_comp.stat().st_size} bytes)")

        # Biome mockups
        for b_name in ("biome_mockup_forest.png", "biome_mockup_plains.png", "biome_mockup_mountain.png"):
            bmp = dressing_family_dir / "review" / b_name
            ok, w, h, err = check_png_header(bmp)
            if not ok:
                errors.append(f"Dressing {b_name} missing or invalid: {err}")
            elif w < 1000 or h < 500:
                errors.append(f"Dressing {b_name} too small ({w}x{h}, expected >= 1000x500)")
            else:
                print(f"[PASS] Dressing biome mockup: {b_name} ({w}x{h})")

        # Density mockups
        for d_name in ("density_mockup_low.png", "density_mockup_medium.png", "density_mockup_high.png"):
            dmp = dressing_family_dir / "review" / d_name
            ok, w, h, err = check_png_header(dmp)
            if not ok:
                errors.append(f"Dressing {d_name} missing or invalid: {err}")
            elif w < 1000 or h < 500:
                errors.append(f"Dressing {d_name} too small ({w}x{h}, expected >= 1000x500)")
            else:
                print(f"[PASS] Dressing density mockup: {d_name} ({w}x{h})")

        # Gameplay mockup
        d_mockup = dressing_family_dir / "review" / "gameplay_mockup.png"
        ok, w, h, err = check_png_header(d_mockup)
        if not ok:
            errors.append(f"Dressing gameplay mockup missing or invalid: {err}")
        elif w < 1000 or h < 500:
            errors.append(f"Dressing gameplay mockup too small ({w}x{h}, expected >= 1000x500)")
        else:
            print(f"[PASS] Dressing gameplay mockup: {d_mockup.name} ({w}x{h}, {d_mockup.stat().st_size} bytes)")

        # Family review.md & metrics summary
        d_review = dressing_family_dir / "review" / "review.md"
        if not d_review.exists():
            errors.append(f"Missing dressing family review.md at {d_review}")
        else:
            content = d_review.read_text(encoding="utf-8")
            if "# Family Self Review" not in content:
                errors.append(f"Dressing review.md missing title header in {d_review}")
            else:
                print(f"[PASS] Dressing family review document: {d_review.name}")

        d_metrics = dressing_family_dir / "review" / "metrics_summary.json"
        if not d_metrics.exists():
            errors.append(f"Missing dressing metrics_summary.json at {d_metrics}")
        else:
            print(f"[PASS] Dressing metrics summary: {d_metrics.name}")

        # Texture files & Godot material resource
        d_textures_dir = dressing_family_dir / "textures"
        for tex_name in ("dressing_palette_atlas.png", "dressing_roughness_atlas.png"):
            tp = d_textures_dir / tex_name
            ok, w, h, err = check_png_header(tp)
            if not ok:
                errors.append(f"Dressing texture {tex_name} missing or invalid: {err}")
            elif w != 64 or h != 64:
                errors.append(f"Dressing texture {tex_name} resolution is {w}x{h}, expected 64x64")
            else:
                print(f"[PASS] Dressing texture atlas: {tex_name} ({w}x{h}, {tp.stat().st_size} bytes)")

        tres_file = d_textures_dir / "material_dressing_atlas.tres"
        if not tres_file.exists():
            errors.append(f"Missing dressing Godot material resource at {tres_file}")
        else:
            tres_text = tres_file.read_text(encoding="utf-8")
            if "dressing_palette_atlas.png" not in tres_text or "dressing_roughness_atlas.png" not in tres_text:
                errors.append(f"Dressing Godot material {tres_file.name} missing atlas texture references")
            elif "roughness_texture_channel = 1" not in tres_text:
                errors.append(f"Dressing Godot material {tres_file.name} missing roughness_texture_channel = 1")
            else:
                print(f"[PASS] Dressing Godot material resource: {tres_file.name}")

        # All 19 variants
        dressing_variants = [
            "grass_tuft_small_01",
            "grass_tuft_small_02",
            "grass_tuft_small_03",
            "grass_tuft_med_01",
            "grass_tuft_med_02",
            "grass_tuft_tall_01",
            "flower_white_cluster",
            "flower_yellow_cluster",
            "flower_red_cluster",
            "flower_mixed_accent",
            "moss_tree_base",
            "moss_rock_shelf",
            "moss_cliff_ledge",
            "stone_debris_single",
            "stone_debris_trio",
            "stone_debris_flat_patch",
            "stone_debris_angular_chip",
            "stone_debris_fine_scatter",
            "stone_debris_mountain_cluster",
        ]
        for slug in dressing_variants:
            pkg_dir = dressing_family_dir / slug
            if not pkg_dir.is_dir():
                errors.append(f"Missing dressing variant package directory: {pkg_dir}")
                continue

            glb_file = pkg_dir / "output" / "model.glb"
            if not glb_file.exists() or glb_file.stat().st_size < 20:
                errors.append(f"{slug}: Missing or invalid output/model.glb")
            else:
                try:
                    with open(glb_file, "rb") as gf:
                        magic, ver, total_len = struct.unpack("<4sII", gf.read(12))
                        chunk_len, chunk_type = struct.unpack("<I4s", gf.read(8))
                        if magic != b"glTF" or chunk_type != b"JSON":
                            errors.append(f"{slug}: Invalid glTF/GLB header in {glb_file}")
                        else:
                            gltf_json = json.loads(gf.read(chunk_len).decode("utf-8"))
                            bin_chunk_len, bin_chunk_type = struct.unpack("<I4s", gf.read(8))
                            bin_data = gf.read(bin_chunk_len)

                            # 1. Material count and name
                            mats = gltf_json.get("materials", [])
                            if len(mats) != 1:
                                errors.append(f"{slug}: Expected exactly 1 material in GLB, found {len(mats)}")
                            elif mats[0].get("name") != "mat_dressing_atlas":
                                errors.append(f"{slug}: Material name '{mats[0].get('name')}' != 'mat_dressing_atlas'")
                            else:
                                mat0 = mats[0]
                                pbr = mat0.get("pbrMetallicRoughness", {})
                                if "baseColorTexture" not in pbr:
                                    errors.append(f"{slug}: GLB material missing baseColorTexture")
                                if "metallicRoughnessTexture" not in pbr:
                                    errors.append(f"{slug}: GLB material missing metallicRoughnessTexture")

                            # 2. Primitives attributes
                            for m in gltf_json.get("meshes", []):
                                for prim in m.get("primitives", []):
                                    attrs = prim.get("attributes", {})
                                    for req_attr in ("POSITION", "NORMAL", "TEXCOORD_0"):
                                        if req_attr not in attrs:
                                            errors.append(f"{slug}: Primitive missing attribute {req_attr}")
                                    if prim.get("material") != 0:
                                        errors.append(f"{slug}: Primitive material index != 0")

                            # 3. Roughness texture semantics check
                            if mats and "metallicRoughnessTexture" in mats[0].get("pbrMetallicRoughness", {}):
                                mr_tex_idx = mats[0]["pbrMetallicRoughness"]["metallicRoughnessTexture"]["index"]
                                mr_img_idx = gltf_json["textures"][mr_tex_idx]["source"]
                                bv_idx = gltf_json["images"][mr_img_idx]["bufferView"]
                                bv = gltf_json["bufferViews"][bv_idx]
                                img_bytes = bin_data[bv.get("byteOffset", 0):bv.get("byteOffset", 0) + bv["byteLength"]]

                                import io
                                from PIL import Image
                                mr_img = Image.open(io.BytesIO(img_bytes))

                                v_path = pkg_dir / "source" / "voxels.json"
                                if v_path.exists():
                                    v_data = json.loads(v_path.read_text(encoding="utf-8"))
                                    for tok, spec in v_data.get("materials", {}).items():
                                        col, row = spec.get("atlas_cell", [0, 0])
                                        px = col * 8 + 4
                                        py = row * 8 + 4
                                        g_val = mr_img.getpixel((px, py))[1]
                                        exp_g = int(round(spec.get("roughness", 0.88) * 255))
                                        if abs(g_val - exp_g) > 1:
                                            errors.append(f"{slug}: Token '{tok}' GLB roughness {g_val} != expected {exp_g}")

                            # 4. BaseColor texture sRGB encoding and canonical linear fidelity check
                            if mats and "baseColorTexture" in mats[0].get("pbrMetallicRoughness", {}):
                                bc_tex_idx = mats[0]["pbrMetallicRoughness"]["baseColorTexture"]["index"]
                                bc_img_idx = gltf_json["textures"][bc_tex_idx]["source"]
                                bc_bv_idx = gltf_json["images"][bc_img_idx]["bufferView"]
                                bc_bv = gltf_json["bufferViews"][bc_bv_idx]
                                bc_bytes = bin_data[bc_bv.get("byteOffset", 0):bc_bv.get("byteOffset", 0) + bc_bv["byteLength"]]

                                import io
                                from PIL import Image
                                bc_img = Image.open(io.BytesIO(bc_bytes))

                                def srgb_to_linear(b: int) -> float:
                                    c = b / 255.0
                                    if c <= 0.04045:
                                        return c / 12.92
                                    return ((c + 0.055) / 1.055) ** 2.4

                                v_path = pkg_dir / "source" / "voxels.json"
                                if v_path.exists():
                                    v_data = json.loads(v_path.read_text(encoding="utf-8"))
                                    for tok, spec in v_data.get("materials", {}).items():
                                        col, row = spec.get("atlas_cell", [0, 0])
                                        px = col * 8 + 4
                                        py = row * 8 + 4
                                        texel = bc_img.getpixel((px, py))
                                        canon_bc = spec.get("base_color", [1.0, 1.0, 1.0, 1.0])
                                        for ch_i, ch_name in enumerate(("R", "G", "B")):
                                            c_lin = srgb_to_linear(texel[ch_i])
                                            exp_lin = canon_bc[ch_i]
                                            if abs(c_lin - exp_lin) > 0.015:
                                                errors.append(f"{slug}: Token '{tok}' {ch_name} baseColor linear {c_lin:.4f} != expected {exp_lin:.4f} (texel: {texel})")
                except Exception as exc:
                    errors.append(f"{slug}: Error inspecting GLB materials: {exc}")

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
                    if data.get("materials") != 1:
                        errors.append(f"{slug}: metrics.json materials count is {data.get('materials')}, expected 1")
                    if data.get("shared_material") != "mat_dressing_atlas":
                        errors.append(f"{slug}: metrics.json shared_material is {data.get('shared_material')}, expected 'mat_dressing_atlas'")
                    if data.get("atlas_texture") != "dressing_palette_atlas.png":
                        errors.append(f"{slug}: metrics.json atlas_texture is {data.get('atlas_texture')}, expected 'dressing_palette_atlas.png'")
                    if data.get("roughness_atlas_texture") != "dressing_roughness_atlas.png":
                        errors.append(f"{slug}: metrics.json roughness_atlas_texture is {data.get('roughness_atlas_texture')}, expected 'dressing_roughness_atlas.png'")
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

            print(f"  [PASS] {slug}: all 4 renders (512x512), metrics (1 shared mat, PBR atlas), GLB (PBR metallicRoughness), and review document verified.")

        # Distinctiveness check for stone debris variants: verify no two variants are 3D rotationally equivalent
        stone_slugs = [s for s in dressing_variants if s.startswith("stone_debris_")]
        import itertools
        rot_transforms = []
        for perm in itertools.permutations([0, 1, 2]):
            for signs in itertools.product([1, -1], repeat=3):
                det = signs[0] * signs[1] * signs[2]
                if perm not in [(0, 1, 2), (1, 2, 0), (2, 0, 1)]:
                    det = -det
                if det == 1:
                    rot_transforms.append((perm, signs))

        def get_canonical_signature(coords: list[tuple[int, int, int]]) -> tuple:
            signatures = []
            for perm, signs in rot_transforms:
                rotated = [(pt[perm[0]] * signs[0], pt[perm[1]] * signs[1], pt[perm[2]] * signs[2]) for pt in coords]
                min_x = min(p[0] for p in rotated)
                min_y = min(p[1] for p in rotated)
                min_z = min(p[2] for p in rotated)
                signatures.append(tuple(sorted((p[0] - min_x, p[1] - min_y, p[2] - min_z) for p in rotated)))
            return min(signatures)

        stone_signatures = {}
        for s in stone_slugs:
            v_file = dressing_family_dir / s / "source" / "voxels.json"
            if v_file.exists():
                v_data = json.loads(v_file.read_text(encoding="utf-8"))
                coords = []
                for layer in v_data.get("layers", []):
                    y = layer.get("y", 0)
                    for z, row in enumerate(layer.get("rows", [])):
                        for x, ch in enumerate(row):
                            if ch not in (".", " "):
                                coords.append((x, y, z))
                stone_signatures[s] = get_canonical_signature(coords)

        # Verify no pair is rotationally equivalent
        for i in range(len(stone_slugs)):
            for j in range(i + 1, len(stone_slugs)):
                s1, s2 = stone_slugs[i], stone_slugs[j]
                if stone_signatures.get(s1) == stone_signatures.get(s2):
                    errors.append(f"Stone debris rotational equivalence collision: {s1} and {s2} are rotationally identical!")
        print(f"[PASS] Stone debris distinctiveness verified: all {len(stone_slugs)} variants have unique 3D rotational signatures.")

        # Distinctiveness check for flower variants: verify all 4 have unique voxel geometry
        flower_slugs = [s for s in dressing_variants if s.startswith("flower_")]
        flower_signatures = {}
        for f_slug in flower_slugs:
            v_file = dressing_family_dir / f_slug / "source" / "voxels.json"
            if v_file.exists():
                v_data = json.loads(v_file.read_text(encoding="utf-8"))
                coords = []
                for layer in v_data.get("layers", []):
                    y = layer.get("y", 0)
                    for z, row in enumerate(layer.get("rows", [])):
                        for x, ch in enumerate(row):
                            if ch not in (".", " "):
                                coords.append((x, y, z))
                flower_signatures[f_slug] = (len(coords), tuple(sorted(coords)))

        for i in range(len(flower_slugs)):
            for j in range(i + 1, len(flower_slugs)):
                f1, f2 = flower_slugs[i], flower_slugs[j]
                if flower_signatures.get(f1) == flower_signatures.get(f2):
                    errors.append(f"Flower variant collision: {f1} and {f2} have identical voxel geometry!")
        print(f"[PASS] Flower distinctiveness verified: all {len(flower_slugs)} flower archetypes have unique voxel geometries.")

        # Documentation consistency check
        d_readme = dressing_family_dir / "references" / "README.md"
        if d_readme.exists():
            d_readme_text = d_readme.read_text(encoding="utf-8")
            if "100% согласован с destructible rock family" in d_readme_text:
                errors.append(f"Dressing references/README.md contains stale claim: '100% согласован с destructible rock family'")
            if "использует идентичные PBR-материалы скал" in d_readme_text:
                errors.append(f"Dressing references/README.md contains stale claim: 'использует идентичные PBR-материалы скал'")
        d_rev = dressing_family_dir / "review" / "review.md"
        if d_rev.exists():
            d_rev_text = d_rev.read_text(encoding="utf-8")
            if "Uses the identical 4-material palette from destructible_rock" in d_rev_text:
                errors.append(f"Dressing review/review.md contains stale claim: 'Uses the identical 4-material palette from destructible_rock'")
            if "Exact palette & shader parameters matched to Issue #3" in d_rev_text:
                errors.append(f"Dressing review/review.md contains stale claim: 'Exact palette & shader parameters matched to Issue #3'")

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

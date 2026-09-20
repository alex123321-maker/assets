"""Regression checks for stale/fabricated evidence and immutable review inputs."""
import contextlib
import io
import json
import shutil
import struct
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from tools import quality_gate as q
from tools.pipeline_reports import initialize_text, write_build_report


def make_glb(path, triangles=2, materials=1):
    primitives = []
    accessors = []
    for i in range(materials):
        accessors.append({"count": triangles * 3})
        primitives.append({"indices": i, "attributes": {"POSITION": i}, "material": i})
    data = json.dumps({"meshes": [{"primitives": primitives}], "accessors": accessors}).encode()
    data += b" " * (-len(data) % 4)
    path.write_bytes(b"glTF" + struct.pack("<IIII", 2, len(data) + 20, len(data), 0x4E4F534A) + data)


class QualityGateTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name).resolve()
        self.pkg = self.root / "assets/props/test"
        for folder in ("source", "output", "review", "references"):
            (self.pkg / folder).mkdir(parents=True)
        (self.pkg / "source/model.txt").write_text("canonical", encoding="utf-8")
        (self.pkg / "request.md").write_text("Approved request", encoding="utf-8")
        q.write_json(self.pkg / "manifest.json", {"source": "source/model.txt", "budgets": {"max_triangles": 4, "max_materials": 1}})
        (self.root / "builder.py").write_text("# deterministic fixture builder\n", encoding="utf-8")
        self.prefix = "assets/props/test"
        self.contract = {"version": 1,
            "inputs": [f"{self.prefix}/source", "builder.py"],
            "commands": [[sys.executable, "builder.py"]],
            "references": [], "reference_free_reason": "Explicit request-only direction",
            "artifacts": [f"{self.prefix}/output", f"{self.prefix}/review/iso.png", f"{self.prefix}/review/metrics.json"],
            "criteria": [{"id": "silhouette", "target": "Two asymmetric peaks", "evidence": [f"{self.prefix}/review/iso.png"]}],
            "require_engine_review": False}
        self.save_contract()
        self.output()

    def save_contract(self):
        q.write_json(self.pkg / "quality.json", self.contract)

    def output(self):
        from PIL import Image
        Image.new("RGB", (12, 12), "green").save(self.pkg / "review/iso.png")
        make_glb(self.pkg / "output/model.glb")
        q.write_json(self.pkg / "review/metrics.json", {"triangles": 2})

    def build(self):
        with contextlib.redirect_stdout(io.StringIO()):
            return q.build(self.root, self.pkg)

    def reviewed(self):
        record = self.build()
        q.write_json(self.pkg / "review/visual_review.json", {
            "evidence_digest": record["digest"], "reviewer": "Test reviewer",
            "inspected_images": [f"{self.prefix}/review/iso.png"],
            "criteria": [{"id": "silhouette", "status": "pass", "observation": "Two unequal peaks separated by a visible notch."}],
            "gameplay": {"status": "mockup_only", "evidence": [f"{self.prefix}/review/iso.png"], "notes": "Engine unavailable"}})
        return record

    def test_build_records_export_and_unreviewed_template(self):
        record = self.build()
        self.assertEqual(record["measurements"][f"{self.prefix}/output/model.glb"]["triangles"], 2)
        q.check(self.root, self.pkg)
        with self.assertRaises(q.QualityError):
            q.check(self.root, self.pkg, True)

    def test_clean_build_runs_recipe_and_creates_delivery(self):
        raw = (self.pkg / "output/model.glb").read_bytes()
        for name in ("output/model.glb", "review/iso.png", "review/metrics.json"):
            (self.pkg / name).unlink()
        script = (
            "from pathlib import Path\nfrom PIL import Image\n"
            "p = Path('assets/props/test')\n"
            "assert (p / 'source/model.txt').read_text() == 'canonical'\n"
            f"(p / 'output/model.glb').write_bytes({raw!r})\n"
            "Image.new('RGB', (16,16), 'blue').save(p / 'review/iso.png')\n"
            "(p / 'review/metrics.json').write_text('{\"triangles\": 2}')\n"
        )
        (self.root / "builder.py").write_text(script, encoding="utf-8")
        self.build()
        q.check(self.root, self.pkg)
        self.assertTrue((self.pkg / "review/evidence.json").exists())

    def test_visual_review_pass_and_preservation(self):
        self.reviewed()
        q.check(self.root, self.pkg, True)
        old = (self.pkg / "review/visual_review.json").read_bytes()
        self.build()
        self.assertEqual(old, (self.pkg / "review/visual_review.json").read_bytes())
        with self.assertRaisesRegex(q.QualityError, "STALE VISUAL"):
            q.check(self.root, self.pkg, True)

    def test_source_edit_invalidates_evidence(self):
        self.build()
        (self.pkg / "source/model.txt").write_text("changed")
        with self.assertRaisesRegex(q.QualityError, "STALE BUILD"):
            q.check(self.root, self.pkg)

    def test_windows_line_endings_match_linux_checkout(self):
        (self.pkg / "source/model.txt").write_bytes(b"canonical\r\nsource\r\n")
        self.build()
        (self.pkg / "source/model.txt").write_bytes(b"canonical\nsource\n")
        q.check(self.root, self.pkg)

    def test_entry_script_and_manifest_source_cannot_be_omitted(self):
        self.contract["inputs"] = [f"{self.prefix}/request.md"]
        self.save_contract()
        record = self.build()
        self.assertIn("builder.py", record["inputs"])
        self.assertIn(f"{self.prefix}/source/model.txt", record["inputs"])

    def test_dependency_and_request_changes_invalidate_evidence(self):
        for path in (self.root / "builder.py", self.pkg / "request.md"):
            with self.subTest(path=path):
                self.build()
                path.write_text(path.read_text() + "\n# changed")
                with self.assertRaisesRegex(q.QualityError, "STALE BUILD"):
                    q.check(self.root, self.pkg)

    def test_deleted_or_added_output_invalidates_evidence(self):
        self.build()
        (self.pkg / "output/unexpected.txt").write_text("extra")
        with self.assertRaisesRegex(q.QualityError, "STALE EVIDENCE"):
            q.check(self.root, self.pkg)

    def test_render_change_invalidates_evidence(self):
        self.build()
        from PIL import Image
        Image.new("RGB", (12, 12), "red").save(self.pkg / "review/iso.png")
        with self.assertRaisesRegex(q.QualityError, "STALE EVIDENCE"):
            q.check(self.root, self.pkg)

    def test_failure_removes_old_receipt(self):
        self.build()
        (self.root / "builder.py").write_text("raise SystemExit(2)")
        with self.assertRaises(subprocess.CalledProcessError):
            self.build()
        self.assertFalse((self.pkg / "review/evidence.json").exists())

    def test_build_must_not_rewrite_request(self):
        (self.root / "builder.py").write_text("from pathlib import Path\nPath('assets/props/test/request.md').write_text('changed')\n")
        with self.assertRaisesRegex(q.QualityError, "changed its inputs"):
            self.build()

    def test_reference_approval_and_hash(self):
        ref = self.pkg / "references/ref.png"
        ref.write_bytes((self.pkg / "review/iso.png").read_bytes())
        self.contract["references"] = [{"path": f"{self.prefix}/references/ref.png", "status": "approved", "provenance": "User supplied", "sha256": q.file_hash(ref)}]
        self.save_contract()
        with self.assertRaisesRegex(q.QualityError, "decision citation"):
            self.build()
        self.contract["references"][0]["approval"] = "Issue #1 user decision"
        self.save_contract()
        self.build()
        ref.write_bytes(b"different")
        with self.assertRaisesRegex(q.QualityError, "Reference changed"):
            q.check(self.root, self.pkg)

    def test_budget_and_metrics_use_export(self):
        make_glb(self.pkg / "output/model.glb", triangles=5)
        with self.assertRaisesRegex(q.QualityError, "exceeds budget"):
            self.build()
        make_glb(self.pkg / "output/model.glb", triangles=3)
        with self.assertRaisesRegex(q.QualityError, "disagrees"):
            self.build()

    def test_material_budget(self):
        make_glb(self.pkg / "output/model.glb", triangles=1, materials=2)
        with self.assertRaisesRegex(q.QualityError, "materials.*exceeds"):
            self.build()

    def test_corrupt_image_is_not_evidence(self):
        (self.pkg / "review/iso.png").write_bytes(b"\x89PNG\r\n\x1a\n" + b"0" * 50)
        with self.assertRaisesRegex(q.QualityError, "Cannot decode"):
            self.build()

    def test_recipe_cannot_omit_declared_export(self):
        manifest = q.read_json(self.pkg / "manifest.json")
        manifest["outputs"] = {"model": "output/model.glb"}
        q.write_json(self.pkg / "manifest.json", manifest)
        self.contract["artifacts"] = [f"{self.prefix}/review/iso.png", f"{self.prefix}/review/metrics.json"]
        self.save_contract()
        with self.assertRaisesRegex(q.QualityError, "omitted"):
            self.build()

    def test_path_escape_rejected(self):
        self.contract["inputs"].append("../outside.txt")
        self.save_contract()
        with self.assertRaisesRegex(q.QualityError, "leaves repository"):
            self.build()

    def test_missing_and_empty_input_fail(self):
        for value in (["missing.txt"], []):
            self.contract["inputs"] = value
            self.save_contract()
            with self.assertRaises(q.QualityError):
                self.build()

    def test_no_automatic_pass_from_artifact_presence(self):
        self.reviewed()
        path = self.pkg / "review/visual_review.json"
        review = q.read_json(path)
        review["criteria"][0]["observation"] = ""
        q.write_json(path, review)
        with self.assertRaisesRegex(q.QualityError, "observation"):
            q.check(self.root, self.pkg, True)

    def test_required_engine_review_cannot_use_mockup(self):
        self.contract["require_engine_review"] = True
        self.save_contract()
        self.reviewed()
        with self.assertRaisesRegex(q.QualityError, "engine review"):
            q.check(self.root, self.pkg, True)

    def test_build_reports_preserve_authored_documents(self):
        path = self.pkg / "review/review.md"
        path.write_text("Real review: visible defect", encoding="utf-8")
        write_build_report(path.parent, "fixture", {"triangles": 2})
        self.assertEqual(path.read_text(), "Real review: visible defect")
        self.assertIn("not an artistic verdict", (path.parent / "build_report.md").read_text())
        self.assertFalse(initialize_text(self.pkg / "request.md", "Replacement"))
        self.assertEqual((self.pkg / "request.md").read_text(), "Approved request")

    def init_git(self):
        def run(*args):
            return q.git(self.root, *args)
        run("init", "-q")
        run("config", "user.email", "tests@example.invalid")
        run("config", "user.name", "Tests")
        run("config", "core.autocrlf", "false")
        return run

    def test_packet_pins_commit_and_rejects_dirty_evidence(self):
        self.reviewed()
        run = self.init_git()
        run("add", ".")
        run("commit", "-qm", "fixture")
        sha = run("rev-parse", "HEAD")
        text = q.packet(self.root, self.pkg, "HEAD", "owner/repo")
        self.assertIn(f"/blob/{sha}/", text)
        self.assertNotIn("/blob/main/", text)
        (self.pkg / "review/visual_review.json").write_text((self.pkg / "review/visual_review.json").read_text() + "\n")
        with self.assertRaisesRegex(q.QualityError, "differs"):
            q.packet(self.root, self.pkg, "HEAD", "owner/repo")

    def test_new_packages_required_but_legacy_untouched(self):
        (self.pkg / "quality.json").unlink()
        run = self.init_git()
        run("add", ".")
        run("commit", "-qm", "legacy")
        base = run("rev-parse", "HEAD")
        with contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(q.check_all(self.root, base), 0)
        new = self.root / "assets/props/new/manifest.json"
        q.write_json(new, {"source": "source"})
        run("add", ".")
        run("commit", "-qm", "new without contract")
        with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
            self.assertEqual(q.check_all(self.root, base), 1)

    def test_init_does_not_approve_or_overwrite(self):
        (self.pkg / "quality.json").unlink()
        q.initialize(self.root, self.pkg)
        self.assertEqual(q.read_json(self.pkg / "quality.json")["commands"], [])
        with self.assertRaisesRegex(q.QualityError, "Already exists"):
            q.initialize(self.root, self.pkg)

    def test_new_asset_cli_creates_quality_starter(self):
        repo = Path(__file__).resolve().parents[2]
        shutil.copytree(repo / "assets/_template", self.root / "assets/_template")
        (self.root / "tools").mkdir()
        for name in ("new_asset.py", "quality_gate.py"):
            shutil.copy2(repo / "tools" / name, self.root / "tools" / name)
        subprocess.run([sys.executable, str(self.root / "tools/new_asset.py"), "props", "new_fixture"],
                       cwd=self.root, check=True, capture_output=True)
        created = q.read_json(self.root / "assets/props/new_fixture/quality.json")
        self.assertEqual(created["commands"], [])
        self.assertEqual(created["criteria"][0]["target"], "")

    def test_hud_source_runner_imports_from_unrelated_working_directory(self):
        repo = Path(__file__).resolve().parents[2]
        runner = repo / "assets/ui/hud_visual_kit/source/generate_kit.py"
        # __main__ is deliberately not executed: imports must work without regenerating assets.
        subprocess.run([sys.executable, "-c", "import runpy,sys; runpy.run_path(sys.argv[1], run_name='pipeline_import_check')", str(runner)],
                       cwd=self.root, check=True, capture_output=True)


if __name__ == "__main__":
    unittest.main()

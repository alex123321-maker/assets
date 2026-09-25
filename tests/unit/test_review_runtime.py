"""Regression coverage for a watcher deployed outside the asset checkout."""
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from tools.review_loop.agent_resumer import AgentResumer, resolve_agentapi_command, AgentResumerError
from tools.review_loop.config import SOURCE_ROOT, VISUAL_MEDIA_POLICY
from tools.review_loop.install import install_antigravity_sidecar, ANTIGRAVITY_SIDECAR_ID


class TestIsolatedRuntime(unittest.TestCase):
    def test_state_and_git_target_remain_separate_from_code_and_policy(self):
        with tempfile.TemporaryDirectory() as directory:
            result = subprocess.run(
                [sys.executable, "-c", "import json; from tools.review_loop.config import *; "
                 "print(json.dumps([str(REPO_ROOT),str(DEFAULT_STATE_FILE),str(VISUAL_MEDIA_POLICY)]))"],
                cwd=SOURCE_ROOT, env={**os.environ, "ASSET_REVIEW_REPO_ROOT": directory},
                capture_output=True, text=True, check=True,
            )
            repo, state, policy = map(Path, json.loads(result.stdout))
            self.assertEqual(repo, Path(directory).resolve())
            self.assertEqual(state, repo / ".review_loop" / "state.json")
            self.assertEqual(policy, VISUAL_MEDIA_POLICY)

    def test_installed_sidecar_runs_source_but_targets_asset_repository(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            target = root / "assets"
            with patch("tools.review_loop.install.REPO_ROOT", target), patch(
                "tools.review_loop.install.SIDECAR_MARKER_FILE", root / "marker"
            ):
                self.assertTrue(install_antigravity_sidecar(root))
            manifest = json.loads((root / "sidecars" / ANTIGRAVITY_SIDECAR_ID / "sidecar.json").read_text())
            self.assertEqual(manifest["args"], [str(SOURCE_ROOT / "tools/review_loop/watcher.py")])
            self.assertEqual(manifest["env"]["ASSET_REVIEW_REPO_ROOT"], str(target))

    def test_large_feedback_keeps_tail_and_visual_exception_in_both_prompts(self):
        with tempfile.TemporaryDirectory() as directory:
            resumer = AgentResumer(cwd=Path(directory))
            full = resumer.build_prompt(16, [{"id": "x", "body": "ю" * 30000 + "TAIL-FINDING"}])
            dispatch = resumer.prepare_dispatch_prompt(16, full)
            payloads = list((Path(directory) / ".review_loop/feedback").glob("*.txt"))
            self.assertEqual(len(payloads), 1)
            self.assertEqual(payloads[0].read_text(encoding="utf-8"), full)
            self.assertIn("TAIL-FINDING", full)
            self.assertIn(str(VISUAL_MEDIA_POLICY), full)
            self.assertIn("gh pr comment --attach", full)
            self.assertIn("still publish any missing packet", full)
            self.assertNotIn("finish silently in chat", full)
            self.assertIn("<!-- agent:review-loop -->", full)
            self.assertIn("Publish the visual attachment packet", dispatch)
            self.assertNotIn("or post PR comments", dispatch)
            self.assertEqual(dispatch, resumer.prepare_dispatch_prompt(16, full))

    def test_official_batch_shim_is_unwrapped_without_shell(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            executable = root / "language_server.exe"
            executable.touch()
            shim = root / "agentapi.cmd"
            shim.write_text(f'@echo off\n"{executable}" agentapi %*\n')
            self.assertEqual(resolve_agentapi_command([str(shim)]), [str(executable), "agentapi"])
            shim.write_text('@echo off\necho %*\n')
            with self.assertRaises(AgentResumerError):
                resolve_agentapi_command([str(shim)])


if __name__ == "__main__":
    unittest.main()

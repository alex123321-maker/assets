"""Regression coverage for PR #16: Windows argv limits and duplicate feedback."""
import hashlib
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

from tools.review_loop.agent_resumer import (
    AgentResumer, AgentResumerError, BACKEND_AGENTAPI,
    MAX_INLINE_PROMPT_CHARS, resolve_agentapi_command,
)
from tools.review_loop.github_client import GitHubClient
from tools.review_loop.state_manager import StateManager
from tools.review_loop.watcher import ReviewWatcher


class TestReviewTransport(unittest.TestCase):
    def test_official_batch_shim_is_unwrapped_without_shell(self):
        with tempfile.TemporaryDirectory() as tmp:
            folder = Path(tmp) / "directory with spaces"
            folder.mkdir()
            exe = folder / "language_server.exe"
            exe.touch()
            shim = folder / "agentapi.bat"
            shim.write_text(f'@echo off\n"{exe}" agentapi %*\n', encoding="utf-8")
            self.assertEqual(resolve_agentapi_command([str(shim)]), [str(exe), "agentapi"])

    def test_unknown_batch_script_is_never_executed(self):
        with tempfile.TemporaryDirectory() as tmp:
            shim = Path(tmp) / "agentapi.cmd"
            shim.write_text('@echo off\necho %*\n', encoding="utf-8")
            with self.assertRaises(AgentResumerError):
                resolve_agentapi_command([str(shim)])
            with patch("subprocess.run") as run:
                ok, error, _ = AgentResumer(agentapi_cmd=[str(shim)]).resume_conversation("chat", 16)
                self.assertFalse(ok)
                self.assertIn("Unsupported agentapi batch shim", error)
                run.assert_not_called()

    def test_long_feedback_is_saved_whole_and_retry_uses_same_path(self):
        with tempfile.TemporaryDirectory() as tmp:
            resumer = AgentResumer(cwd=Path(tmp))
            body = ('Исправить "нормали" & <грани> %PATH% ! ^\n' * 1800) + "FINAL-FINDING"
            prompt = resumer.build_prompt(16, [{"id": "review16", "body": body}])
            self.assertIn(body, prompt)
            self.assertNotIn("[truncated by watcher]", prompt)
            short = resumer.prepare_dispatch_prompt(16, prompt)
            self.assertLess(len(short), MAX_INLINE_PROMPT_CHARS)
            files = list((Path(tmp) / ".review_loop" / "feedback").glob("*.txt"))
            self.assertEqual(len(files), 1)
            self.assertEqual(files[0].read_bytes(), prompt.encode("utf-8"))
            self.assertIn(hashlib.sha256(files[0].read_bytes()).hexdigest(), short)
            self.assertEqual(resumer.prepare_dispatch_prompt(16, prompt), short)
            changed = resumer.prepare_dispatch_prompt(16, prompt + "new finding")
            self.assertNotEqual(changed, short)
            self.assertEqual(files[0].read_bytes(), prompt.encode("utf-8"))

    def test_spool_failure_does_not_send_partial_task(self):
        resumer = AgentResumer(agentapi_cmd=["agentapi"])
        with patch.object(resumer, "prepare_dispatch_prompt", side_effect=OSError("disk full")), patch("subprocess.run") as run:
            ok, error, _ = resumer.resume_conversation("chat", 16)
            self.assertFalse(ok)
            self.assertIn("disk full", error)
            run.assert_not_called()

    def test_legacy_duplicate_text_keeps_all_event_ids_and_locations(self):
        events = [
            {"id": "42", "type": "INLINE_COMMENT", "author": "owner", "body": "Fix normals", "path": "mesh.py", "line": 4},
            {"id": "node42", "type": "THREAD_COMMENT", "author": "owner", "body": "Fix normals"},
            {"id": "43", "type": "INLINE_COMMENT", "author": "owner", "body": "Fix normals", "path": "other.py", "line": 9},
        ]
        prompt = AgentResumer().build_prompt(16, events)
        self.assertEqual(prompt.count("Fix normals"), 1)
        for identifier in ("42", "node42", "43"):
            self.assertIn(f"id={identifier} ", prompt)
        self.assertIn("path=other.py line=9", prompt)
        self.assertEqual(events[1]["body"], "Fix normals")

    def test_real_subprocess_preserves_unicode_and_shell_characters(self):
        # This harmless receiver exercises actual Windows argv, not a mocked CLI.
        receiver = "import sys,json; print(json.dumps(sys.argv[1:],ensure_ascii=True))"
        with tempfile.TemporaryDirectory() as tmp:
            resumer = AgentResumer(
                agentapi_cmd=[sys.executable, "-c", receiver],
                backend_type=BACKEND_AGENTAPI, cwd=Path(tmp),
            )
            body = 'Нормали "наружу" & echo NO > file %PATH% ! ^'
            ok, output, _ = resumer.resume_conversation("chat", 16, feedback_events=[{"id": "r", "body": body}], max_retries=1)
            self.assertTrue(ok, output)
            args = json.loads(output)
            self.assertEqual(args[:2], ["send-message", "chat"])
            self.assertIn(body, args[2])
            self.assertFalse((Path(tmp) / "file").exists())
            ok, output, _ = resumer.resume_conversation("chat", 16, feedback_events=[{"id": "r", "body": body * 2000}], max_retries=1)
            self.assertTrue(ok, output)
            args = json.loads(output)
            self.assertLess(len(subprocess.list2cmdline(args)), 8000)
            self.assertIn("Task file:", args[2])


class TestReviewIdentity(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.state = StateManager(Path(self.temp.name) / "state.json")
        self.state.register_pr(16, "chat", "branch")
        self.state.add_to_allowlist("owner")
        self.github = MagicMock(spec=GitHubClient)
        self.github.get_pr_reviews.return_value = []
        self.github.get_pr_comments.return_value = []
        self.github.get_pr_inline_comments.return_value = [
            {"id": 42, "node_id": "NODE42", "user": {"login": "owner"}, "body": "Fix normals", "path": "mesh.py", "line": 4},
        ]
        self.github.get_pr_review_threads.return_value = [
            {"id": "THREAD", "isResolved": False, "comments": {"nodes": [
                {"id": "NODE42", "databaseId": 42, "author": {"login": "owner"}, "body": "Fix normals", "path": "mesh.py", "line": 4},
            ]}},
        ]
        self.watcher = ReviewWatcher(github_client=self.github, state_manager=self.state, agent_resumer=MagicMock())

    def test_rest_and_graphql_comment_dispatched_once_across_cycles(self):
        events = self.watcher.check_pr_events(16, {})
        self.assertEqual([e["id"] for e in events], ["42"])
        self.state.set_in_flight_events(16, events)
        self.assertEqual(self.watcher.check_pr_events(16, {}), [])
        self.state.finalize_in_flight_events(16)
        self.assertEqual(self.watcher.check_pr_events(16, {}), [])

    def test_old_graphql_processed_or_pending_ids_are_not_replayed(self):
        self.state.queue_pending_event(16, {"id": "NODE42", "body": "Fix normals"})
        self.assertEqual(self.watcher.check_pr_events(16, {}), [])
        self.state.pop_pending_events(16)
        self.state.mark_event_processed(16, "NODE42")
        self.assertEqual(self.watcher.check_pr_events(16, {}), [])

    def test_graphql_fallback_and_later_rest_use_same_identity(self):
        self.github.get_pr_inline_comments.return_value = []
        events = self.watcher.check_pr_events(16, {})
        self.assertEqual(events[0]["id"], "42")
        self.assertEqual(events[0]["path"], "mesh.py")
        self.state.set_in_flight_events(16, events)
        self.github.get_pr_inline_comments.return_value = [{"id": 42, "node_id": "NODE42", "user": {"login": "owner"}, "body": "Fix normals"}]
        self.assertEqual(self.watcher.check_pr_events(16, {}), [])

    def test_equal_text_on_different_comments_is_not_dropped(self):
        self.github.get_pr_inline_comments.return_value.append({"id": 43, "node_id": "NODE43", "user": {"login": "owner"}, "body": "Fix normals"})
        self.assertEqual([e["id"] for e in self.watcher.check_pr_events(16, {})], ["42", "43"])

    def test_graphql_query_requests_database_identity(self):
        client = GitHubClient()
        with patch.object(client, "get_repo_owner_and_name", return_value=("owner", "repo")), patch.object(client, "run_gh", return_value=(0, '{}', '')) as run:
            client.get_pr_review_threads(16)
        self.assertIn("databaseId", " ".join(run.call_args.args[0]))


if __name__ == "__main__":
    unittest.main()

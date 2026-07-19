from __future__ import annotations

import os
from pathlib import Path
import subprocess
import tempfile
import unittest

from tests import support as _support  # installs src/ on sys.path

from tempo.errors import CheckerFailure
from tempo.subject import repository_ref, validate_repository_ref
from tempo.util import Workspace, sha256_json


class SubjectBindingTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name) / "subject"
        self.root.mkdir()
        self._git(self.root, "init")
        self._git(self.root, "config", "user.name", "TEMPO Test")
        self._git(self.root, "config", "user.email", "tempo@example.invalid")
        (self.root / "tracked.txt").write_text("baseline\n", encoding="utf-8")
        self._git(self.root, "add", "tracked.txt")
        self._git(self.root, "commit", "-m", "baseline")
        self._git(
            self.root,
            "remote",
            "add",
            "origin",
            "https://token@example.com/vemodalen-x/TEMPO.git?ignored=1",
        )
        self.workspace = Workspace.from_path(self.root)

    def tearDown(self) -> None:
        self.temporary.cleanup()

    def _git(self, root: Path, *args: str) -> str:
        completed = subprocess.run(
            ["git", "-C", str(root), *args],
            check=True,
            capture_output=True,
            text=True,
            encoding="utf-8",
        )
        return completed.stdout.strip()

    def test_v2_ref_accepts_only_the_captured_git_subject(self) -> None:
        captured = repository_ref(self.workspace)

        self.assertTrue(captured.startswith("repository:v2:git:"))
        self.assertNotIn("token", captured)
        self.assertTrue(validate_repository_ref(self.workspace, captured))

    def test_equivalent_remote_protocol_does_not_change_origin_identity(self) -> None:
        captured = repository_ref(self.workspace)

        self._git(
            self.root,
            "remote",
            "set-url",
            "origin",
            "git@example.com:vemodalen-x/TEMPO.git",
        )

        self.assertEqual(repository_ref(self.workspace), captured)

    def test_different_origin_commit_and_revision_are_rejected(self) -> None:
        captured = repository_ref(self.workspace)

        self._git(self.root, "remote", "set-url", "origin", "https://example.com/other/repo.git")
        self.assertFalse(validate_repository_ref(self.workspace, captured))
        self._git(
            self.root,
            "remote",
            "set-url",
            "origin",
            "git@example.com:vemodalen-x/TEMPO.git",
        )

        (self.root / "tracked.txt").write_text("next commit\n", encoding="utf-8")
        self._git(self.root, "add", "tracked.txt")
        self._git(self.root, "commit", "-m", "next")
        self.assertFalse(validate_repository_ref(self.workspace, captured))

        self._git(self.root, "reset", "--hard", "HEAD~1")
        self._git(self.root, "checkout", "-b", "alternate")
        self.assertFalse(validate_repository_ref(self.workspace, captured))

    def test_file_url_host_is_part_of_origin_identity(self) -> None:
        self._git(
            self.root,
            "remote",
            "set-url",
            "origin",
            "file://server-a/share/TEMPO.git",
        )
        captured = repository_ref(self.workspace)

        self._git(
            self.root,
            "remote",
            "set-url",
            "origin",
            "file://server-b/share/TEMPO.git",
        )

        self.assertFalse(validate_repository_ref(self.workspace, captured))

    def test_same_origin_and_commit_in_another_worktree_is_rejected(self) -> None:
        captured = repository_ref(self.workspace)
        clone = Path(self.temporary.name) / "clone"
        subprocess.run(
            ["git", "clone", "--no-hardlinks", str(self.root), str(clone)],
            check=True,
            capture_output=True,
            text=True,
            encoding="utf-8",
        )
        self._git(
            clone,
            "remote",
            "set-url",
            "origin",
            "git@example.com:vemodalen-x/TEMPO.git",
        )

        self.assertFalse(validate_repository_ref(Workspace.from_path(clone), captured))

    def test_non_git_subject_is_allowed_only_for_explicit_fixture(self) -> None:
        fixture_root = Path(self.temporary.name) / "fixture"
        fixture_root.mkdir()
        fixture_workspace = Workspace.from_path(fixture_root)

        with self.assertRaises(CheckerFailure) as caught:
            repository_ref(fixture_workspace)

        self.assertEqual(caught.exception.reason_code, "GIT_SUBJECT_REQUIRED")
        fixture_ref = repository_ref(fixture_workspace, allow_fixture=True)
        self.assertTrue(fixture_ref.startswith("repository:v2:fixture:"))
        self.assertTrue(validate_repository_ref(fixture_workspace, fixture_ref))

    def test_legacy_path_hash_and_workspace_name_cannot_authorize(self) -> None:
        root = os.path.normcase(
            os.path.normpath(str(self.workspace.root.resolve(strict=True)))
        )
        legacy_path_hash = "repository:" + sha256_json({"workspace_root": root})[7:]

        self.assertFalse(validate_repository_ref(self.workspace, legacy_path_hash))
        self.assertFalse(validate_repository_ref(self.workspace, self.workspace.root.name))


if __name__ == "__main__":
    unittest.main()

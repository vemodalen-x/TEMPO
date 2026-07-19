from __future__ import annotations

from unittest.mock import patch

from tests import support as _support  # installs src/ on sys.path
from tests.support import SESSION, WorkspaceCase, read_json, write_json

from tempo.errors import PolicyBlock
from tempo.guards import evaluate_event
from tempo.ledger import Ledger
from tempo.subject import repository_ref
from tempo.warrant import start, status, validate_build_lease


class StabilizationContractTests(WorkspaceCase):
    def setUp(self) -> None:
        super().setUp()
        self.install_valid_case()
        self.authorize_demo()

    def start_build(self) -> dict:
        return start(
            self.workspace,
            task_id="T-TEST-001",
            path="src/tempo/new.py",
            lane="core",
            action="implementation_write",
            actor="agent:builder",
            session=SESSION,
        )

    def assert_policy_code(self, expected: str, callable_, *args, **kwargs) -> PolicyBlock:
        with self.assertRaises(PolicyBlock) as caught:
            callable_(*args, **kwargs)
        self.assertEqual(caught.exception.reason_code, expected)
        return caught.exception

    def test_new_warrant_is_bound_to_canonical_repository_workspace(self) -> None:
        warrant = read_json(self.root / "plan/authorization-warrant.json")
        self.assertEqual(
            warrant["repository_ref"],
            repository_ref(self.workspace, allow_fixture=True),
        )
        self.assertTrue(warrant["repository_ref"].startswith("repository:v2:fixture:"))

    def test_missing_active_lease_keeps_authorization_but_disables_build(self) -> None:
        self.start_build()
        (self.root / ".tempo/run/active.json").unlink()

        current = status(self.workspace)
        self.assertTrue(current["authorization_valid"])
        self.assertFalse(current["build_allowed"])
        self.assertEqual(current["build_reason"], "BUILD_LEASE_MISSING")

    def test_active_lease_actor_tampering_is_rejected(self) -> None:
        self.start_build()
        active_path = self.root / ".tempo/run/active.json"
        active = read_json(active_path)
        active["actor"] = "agent:other"
        write_json(active_path, active)

        self.assert_policy_code(
            "BUILD_LEASE_ACTOR_MISMATCH",
            validate_build_lease,
            self.workspace,
            actor="agent:builder",
            session=SESSION,
        )

    def test_duplicate_start_receipt_fails_closed(self) -> None:
        self.start_build()
        active = read_json(self.root / ".tempo/run/active.json")
        Ledger(self.workspace).append(
            "mvp_started",
            actor=active["actor"],
            session=active["session"],
            relevant_ids={
                "warrant_id": active["warrant_id"],
                "mvp_id": active["mvp_id"],
                "task_id": active["task_id"],
            },
            artifact_hashes={},
            evidence_refs=[],
            reason_code="DUPLICATE_START_TEST",
            resulting_state="BUILDING",
            details={"path": active["path"], "lane": active["lane"], "action": active["action"]},
        )

        error = self.assert_policy_code("BUILD_START_RECEIPT_INVALID", validate_build_lease, self.workspace)
        self.assertEqual(error.details["matching_events"], 1)
        self.assertEqual(error.details["lease_events"], 2)

    def test_same_owner_can_rotate_and_revisit_paths_with_unique_receipts(self) -> None:
        first = self.start_build()
        second = start(
            self.workspace,
            task_id="T-TEST-001",
            path="src/tempo/other.py",
            lane="core",
            action="implementation_write",
            actor="agent:builder",
            session=SESSION,
        )
        self.assertTrue(second["rotated"])
        self.assertFalse(second["idempotent"])
        self.assertEqual(second["path"], "src/tempo/other.py")
        self.assertEqual(validate_build_lease(self.workspace, path=second["path"])["active"]["path"], second["path"])

        third = self.start_build()
        self.assertTrue(third["rotated"])
        self.assertEqual(third["path"], first["path"])
        current = validate_build_lease(self.workspace, path=first["path"])
        self.assertEqual(current["start_event"]["details"]["started_at"], third["started_at"])
        self.assertEqual(len([event for event in Ledger(self.workspace).events() if event["event_type"] == "mvp_started"]), 3)

    def test_failed_rotation_restores_the_previous_active_lease(self) -> None:
        first = self.start_build()
        with patch("tempo.warrant.Ledger.append", side_effect=OSError("simulated ledger failure")):
            with self.assertRaises(OSError):
                start(
                    self.workspace,
                    task_id="T-TEST-001",
                    path="src/tempo/other.py",
                    lane="core",
                    action="implementation_write",
                    actor="agent:builder",
                    session=SESSION,
                )

        self.assertEqual(read_json(self.root / ".tempo/run/active.json")["path"], first["path"])
        self.assertEqual(validate_build_lease(self.workspace)["active"]["path"], first["path"])

    def test_guard_rejects_session_that_does_not_own_active_lease(self) -> None:
        self.start_build()

        self.assert_policy_code(
            "BUILD_LEASE_SESSION_MISMATCH",
            evaluate_event,
            self.workspace,
            {
                "tool": "edit_file",
                "input": {"path": "src/tempo/new.py", "new_string": "safe = True"},
                "actor": "agent:builder",
                "session": "test:other-session",
                "lane": "core",
                "action": "implementation_write",
            },
        )


if __name__ == "__main__":
    import unittest

    unittest.main()

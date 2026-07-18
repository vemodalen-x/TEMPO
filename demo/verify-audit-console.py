#!/usr/bin/env python3
"""Validate the synthetic audit projection and static console contract."""

from __future__ import annotations

import argparse
from copy import deepcopy
from datetime import datetime
import hashlib
import json
from pathlib import Path
import re
import sys
from typing import Any


ROOT = Path(__file__).resolve().parent
FIXTURE = ROOT / "audit-console.fixture.json"
HTML = ROOT / "audit-console.html"
GENESIS = "sha256:" + "0" * 64
CLAIM_BOUNDARY = (
    "Synthetic interaction fixture for local UI validation. It is not customer "
    "evidence, build authority, or external attestation."
)
CLAIM_BOUNDARY_ZH = "仅用于本地界面验证的合成交互夹具；不是客户证据、构建权限或外部证明。"
RECORD_ID = re.compile(r"^AUD-DEMO-[0-9]{4}$")
ACTOR = re.compile(r"^(human|agent|kernel|verifier):[A-Za-z0-9][A-Za-z0-9._@+:/-]{1,127}$")
HASH = re.compile(r"^sha256:[a-f0-9]{64}$")
RECEIPT_REF = re.compile(r"^R-[A-Z0-9][A-Z0-9._-]{2,63}$")
RFC3339_UTC_SECONDS = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$")
NEXT_ACTION = (
    "NO_SAFE_AUTOMATED_ACTION: a human owner must define a new governed MVP "
    "cycle; the revoked warrant cannot be reused."
)
NEXT_ACTION_ZH = (
    "无可安全自动执行的动作：必须由人类负责人定义新的受治理 MVP 周期；"
    "已撤销的 warrant 不能复用。"
)
REF_GROUPS = {
    "tasks",
    "hypotheses",
    "charters",
    "assessments",
    "warrants",
    "receipts",
    "evidence",
    "artifacts",
}
EXPECTED_STORY = (
    (
        "opportunity_created",
        "allowed",
        "WORKSPACE_INITIALIZED",
        "Cycle 1: DRAFT / NOT_AUTHORIZED",
        "Cycle 1: DISCOVERY / NOT_AUTHORIZED",
        "human:founder",
    ),
    (
        "evidence_added",
        "allowed",
        "EVIDENCE_RECORDED",
        "Cycle 1: DISCOVERY / NOT_AUTHORIZED",
        "Cycle 1: VALIDATING / NOT_AUTHORIZED",
        "agent:researcher",
    ),
    (
        "readiness_assessed",
        "blocked",
        "EXPERIMENT_REQUIRED",
        "Cycle 1: VALIDATING / NOT_AUTHORIZED",
        "Cycle 1: EXPERIMENT_REQUIRED / NOT_AUTHORIZED",
        "kernel:tempo",
    ),
    (
        "evidence_added",
        "allowed",
        "EVIDENCE_RECORDED",
        "Cycle 1: EXPERIMENT_REQUIRED / NOT_AUTHORIZED",
        "Cycle 2: VALIDATING / NOT_AUTHORIZED",
        "verifier:local",
    ),
    (
        "readiness_assessed",
        "allowed",
        "MVP_AUTHORIZED",
        "Cycle 2: VALIDATING / NOT_AUTHORIZED",
        "Cycle 2: MVP_CANDIDATE / NOT_AUTHORIZED",
        "kernel:tempo",
    ),
    (
        "mvp_charter_signed",
        "allowed",
        "HUMAN_CHARTER_SIGNATURE",
        "Cycle 2: MVP_CANDIDATE / NOT_AUTHORIZED",
        "Cycle 2: MVP_CANDIDATE / NOT_AUTHORIZED",
        "human:founder",
    ),
    (
        "mvp_authorized",
        "allowed",
        "HUMAN_TTY_AUTHORIZATION",
        "Cycle 2: MVP_CANDIDATE / NOT_AUTHORIZED",
        "Cycle 2: MVP_CANDIDATE / AUTHORIZED",
        "human:founder",
    ),
    (
        "mvp_start_blocked",
        "blocked",
        "SCOPE_NOT_AUTHORIZED",
        "Cycle 2: MVP_CANDIDATE / AUTHORIZED",
        "Cycle 2: MVP_CANDIDATE / AUTHORIZED",
        "agent:builder",
    ),
    (
        "mvp_started",
        "allowed",
        "VALID_WARRANT_AND_SCOPE",
        "Cycle 2: MVP_CANDIDATE / AUTHORIZED",
        "Cycle 2: MVP_CANDIDATE / BUILDING",
        "agent:builder",
    ),
    (
        "mvp_authorization_invalidated",
        "blocked",
        "PROTECTED_INPUT_DRIFT",
        "Cycle 2: MVP_CANDIDATE / BUILDING",
        "Cycle 2: MVP_CANDIDATE / REVOKED",
        "kernel:tempo",
    ),
)

def _refs(
    *,
    tasks: tuple[str, ...] = (),
    hypotheses: tuple[str, ...] = (),
    charters: tuple[str, ...] = (),
    assessments: tuple[str, ...] = (),
    warrants: tuple[str, ...] = (),
    receipts: tuple[str, ...] = (),
    evidence: tuple[str, ...] = (),
    artifacts: tuple[str, ...] = (),
) -> dict[str, list[str]]:
    return {
        "tasks": list(tasks),
        "hypotheses": list(hypotheses),
        "charters": list(charters),
        "assessments": list(assessments),
        "warrants": list(warrants),
        "receipts": list(receipts),
        "evidence": list(evidence),
        "artifacts": list(artifacts),
    }


EXPECTED_REFS = (
    _refs(hypotheses=("H-AUDIT-001",), artifacts=("plan/opportunity.json",)),
    _refs(
        hypotheses=("H-AUDIT-001",),
        evidence=("E-AUDIT-001",),
        artifacts=("plan/evidence/E-AUDIT-001.json",),
    ),
    _refs(
        hypotheses=("H-AUDIT-001",),
        assessments=("A-DEMO-0001",),
        evidence=("E-AUDIT-001",),
        artifacts=(".tempo/assessments/A-DEMO-0001.json",),
    ),
    _refs(
        hypotheses=("H-AUDIT-001",),
        receipts=("R-DEMO-EXPERIMENT",),
        evidence=("E-AUDIT-001", "E-AUDIT-002"),
        artifacts=("plan/evidence/E-AUDIT-002.json",),
    ),
    _refs(
        hypotheses=("H-AUDIT-001",),
        charters=("M-AUDIT-001",),
        assessments=("A-DEMO-0002",),
        evidence=("E-AUDIT-001", "E-AUDIT-002"),
        artifacts=(".tempo/assessments/A-DEMO-0002.json",),
    ),
    _refs(
        tasks=("T-AUDIT-PHASE1",),
        hypotheses=("H-AUDIT-001",),
        charters=("M-AUDIT-001",),
        assessments=("A-DEMO-0002",),
        evidence=("E-AUDIT-001", "E-AUDIT-002"),
        artifacts=("plan/mvp-charter.json",),
    ),
    _refs(
        tasks=("T-AUDIT-PHASE1",),
        hypotheses=("H-AUDIT-001",),
        charters=("M-AUDIT-001",),
        assessments=("A-DEMO-0002",),
        warrants=("W-DEMO-0001",),
        evidence=("E-AUDIT-001", "E-AUDIT-002"),
        artifacts=("plan/authorization-warrant.json",),
    ),
    _refs(
        tasks=("T-AUDIT-PHASE1",),
        hypotheses=("H-AUDIT-001",),
        charters=("M-AUDIT-001",),
        assessments=("A-DEMO-0002",),
        warrants=("W-DEMO-0001",),
        artifacts=("src/unrelated.py",),
    ),
    _refs(
        tasks=("T-AUDIT-PHASE1",),
        hypotheses=("H-AUDIT-001",),
        charters=("M-AUDIT-001",),
        assessments=("A-DEMO-0002",),
        warrants=("W-DEMO-0001",),
        artifacts=("src/tempo/audit.py",),
    ),
    _refs(
        tasks=("T-AUDIT-PHASE1",),
        hypotheses=("H-AUDIT-001",),
        charters=("M-AUDIT-001",),
        assessments=("A-DEMO-0002",),
        warrants=("W-DEMO-0001",),
        artifacts=("plan/mvp-charter.json",),
    ),
)


def canonical_bytes(value: Any) -> bytes:
    return json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")


def projection_digest(record: dict[str, Any]) -> str:
    payload = {key: value for key, value in record.items() if key != "projection_hash"}
    return "sha256:" + hashlib.sha256(canonical_bytes(payload)).hexdigest()


def bundle_digest(data: dict[str, Any]) -> str:
    payload = deepcopy(data)
    checkpoint = payload.get("projection_checkpoint")
    if isinstance(checkpoint, dict):
        checkpoint.pop("bundle_hash", None)
    return "sha256:" + hashlib.sha256(canonical_bytes(payload)).hexdigest()


def expected_chain(data: dict[str, Any]) -> list[str]:
    previous = GENESIS
    hashes: list[str] = []
    records = data.get("events")
    if not isinstance(records, list):
        raise ValueError("events must be a list")
    for record in records:
        if not isinstance(record, dict):
            raise ValueError("every projection record must be an object")
        candidate = dict(record)
        candidate["previous_projection_hash"] = previous
        digest = projection_digest(candidate)
        hashes.append(digest)
        previous = digest
    return hashes


def parse_timestamp(value: Any) -> datetime | None:
    if not isinstance(value, str) or not RFC3339_UTC_SECONDS.fullmatch(value):
        return None
    try:
        parsed = datetime.fromisoformat(value[:-1] + "+00:00")
    except ValueError:
        return None
    return parsed if parsed.tzinfo is not None else None


def _nonempty_text(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip()) and len(value) <= 4000


def _number_contract_errors(value: Any, location: str = "fixture") -> list[str]:
    """Keep Python and browser canonical JSON number semantics identical."""
    errors: list[str] = []
    if isinstance(value, float):
        return [f"{location} contains a floating-point value; only safe integers are allowed"]
    if type(value) is int and abs(value) > 9_007_199_254_740_991:
        return [f"{location} contains an integer outside the cross-runtime safe range"]
    if isinstance(value, list):
        for index, item in enumerate(value):
            errors.extend(_number_contract_errors(item, f"{location}[{index}]"))
    elif isinstance(value, dict):
        for key, item in value.items():
            errors.extend(_number_contract_errors(item, f"{location}.{key}"))
    return errors


def validate_fixture(data: Any) -> list[str]:
    errors: list[str] = []
    if not isinstance(data, dict):
        return ["fixture root must be an object"]
    if len(canonical_bytes(data)) > 1_000_000:
        errors.append("fixture exceeds the 1 MB prototype limit")
    errors.extend(_number_contract_errors(data))
    if type(data.get("schema_version")) is not int or data.get("schema_version") != 1:
        errors.append("schema_version must be 1")
    if data.get("fixture") is not True:
        errors.append("fixture must be true")
    if data.get("profile") != "solo":
        errors.append("the shipped interaction fixture must use the solo profile")
    if parse_timestamp(data.get("generated_at")) is None:
        errors.append("generated_at must be RFC3339 UTC at whole-second precision")
    if data.get("claim_boundary") != CLAIM_BOUNDARY:
        errors.append("claim_boundary must preserve the exact synthetic trust boundary")
    if data.get("claim_boundary_zh") != CLAIM_BOUNDARY_ZH:
        errors.append("claim_boundary_zh must preserve the exact synthetic trust boundary")

    projection = data.get("projection")
    if not isinstance(projection, dict):
        errors.append("projection metadata is required")
    elif (
        projection.get("kind") != "synthetic_audit_projection"
        or projection.get("authoritative") is not False
        or projection.get("source") != "fixture://tempo-audit-console"
    ):
        errors.append("projection metadata overstates the synthetic view")

    current = data.get("current")
    if not isinstance(current, dict):
        errors.append("current projection is required")
    elif (
        current.get("business_state") != "MVP_CANDIDATE"
        or current.get("mvp_state") != "REVOKED"
        or current.get("build_allowed") is not False
        or current.get("reason_code") != "PROTECTED_INPUT_DRIFT"
        or current.get("next_action") != NEXT_ACTION
        or current.get("next_action_zh") != NEXT_ACTION_ZH
    ):
        errors.append("current projection must remain terminal, revoked, and non-authorizing")

    checkpoint = data.get("projection_checkpoint")
    if not isinstance(checkpoint, dict):
        errors.append("projection_checkpoint is required")
        checkpoint = {}
    else:
        if type(checkpoint.get("version")) is not int or checkpoint.get("version") != 1:
            errors.append("projection_checkpoint.version must be 1")
        if checkpoint.get("trust") != "self_contained_synthetic_fixture":
            errors.append("projection checkpoint must not claim durable or external trust")
        for field in ("head_hash", "bundle_hash"):
            value = checkpoint.get(field)
            if not isinstance(value, str) or not HASH.fullmatch(value):
                errors.append(f"projection_checkpoint.{field} is invalid")

    records = data.get("events")
    if not isinstance(records, list):
        return errors + ["events must be a list"]
    if len(records) != len(EXPECTED_STORY):
        errors.append(f"events must contain the {len(EXPECTED_STORY)}-record governed story")

    examples = data.get("receipt_examples")
    if not isinstance(examples, list):
        errors.append("receipt_examples must be a list")
        examples = []
    if len(examples) != 2:
        errors.append("receipt_examples must contain the two fixed illustrative examples")
    example_ids: set[str] = set()
    for index, example in enumerate(examples):
        location = f"receipt_examples[{index}]"
        if not isinstance(example, dict):
            errors.append(f"{location} must be an object")
            continue
        example_id = example.get("example_receipt_id")
        if not isinstance(example_id, str) or not RECEIPT_REF.fullmatch(example_id):
            errors.append(f"{location}.example_receipt_id is invalid")
        elif example_id in example_ids:
            errors.append(f"duplicate example_receipt_id: {example_id}")
        else:
            example_ids.add(example_id)
        provenance = example.get("provenance")
        if (
            example.get("illustrative") is not True
            or example.get("executed") is not False
            or example.get("outcome") != "not_executed"
            or not isinstance(provenance, dict)
            or provenance.get("kind") != "illustrative_projection"
            or provenance.get("trust") != "no_execution_claim"
            or provenance.get("authoritative") is not False
            or provenance.get("attestation_ref") is not None
        ):
            errors.append(f"{location} must remain illustrative and explicitly not executed")
        for field in ("summary", "summary_zh"):
            if not _nonempty_text(example.get(field)):
                errors.append(f"{location}.{field} is required")
        for field in ("planned_checks", "planned_checks_zh"):
            values = example.get(field)
            if (
                not isinstance(values, list)
                or not values
                or len(values) > 50
                or not all(_nonempty_text(value) for value in values)
            ):
                errors.append(f"{location}.{field} must be a bounded non-empty text list")
        if (
            isinstance(example.get("planned_checks"), list)
            and isinstance(example.get("planned_checks_zh"), list)
            and len(example["planned_checks"]) != len(example["planned_checks_zh"])
        ):
            errors.append(f"{location} bilingual planned-check lists must have equal length")

    seen_ids: set[str] = set()
    previous_hash = GENESIS
    previous_time: datetime | None = None
    for index, record in enumerate(records, start=1):
        location = f"events[{index - 1}]"
        if not isinstance(record, dict):
            errors.append(f"{location} must be an object")
            continue
        if type(record.get("sequence")) is not int or record.get("sequence") != index:
            errors.append(f"{location}.sequence must be {index}")
        record_id = record.get("record_id")
        if not isinstance(record_id, str) or not RECORD_ID.fullmatch(record_id):
            errors.append(f"{location}.record_id is invalid")
        elif record_id in seen_ids:
            errors.append(f"duplicate record_id: {record_id}")
        else:
            seen_ids.add(record_id)
        actor = record.get("actor")
        if not isinstance(actor, str) or not ACTOR.fullmatch(actor):
            errors.append(f"{location}.actor is invalid")
        timestamp = parse_timestamp(record.get("timestamp"))
        if timestamp is None:
            errors.append(f"{location}.timestamp must be RFC3339 UTC")
        elif previous_time is not None and timestamp < previous_time:
            errors.append(f"{location}.timestamp is not monotonic")
        if timestamp is not None:
            previous_time = timestamp
        if index <= len(EXPECTED_STORY):
            expected = EXPECTED_STORY[index - 1]
            actual = (
                record.get("type"),
                record.get("outcome"),
                record.get("reason_code"),
                record.get("state_before"),
                record.get("state_after"),
                record.get("actor"),
            )
            if actual != expected:
                errors.append(f"{location} violates the governed two-cycle story")
        for field in ("summary", "summary_zh", "detail", "detail_zh"):
            if not _nonempty_text(record.get(field)):
                errors.append(f"{location}.{field} is required")
        for field in ("previous_projection_hash", "projection_hash"):
            value = record.get(field)
            if not isinstance(value, str) or not HASH.fullmatch(value):
                errors.append(f"{location}.{field} is invalid")
        if record.get("previous_projection_hash") != previous_hash:
            errors.append(f"{location}.previous_projection_hash does not match the prior record")
        calculated = projection_digest(record)
        if record.get("projection_hash") != calculated:
            errors.append(f"{location}.projection_hash mismatch: expected {calculated}")
        previous_hash = calculated

        refs = record.get("refs")
        if not isinstance(refs, dict) or set(refs) != REF_GROUPS:
            errors.append(f"{location}.refs must contain the stable projection groups")
            continue
        refs_valid = True
        for group, values in refs.items():
            if (
                not isinstance(values, list)
                or len(values) > 100
                or not all(isinstance(value, str) and 0 < len(value) <= 512 for value in values)
                or len(values) != len(set(values))
            ):
                errors.append(f"{location}.refs.{group} must be a bounded unique string list")
                refs_valid = False
        if index <= len(EXPECTED_REFS) and refs != EXPECTED_REFS[index - 1]:
            errors.append(f"{location}.refs violates the fixed governed reference story")
        receipt_values = refs.get("receipts")
        if refs_valid and isinstance(receipt_values, list):
            unknown_examples = set(receipt_values) - example_ids
            if unknown_examples:
                errors.append(f"{location} references unknown receipt examples: {sorted(unknown_examples)}")

    if type(checkpoint.get("sequence")) is not int or checkpoint.get("sequence") != len(records):
        errors.append("projection_checkpoint.sequence does not match the record count")
    if checkpoint.get("head_hash") != previous_hash:
        errors.append("projection_checkpoint.head_hash does not match the projection head")
    calculated_bundle = bundle_digest(data)
    if checkpoint.get("bundle_hash") != calculated_bundle:
        errors.append(
            "projection_checkpoint.bundle_hash does not cover the complete fixture: "
            f"expected {calculated_bundle}"
        )
    return errors


def validate_html(text: str) -> list[str]:
    required_tokens = {
        "bilingual title": "Audit trail / 审计轨迹",
        "fixture boundary": "Synthetic fixture",
        "today surface": 'id="todayCard"',
        "timeline": 'id="timeline"',
        "trace": 'id="tracePanel"',
        "receipt examples": 'id="receiptsPanel"',
        "export JSON": 'id="exportJson"',
        "export HTML": 'id="exportHtml"',
        "file fallback": 'id="fixturePicker"',
        "screen-reader updates": 'aria-live="polite"',
        "visible focus": ":focus-visible",
        "Web Crypto projection check": "crypto.subtle.digest",
        "no authority claim": "cannot authorize work",
        "browser self-test": 'id="selfTestResult"',
        "content security policy": "Content-Security-Policy",
    }
    return [
        f"HTML missing {label}: {token}"
        for label, token in required_tokens.items()
        if token not in text
    ]


def _checker_failure(message: str) -> int:
    print("AUDIT_CONSOLE_CHECKER_FAILURE", file=sys.stderr)
    print(f"- {message}", file=sys.stderr)
    return 3


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--print-chain",
        action="store_true",
        help="Print expected projection hashes without validating stored hashes.",
    )
    parser.add_argument(
        "--print-bundle-hash",
        action="store_true",
        help="Print the expected complete-fixture hash without validating it.",
    )
    args = parser.parse_args()
    try:
        data = json.loads(FIXTURE.read_text(encoding="utf-8"))
        if args.print_chain:
            for index, digest in enumerate(expected_chain(data), start=1):
                print(f"{index}: {digest}")
            return 0
        if args.print_bundle_hash:
            print(bundle_digest(data))
            return 0
        fixture_errors = validate_fixture(data)
    except (OSError, UnicodeError, json.JSONDecodeError, TypeError, ValueError) as exc:
        return _checker_failure(str(exc))
    except Exception as exc:  # pragma: no cover - last-resort stable exit boundary
        return _checker_failure(f"unexpected validator failure: {exc}")

    if fixture_errors:
        print("AUDIT_FIXTURE_POLICY_BLOCK", file=sys.stderr)
        for error in fixture_errors:
            print(f"- {error}", file=sys.stderr)
        return 2

    try:
        text = HTML.read_text(encoding="utf-8")
    except (OSError, UnicodeError) as exc:
        return _checker_failure(str(exc))
    html_errors = validate_html(text)
    if html_errors:
        print("AUDIT_CONSOLE_CHECKER_FAILURE", file=sys.stderr)
        for error in html_errors:
            print(f"- {error}", file=sys.stderr)
        return 3

    print(
        json.dumps(
            {
                "outcome": "AUDIT_CONSOLE_VALID",
                "projection_records": len(data["events"]),
                "illustrative_receipt_examples": len(data["receipt_examples"]),
                "projection_head": data["events"][-1]["projection_hash"],
                "bundle_hash": data["projection_checkpoint"]["bundle_hash"],
                "claim_boundary": data["claim_boundary"],
            },
            ensure_ascii=False,
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

# Auditable solo-company workflow: Phase 1

Status: evidence-only interaction prototype and implementation specification.
It does not change runtime policy, grant a warrant, or authorize product code.

Date: 2026-07-18

## Outcome

Make TEMPO easier for a founder or small company to operate without weakening
its controls. A user should be able to answer four questions in under one
minute:

1. What can I do now?
2. Why is an action allowed or blocked?
3. Which evidence and human decisions caused that result?
4. Can another reviewer reconstruct and export the same history?

The accompanying [`demo/audit-console.html`](../../demo/audit-console.html) is
an offline, synthetic prototype of that journey. It reads no live TEMPO state,
does not write repository data, and cannot authorize work.

## Practice adopted from task `019f706f-f9f4-7303-932a-58183d2ba2f1`

The referenced practice run provides five useful constraints:

- A user message is not silently converted into a signature or customer
  result. Human approval must cross the existing interactive signing boundary.
- Evidence-only work remains type-distinct from product implementation.
- Synthetic fixture observations test tooling but never become real evidence.
- The main interface presents the user's task; raw JSON and operator controls
  live in a secondary, inspectable layer.
- Interaction claims are checked in a real browser as well as by static tests.

It also demonstrated a repository-boundary rule: framework capabilities belong
in TEMPO, while downstream product code belongs in a separate repository pinned
to a TEMPO revision. This proposal contains only framework-level behavior.

## Target journey

```text
tempo today
  -> one current goal, authority state, reason, and safest next action

tempo next
  -> one executable command or one clearly named human checkpoint

tempo audit timeline
  -> ordered, filterable decisions, attempts, receipts, and state changes

tempo trace <id>
  -> upstream evidence/decision inputs and downstream attempts/receipts

tempo audit export --format html
  -> portable review bundle with verification status and claim boundaries
```

`today` and `next` are projections over authoritative records. They must never
invent a state transition or infer permission from prose.

## Interaction contract

Every human-readable result uses the same information order:

1. **Outcome** — allowed, blocked, warning, or informational.
2. **Why** — stable reason code plus a plain-language sentence.
3. **Evidence** — concrete IDs and paths, never the phrase “see artifacts”.
4. **Next action** — exactly one safe next command or human checkpoint.

Raw JSON remains available, but it is not the default surface for a founder.
Blocked attempts stay visible in the timeline and are never hidden by a
successful retry.

## Profiles

Profiles change defaults and required checkpoints, not truth semantics.

| Profile | Intended operator | Default detail | Human checkpoints | Export |
| --- | --- | --- | --- | --- |
| `solo` | Founder or one-person company | One next action and compact timeline | Signature and destructive/external actions | Local HTML + JSON |
| `team` | Cross-functional product team | Owners, handoffs, and pending reviews | Signature, spend, external actions, policy exceptions | HTML + JSON + review index |
| `regulated` | High-assurance workflow | Full provenance and data classification | All sensitive transitions and external attestations | Signed/attested bundle when configured |

A `solo` profile cannot lower schema, signature, scope, budget, deadline,
counterevidence, or verification requirements.

## Runtime data model

### 1. Immutable input snapshots

Every assessment binding should retain both integrity and reconstructability:

```json
{
  "artifact_ref": "plan/hypotheses.json",
  "hash": "sha256:<digest>",
  "snapshot_ref": ".tempo/objects/sha256/ab/<remaining-digest>",
  "media_type": "application/json",
  "size_bytes": 1234
}
```

The object store preserves exact raw bytes, is content-addressed, write-once,
and verified on read. Existing `artifact_ref` and `hash` fields remain
unchanged for compatibility; optional `snapshot_ref`, `media_type`, and
`size_bytes` fields add reconstruction. JSONL and other non-JSON inputs are not
renamed or reserialized.

### 2. Serialized mutable heads

State transitions, ledger appends, evidence-manifest appends, and durable-head
updates use one repository-local lock discipline. Concurrent success with a
lost transition is forbidden. Whenever more than one store is involved, the
fixed nested order is `authorization -> evidence -> ledger` after omitting
stores that are not part of that operation. State code must release the state
lock before appending a ledger event; it must never wait for a ledger lock while
holding the state lock.

Multi-store operations use a write-ahead transaction journal from the first
implementation slice: record the exact intent and expected old heads, append in
the declared order, advance durable heads, then mark the journal complete. A
filesystem crash can therefore leave a detectable partial append; it is not
described as atomic. Readers fail closed while an incomplete journal exists,
until conservative recovery either completes those exact recorded bytes or
restores the previously authoritative heads without deleting observed material.

Audit reads use a stable-head double read: capture all relevant durable heads,
read and verify the stores, then re-read the heads. A changed head causes a
bounded retry or an explicit `AUDIT_SNAPSHOT_CHANGED` warning, never a mixed
snapshot presented as verified.

### 3. Cross-store reconciliation

`tempo audit verify` should compare:

- ledger tail against its durable head checkpoint;
- evidence manifest tail against its durable head checkpoint;
- every `evidence_added` event against one manifest record;
- every manifest record against its immutable evidence object;
- assessments and warrants against their snapshotted inputs; and
- receipts against referenced checks and artifacts.

The verifier fails closed on a missing tail, orphaned record, duplicate ID,
unknown reference, object hash mismatch, or partial transaction journal.

### 4. Read-only audit projection

Timeline and trace output are derived indexes. They may be deleted and rebuilt
without losing authority or evidence. The projection records source locations
so a reviewer can open the authoritative item behind every row.

## Proposed command contracts

### `tempo today`

Returns the current business and MVP states, warrant validity, the most recent
meaningful event, unresolved blockers, and one next action. Exit `0` is an
informational success; it does not mean implementation is allowed.

### `tempo next`

Returns one of:

- an executable, non-destructive CLI command;
- an ordered human checkpoint, including the exact artifact to review; or
- `NO_SAFE_AUTOMATED_ACTION` when no agent action is authorized.

It must not suggest a signer command as though the agent can perform the human
confirmation.

### `tempo audit timeline`

Supports filters for time, outcome, reason code, actor, event type, task,
hypothesis, charter, assessment, warrant, receipt, and evidence IDs. Human
output is concise; `--json` returns a stable schema with source references.

### `tempo trace <id>`

Accepts any governed identifier and returns:

- upstream inputs that explain the item;
- the authoritative source path and immutable snapshot where available;
- downstream state changes, attempts, and receipts; and
- verification gaps that prevent a complete reconstruction.

An unknown ID returns warning exit `4`; an ambiguous ID or integrity mismatch
returns policy-block exit `2`. An executor, schema-engine, or I/O failure
returns checker-failure exit `3`.

### `tempo audit export`

Produces a local JSON or self-contained HTML bundle. The header declares
fixture status, provenance ceiling, verification time, unresolved gaps, and
whether external attestation exists. Export never upgrades local integrity to
external assurance.

### `tempo repair`

Repair is conservative and journaled. It may rebuild derived indexes or finish
an interrupted append when every authoritative hash agrees. It may not invent
a missing event, evidence item, signature, receipt, or human verdict.

## Minimum authorized implementation slices

1. **Integrity foundation**
   - content-addressed assessment snapshots;
   - one cross-platform repository lock for state and append-only stores;
   - a write-ahead transaction journal and fail-closed incomplete-journal reads;
   - evidence durable-head checkpoint;
   - ledger/manifest/object reconciliation;
   - tamper and concurrency tests.
2. **Operator navigation**
   - `today`, `next`, `audit timeline`, receipt list/show, and `trace`;
   - specific human rendering for current commands;
   - stable JSON contracts and accessibility-oriented terminal output.
3. **Recovery and portability**
   - JSON/HTML export;
   - rebuildable audit indexes;
   - conservative `repair` diagnostics over the slice-1 transaction journal.
4. **Governed experiment lane**
   - implement the separate proposal in
     [`governed-experiment-lane.md`](governed-experiment-lane.md);
   - expose `quick`, `standard`, and `sensitive` experiment profiles;
   - prove experimentally issued permits are rejected by `mvp start`.

Slices 2–4 depend on slice 1. They should not be merged as one unreviewable
change.

## Acceptance matrix

| Risk | Required proof |
| --- | --- |
| Historical input changed after assessment | Trace still opens the original immutable snapshot and reports current drift |
| Evidence manifest tail deleted | Audit verification fails even when the remaining local chain is internally valid |
| Ledger says two evidence items but manifest has one | Reconciliation returns a specific count/reference mismatch |
| Two state transitions race | Both are serialized or one fails explicitly; no successful transition is lost |
| Process exits between data append and head update | Reads fail closed; recovery reports the journal and either completes the exact recorded append or restores the old authoritative heads without deleting observed bytes |
| Unknown or corrupt trace reference | Stable exit and reason code; no partial “verified” result |
| Fixture exported for review | Header says fixture and local integrity; no customer-validation claim |
| Narrow terminal | Outcome, reason, IDs, and next action remain readable without horizontal scrolling |
| Keyboard-only browser use | Timeline, filters, details, trace, and export are reachable with visible focus |

## Migration and compatibility

- Existing receipts, ledgers, manifests, and assessments remain readable.
- Legacy assessments without snapshots display
  `HISTORICAL_INPUT_NOT_RECONSTRUCTABLE`; they are never silently backfilled
  from current files.
- Creating the first evidence head checkpoint requires a reconciliation pass.
  A mismatch blocks checkpoint creation and preserves all observed material.
- New human text is additive. Existing JSON keys and stable exit codes remain
  compatible unless a versioned schema explicitly says otherwise.

## Current authorization boundary

The repository is feature-frozen and `tempo mvp status` currently reports
`build_allowed: false`. The tracked freeze permits documentation and demo work
but mechanically blocks `src/**`, `tests/**`, and planning changes. This file
and the audit console therefore stop at a verified prototype. Runtime
implementation requires both:

1. a human-controlled decision to open a scoped post-freeze development cycle;
2. a current, hash-bound warrant followed by a successful `tempo mvp start` for
   the exact task, lane, action, and path.

# Governed evidence-only experiment lane

Status: proposal only; not an implemented TEMPO capability and not build
authority.

Date: 2026-07-18

## Outcome

TEMPO correctly separates evidence, readiness, and human build authority. A
downstream MVP practice run exposed a missing middle lane: a readiness
assessment can recommend the cheapest next experiment, but TEMPO cannot yet
issue a narrower permit for collecting that evidence. Teams therefore assemble
experiment scripts, privacy limits, checkpoints, and receipts ad hoc.

The proposed lane authorizes only bounded evidence collection. It must never be
accepted by `tempo mvp start`, and it must never authorize product source
writes, deployment, publication, upload, submission, or a human-owned decision.

## Problems to solve

1. **No first-class experiment lifecycle.** There is no deterministic
   `prepare -> approve -> start -> checkpoint -> record -> close` state machine
   for evidence-only work.
2. **Collection authority is implicit.** Evidence ingestion is guarded, but
   collection lacks a hash-bound permit covering paths, actions, people, data,
   services, time, and cost.
3. **External constraints are not snapshotted.** Rules and provider contracts
   can change; a run should bind to timestamped, explicitly untrusted snapshots.
4. **Environment failures occur late.** Required runtimes, codecs, fonts,
   providers, network access, and output paths should fail at preflight.
5. **Human checkpoints are not ordered artifacts.** A cheap sample or keyframe
   should be reviewable before a full render or other expensive operation.
6. **Domain adapters need mixed checks.** Machine validity alone cannot decide
   qualities such as voice naturalness or visual hierarchy, while human preview
   alone cannot prove codec, timing, source, or budget compliance.
7. **Founder-MVP evidence is easy to overclaim.** One builder can establish
   bounded technical feasibility, not independent user value. The framework
   should encode those as different stages, hypotheses, and evidence classes.

## Proposed authority model

Add an experiment permit that is intentionally weaker and type-distinct from
an MVP warrant.

| Capability | Experiment permit | MVP warrant |
| --- | --- | --- |
| Generate declared fixtures | Allowed when scoped | Allowed when scoped |
| Collect declared observations | Allowed when scoped | Allowed when scoped |
| Write product implementation | Never | Allowed when scoped |
| Deploy, upload, publish, or submit | Never | Separate explicit authority |
| Sign a decision or verdict | Never | Human-only boundary |
| Satisfy readiness by itself | Never | No; evidence must be ingested and reassessed |

The serialized permit should use a distinct schema and signing purpose so no
parser or guard can confuse it with `authorization-warrant.schema.json`.

## Proposed lifecycle

1. `tempo experiment prepare --spec <path>` validates the proposal and pins
   hypotheses, proposed action, source revisions, constraint snapshots,
   checkpoints, stop conditions, and budgets.
2. `tempo experiment approve --signer <human>` requires interactive human
   confirmation and emits a short-lived, hash-bound experiment permit.
3. `tempo experiment start --task <id>` revalidates scope, deadline, money,
   wall-clock, network, services, data class, and protected hashes.
4. `tempo experiment checkpoint --stage <name>` records deterministic checks
   and, where declared, an interactive human preview result.
5. `tempo experiment record --input <observation>` preserves supporting,
   neutral, ineligible, and contradictory observations with provenance.
6. `tempo experiment close` verifies stop/cleanup conditions and emits a
   machine receipt. Readiness must be reassessed as a separate command.

The start guard should fail closed on an unknown action, path, service, data
class, participant class, or checkpoint order.

## Required contract fields

- decision to unlock, hypothesis references, and proposed-action reference;
- allowed and forbidden paths and actions;
- source revisions and external-constraint snapshots;
- wall-clock, money, request, render, and network budgets;
- declared services and exact transmitted-content classes;
- participant eligibility, consent, privacy, and retention rules;
- ordered machine and human checkpoints;
- counterevidence retention and ineligible-observation handling;
- stop conditions and cleanup steps; and
- explicit `grants_product_build: false` and `accepted_by_mvp_start: false`.

## Staged founder-MVP pattern

TEMPO should provide a documented pattern for two decisions without weakening a
rank-1 user-outcome threshold:

1. **Founder technical stage:** one named builder tests delivery feasibility
   against a narrowly scoped technical hypothesis and produces local receipts.
2. **External outcome stage:** independent participants test usability or value
   against the original user-outcome hypothesis.

The stages require separate evidence types and decision briefs. A founder
receipt must not be relabeled as observed user behavior, and completing stage 1
must not silently satisfy stage 2.

## Adapter pattern

Domain adapters should contribute deterministic checks and named human preview
fields while inheriting the same authority boundary. A media adapter, for
example, may check container, codec, duration, audio levels, caption timing,
safe-zone intersections, and source coverage, while reserving voice
naturalness, pronunciation, readability, hierarchy, and pacing for explicit
human checkpoints.

The adapter may emit receipts only. It cannot approve its own checkpoint,
change readiness policy, issue a warrant, or publish an artifact.

## Minimum implementation slice after authorization

- experiment spec and permit schemas;
- prepare, approve, start, checkpoint, record, close, and status commands;
- path, action, time, cost, network, service, and data-transmission guards;
- immutable constraint-snapshot hashing and checkpoint ordering;
- serialized ledger events and a distinct experiment receipt;
- conformance tests proving the permit is rejected by MVP and external-action
  gates; and
- one credential-free demo with both a successful close and blocked escalation.

No framework code should be added from this proposal until TEMPO's existing
MVP start gate confirms a current warrant covering the implementation.

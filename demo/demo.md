# Judge demo

The demo is a deterministic, credential-free D0 journey for a product team
deciding whether to build an AI-enabled workflow. It should complete from a
clean clone with:

```bash
python bin/tempo demo
```

Use `python bin/tempo --json demo` for a machine-readable step report.

## Audit interaction prototype

The read-only [audit console](audit-console.html) demonstrates the proposed
`today -> timeline -> trace -> receipts -> export` journey with a synthetic,
hash-chained fixture. It cannot read live authority, mutate TEMPO, or authorize
work.

Serve only the `demo/` directory locally so the browser can load the adjacent
fixture:

```bash
python -m http.server 8000 --bind 127.0.0.1 --directory demo
```

Then open `http://127.0.0.1:8000/audit-console.html`. If the HTML is opened
directly from disk, use **Load fixture / 载入夹具** and select
`demo/audit-console.fixture.json`.

Validate the fixture chain and static interaction contract with:

```bash
python demo/verify-audit-console.py
python demo/verify-audit-console-browser.py
```

The browser check uses a locally installed Chromium-family browser, serves only
the `demo/` directory on an ephemeral loopback port, and exercises both desktop
and compact responsive viewports. It exits with warning code `4` when no
supported browser is installed.

## CLI judge demo expected story (`python bin/tempo demo`)

This table describes the deterministic CLI judge demo, not execution performed
by the audit console. The console displays only synthetic projection records
and explicitly unexecuted receipt-shaped examples.

| Beat | Expected result | What it proves |
| --- | --- | --- |
| Context and import | Proposal is normalized, never trusted as authority | Models assist planning without self-approval |
| First readiness check | `EXPERIMENT_REQUIRED`, exit `2` | Missing/insufficient external evidence stops the build path |
| Explicit demo evidence | Typed fixture measurements and provenance stay visible | The demo is reproducible without pretending validation |
| Second readiness check | Rank-1 threshold passes; `MVP_AUTHORIZED`, but `build_allowed: false` | A measured eligibility decision is still not authorization |
| Start without warrant | Policy block, exit `2` | A score cannot cross the human boundary |
| Demo authorization | Local-integrity, demo-only warrant | Scope/budget/deadline/hashes are bound |
| In-scope start | Allowed | A valid bounded path exists |
| Out-of-scope or drift attempt | Policy block, exit `2` | Authority fails closed when the contract changes |
| Verification and ledger | Local-integrity receipt, valid chain, durable head checkpoint | Claims have inspectable, tamper-evident local execution evidence |
| Verdict memo | Human section remains blank | The system cannot grade itself into approval |

Exact generated identifiers and timestamps vary. Reason codes, exit semantics,
state transitions, and fixture labels are deterministic.

## What not to claim

- Fixture evidence is not a customer interview or real conversion signal.
- The demo signer is not a production identity or cryptographic remote signer.
- A local receipt is not externally attested.
- This slice does not deploy a product, contact users, spend money, or submit to
  Devpost.
- The runtime does not call GPT-5.6 or any other hosted model.

## Useful follow-up commands

```bash
python bin/tempo mvp status
python bin/tempo evidence validate
python bin/tempo ledger verify
python bin/tempo verify --level all
python bin/tempo verdict compile
python bin/tempo submit-check
```

For the submitted release, `submit-check` is expected to pass: the public
repository, judge-accessible unlisted video, confirmed `/feedback` session ID,
and final owner review are present. A failure means the local submission
package has drifted and should be investigated before any Devpost update.

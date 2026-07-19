# TEMPO — Devpost project description

## Tagline

Turn “should we build?” into evidence, a human decision, and a bounded start.

## Why I built it

I started TEMPO while building Understand Video on my own. Codex made every
implementation iteration faster, but I caught myself treating a convincing
model answer as a reason to keep coding. The missing question was not “can the
agent build this?” It was “who decided this should be built, from what
evidence, and within what exact scope?”

TEMPO grew out of that problem. It blocked my own downstream build when its
evidence, repository identity, or authorization did not match. That failure was
the feature I needed.

This submission is **TEMPO**. [Understand Video](https://github.com/vemodalen-x/understand-video)
is the separate downstream product I used to dogfood the framework and produce
the explanation video; its code is not copied into TEMPO.

## Judge it in 60 seconds

From a clean clone, with Python 3.10+ and no account, API key, package install,
or sample-data download:

```bash
python bin/tempo demo
```

The run takes about two seconds and ends with `JUDGE_DEMO_PASSED`. Before that,
it shows model advice creating no authority, insufficient evidence naming the
next experiment, readiness remaining blocked without a warrant, one bounded
start succeeding, out-of-scope work and protected-input drift failing closed,
and a hash-chained ledger verifying while the human verdict stays blank.

- [Open the live 60-second animated story](https://htmlpreview.github.io/?https://github.com/vemodalen-x/TEMPO/blob/main/docs/judge-story.html)
- [Preview the bilingual audit console](https://raw.githubusercontent.com/vemodalen-x/TEMPO/main/docs/audit-console.png)
- [Watch the 140-second demo video](https://youtu.be/3eIxgVo9z4I)

The browser console is deliberately read-only and uses a clearly labeled
synthetic fixture. It demonstrates the review experience; it cannot authorize
work or pretend to be customer evidence. To interact with it, clone the repo,
serve `demo/` locally, and open `audit-console.html`.

![TEMPO bilingual audit trail with synthetic-fixture label](https://raw.githubusercontent.com/vemodalen-x/TEMPO/main/docs/audit-console.png)

## What TEMPO does

TEMPO is a deterministic business-to-MVP control layer for founders, product
leads, and innovation owners supervising coding agents.

1. A planning provider may propose an opportunity, business model, hypothesis,
   and cheapest experiment. TEMPO treats that output as untrusted advice.
2. Evidence is checked for provenance, freshness, directness, measurements,
   and counterevidence. Hard blockers run before scores.
3. Readiness returns either the next experiment or eligibility for a human
   decision. Eligibility never grants implementation authority.
4. A separate, time-bounded human warrant binds the assessment, evidence,
   charter, repository identity, scope, action, budget, and deadline.
5. Every implementation start is checked against that warrant. Drift, expiry,
   revocation, and out-of-scope work fail closed.
6. A serialized hash-chained ledger, durable checkpoint, receipts, and verdict
   memo make the decision inspectable without filling the human-owned verdict.

The useful answer is sometimes “not yet.” TEMPO returns the failed condition
and the cheapest next experiment instead of a vague denial.

## How I built it

The released vertical slice is a dependency-light Python CLI with JSON Schema
contracts, deterministic state transitions, local file/action guards, evidence
checks, authorization and revocation, verification receipts, and a
credential-free judge demo. GitHub Actions runs it on Windows, macOS, and Linux
and in a digest-pinned, unprivileged, network-disabled container.

Two integrity bugs shaped the final design. A warrant now binds the exact Git
origin, revision, commit, worktree, Git directory, and common directory, so a
branch, origin, commit, or second-worktree change invalidates authority. Ledger
append is failure-atomic: if checkpoint replacement fails, TEMPO rolls back
only the exact fsynced event; if safe rollback cannot be proved, it remains
blocked. The released [repository-subject tests](https://github.com/vemodalen-x/TEMPO/blob/main/tests/test_subject.py)
and [ledger failure tests](https://github.com/vemodalen-x/TEMPO/blob/main/tests/test_ledger.py)
exercise both paths.

The current release discovers 107 tests: 106 pass and one Windows
symlink-permission case is skipped where the OS denies symlink creation. The
latest public CI is green across every required host and the network-disabled
[judge container](https://github.com/vemodalen-x/TEMPO/actions/workflows/ci.yml).

## How I used Codex and GPT-5.6

I used Codex Desktop with GPT-5.6 throughout the build, not only for an initial
scaffold. It helped me reconcile the supplied TEMPO specification with the
pinned MIT-licensed VEMO mechanisms, find the circularity between readiness and
authority, design the contracts, implement the policy kernel, write adversarial
failure cases, dogfood the workflow against Understand Video, and audit the
release from a judge's perspective.

I kept one boundary explicit: GPT-5.6 could propose, critique, and generate
code, but it could never sign a warrant, create authority, manufacture a
passing receipt, or fill the human verdict. `submission/ai-usage.json` maps
those build-time contributions to inspectable files and tests. The released
demo makes no OpenAI API call and needs no credentials.

## Evidence, impact, and limits

TEMPO already changed one real workflow: my own Understand Video build. Three
preserved recovery/replay workspaces recorded repeated readiness and input
failures; one unsafe start-accounting failure revoked authority; after recovery
and a new human authorization, TEMPO recorded one valid start while the public
MVP was delivered.

That is process evidence from one founder and one downstream product, not
independent customer validation. I do not claim measured savings, production
signing, external notarization, or live OpenAI runtime use. A real pilot should
measure avoided implementation starts, decision-cycle time, time to the next
useful experiment, and budget or scope drift caught.

The broader opportunity is a shared decision trail for product, research,
finance, engineering, agencies, and security reviewers before an increasingly
fast coding agent spends the next unit of time or budget.

## Links and version boundary

- Competition repository: https://github.com/vemodalen-x/TEMPO
- Supporting downstream proof: https://github.com/vemodalen-x/understand-video
- Video: https://youtu.be/3eIxgVo9z4I
- CI: https://github.com/vemodalen-x/TEMPO/actions/workflows/ci.yml

The video explains the public `4a73350` graph baseline. The executable hardening
baseline is `0edefe3`; later public commits add judge-facing documentation and
release sanitization without changing the governed journey. GitHub `main` and
green CI are authoritative for the final code.

Category: **Work & Productivity**

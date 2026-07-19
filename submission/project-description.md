# TEMPO — Devpost project description

## Tagline

Turn “should we build?” into a testable, human-authorized workflow before coding agents spend the budget.

## Inspiration

Coding agents made implementation dramatically faster, but they did not make the decision to build any clearer. A team can now produce an MVP before it has agreed on the user, the riskiest assumption, the evidence threshold, the budget, or the condition that should stop the work. That is fast execution in the wrong direction.

I built TEMPO for the person supervising that work: a founder, product lead, or innovation owner who needs the speed of coding agents without turning a promising chat into unlimited authority.

## What it does

TEMPO is a deterministic business-to-MVP governance workflow. It turns a product question into a reviewable sequence:

1. A planning provider proposes an opportunity, business model, ranked hypothesis, and cheapest useful experiment. TEMPO treats all provider and model output as untrusted advice.
2. Evidence is checked for declared provenance, freshness, directness, measurements, and counterevidence. Hard blockers run before scoring.
3. Readiness produces either an actionable next experiment or eligibility for a human decision. Eligibility never grants implementation authority.
4. A separate, time-bounded human warrant binds the assessment, evidence manifest, charter, scope, lane, action, budget, deadline, and repository subject.
5. Every implementation start is checked against that warrant. Out-of-scope work, drift, expiry, revocation, or an unmatched start fails closed.
6. A serialized hash-chained ledger, durable checkpoint, verification receipts, and a verdict memo make the result inspectable. The final human verdict remains blank until a human signs it.

The result is useful even when the answer is “not yet”: TEMPO names the failed condition and the next experiment instead of returning a vague denial.

## How we built it

The working vertical slice is a dependency-light Python 3.10+ CLI with JSON Schema contracts, deterministic state transitions, local file/action guards, evidence checks, authorization and revocation, receipt generation, and a credential-free judge demo. GitHub Actions runs the suite on Windows, macOS, and Linux and also runs a digest-pinned, unprivileged, network-disabled judge container.

The final hardening pass addressed two subtle integrity failures. New human warrants now use a V2 subject digest bound to the exact Git origin, revision, commit, worktree, Git directory, and common directory; only explicit demo fixtures may use a non-Git subject. Ledger appends now roll back the exact fsynced event if checkpoint replacement fails, while a rollback that cannot be proved safe stays fail-closed. Failure-injection tests cover first append, existing history, late filesystem errors, rollback failure, origin changes, commit changes, branch changes, and a second worktree.

TEMPO and the supporting product are deliberately independent repositories. [Understand Video](https://github.com/vemodalen-x/understand-video) is a downstream code-explanation pipeline built under TEMPO’s controls. It is evidence that the framework can govern a real product without importing or coupling the product code into TEMPO.

## How we used Codex and GPT-5.6

Codex Desktop with GPT-5.6 in Sol Ultra mode was the primary engineering environment. It was used materially to inspect and reconcile the supplied TEMPO specification and the pinned MIT-licensed VEMO mechanisms, identify the circularity between readiness and authority, design deterministic contracts, implement the policy kernel, create adversarial failure tests, dogfood the framework against Understand Video, and prepare the judge journey.

GPT-5.6 is not a hidden runtime dependency. The released demo makes no OpenAI API call and needs no credentials. Recorded provider JSON is visibly labeled as fixture data. The file `submission/ai-usage.json` maps the build-time contributions to inspectable repository artifacts.

## Challenges

The hardest design problem was preventing a system from authorizing itself. A high score or a model recommendation can say that an MVP looks worthwhile, but neither should be allowed to spend money or modify product code. TEMPO therefore separates readiness, human warrant, and exact implementation start into three independently checked facts.

The second challenge was making local evidence honest. A hash chain alone does not prove that its tail was not removed, so TEMPO adds a durable head checkpoint. A checkpoint alone is still not external notarization, so the documentation says exactly that. The demo signer proves mechanics only and cannot be mistaken for production identity.

## Accomplishments

- One credential-free command demonstrates model advice, insufficient evidence, readiness without authority, blocked start, bounded start, scope denial, terminal drift, ledger verification, and a blank human verdict.
- Provider recommendations and model-generated synthesis cannot create authority or satisfy the external-evidence requirement.
- Stable exit codes distinguish pass, policy block, checker failure, and warning.
- Repository identity and append failure modes have direct cross-platform regression coverage.
- A separate downstream product proves the framework can govern useful delivery without repository coupling.
- The project makes no claim of measured customer savings, production signing, live OpenAI runtime use, or external notarization.

## Potential impact

The first audience is product and innovation leads repeatedly handing ambiguous initiatives to coding agents. TEMPO can also give founders, research, finance, engineering, agencies, and security reviewers one shared decision trail. A real pilot would measure avoided implementation starts, decision-cycle duration, time to identify the next experiment, and budget or scope drift caught. Those outcomes remain testable hypotheses rather than invented results.

TEMPO has already changed one real internal workflow. Three preserved
single-founder workspaces from the independent Understand Video build recorded
repeated readiness/input failures. One unsafe start-accounting failure revoked
authority; after recovery and a new human authorization, TEMPO recorded one
valid start and 38 bounded exact-path lease rotations while the public MVP was
delivered. The repository case study publishes the derived counts, source
ledger hashes, product commits, and limitations. Because the workspaces include
recovery and replay, these are not independent business decisions or unique
work items, and they do not establish customer value or measured savings.

## Try it

```bash
git clone https://github.com/vemodalen-x/TEMPO.git
cd TEMPO
python bin/tempo selfcheck
python bin/tempo demo
python bin/tempo verify --level all
```

For a browser-first review, serve only the demo directory and open the
bilingual audit console:

```bash
python -m http.server 8000 --bind 127.0.0.1 --directory demo
```

Then visit `http://127.0.0.1:8000/audit-console.html`. The console is a read-only
interaction prototype backed by an explicitly synthetic, hash-chained fixture;
it cannot read live authority or authorize work. Its fixture and browser
contracts are independently verified by `demo/verify-audit-console.py` and
`demo/verify-audit-console-browser.py`.

Repository: [github.com/vemodalen-x/TEMPO](https://github.com/vemodalen-x/TEMPO)

Supporting downstream proof: [github.com/vemodalen-x/understand-video](https://github.com/vemodalen-x/understand-video)

Video: [youtu.be/3eIxgVo9z4I](https://youtu.be/3eIxgVo9z4I)

The video demonstrates the public `4a73350` graph baseline, including the
bilingual audit console. The verified TEMPO release `7d320b5` adds V2
Git-subject binding and ledger failure-atomicity hardening without changing the
governed journey shown in the video. The repository and green CI are
authoritative for the final code.

Category: **Work & Productivity**

# OpenAI Build Week submission checklist

Status: **submitted and read-back confirmed**. This file records
packaging evidence; the repository owner's current instruction authorizes the
final Devpost submission only after the release checks pass.

Authorities: [hackathon page](https://openai.devpost.com/),
[rules](https://openai.devpost.com/rules),
[resources](https://openai.devpost.com/resources), and
[FAQ](https://openai.devpost.com/details/faqs). Re-check them immediately before
submission in case the organizer changes a requirement.

Deadline recorded on 2026-07-17: **2026-07-22 00:00 UTC / 2026-07-21 17:00 PT /
2026-07-22 08:00 Singapore**.

## Hard blockers

- [x] Create the standalone remote repository and replace every
  `<repository-url>` placeholder.
- [x] Push the intended release commit and verify the public remote contents.
- [x] Make the repository public with `LICENSE`, or, if intentionally private,
  share it with `testing@devpost.com` and `build-week-event@openai.com` as
  specified by the current official FAQ.
- [x] Confirm clean-clone setup and the one-command demo on an environment that
  did not build the project.
- [x] Run the complete test/verification suite and inspect tool-generated
  receipts; do not type a receipt or passing status manually.
- [x] Confirm the CI judge-container job passes with the configured digest,
  unprivileged UID, and network disabled.
- [x] Run `/feedback` in the primary Codex task. Confirm the returned value,
  then update `submission/session.json` and the Devpost field. Candidate task:
  `019f6fc9-488b-7be0-9cff-2e9bfbd7a19f`.
- [x] Document material GPT-5.6 build-time contributions and the no-live-runtime
  boundary in `submission/ai-usage.json`, the project description, and video
  script.
- [x] Record a demo with audio, keep the final cut under three minutes, upload
  it to YouTube, set visibility to unlisted or public, and test playback in a signed-out
  browser.
- [x] Record in English or provide the organizer-required English translation.
- [x] Asset audit found no music or external images/logos in the final video;
  visuals use synthetic shapes and system fonts, and the organizer explicitly
  permits AI voiceover. Retaining any applicable voice-provider authorization
  remains an owner obligation.
- [x] Replace all video URL placeholders and confirm the link resolves.
- [x] Repository and video were judge-accessible at submission and final
  read-back. Continued accessibility through judging is tracked below as an
  ongoing owner obligation rather than a one-time packaging check.
- [x] Submit as an individual with Singapore as country of residence; no
  additional team member is listed.
- [x] Repository owner delegated the final description, category, repository,
  video, access, session ID, and claim review in the current submission task.
- [x] Obtain explicit authority for the external Devpost submission action.

## Stage 1 viability

- [x] Category selected: **Work & Productivity**.
- [x] Problem framed as cross-functional workflow productivity, not only a
  developer control.
- [x] Working-project design uses Codex as the build environment.
- [x] Document meaningful GPT-5.6 use from the primary Codex build task.
- [x] Confirm the public repository and judge-accessible video are accessible to judges.
- [x] Confirm the Devpost project includes the required description and category.

## Repository package

- [x] MIT license present.
- [x] README includes setup, run, sample/demo, architecture, security, and the
  OpenAI-provider truth boundary.
- [x] Source lineage and third-party notice present.
- [x] Work & Productivity and judging alignment documented.
- [x] Credential-free demo instructions present.
- [x] Security, sandbox, and traceability documents present.
- [x] All automated tests pass on supported host platforms.
- [x] No secrets, credential paths, private course material, source archives,
  build caches, or generated demo workspaces are committed.
- [x] `git status`, tracked-file list, and public remote contents match the
  intended submission scope.
- [x] Replace the remaining video placeholder and remove no longer relevant
  draft notes.

## Video content

- [x] The 140-second cut opens with the work problem and explains TEMPO's
  evidence, readiness, authorization, denial, ledger, and verdict journey.
- [x] The cut includes audio, safe-area English captions, real terminal output,
  and an explicit fixture/local-integrity claim boundary.
- [x] Codex and GPT-5.6 build-time use is stated in the cut and mapped concretely
  to artifacts in `submission/ai-usage.json` and the Devpost description.
- [x] The cut does not claim live API use, production signing, real customer
  validation, measured savings, deployment, or external attestation.

Presentation trade-off: the published cut uses a compact slide-led explanation
and a downstream governed-product terminal example rather than showing every
literal CLI state. The README's 60-second path and `python bin/tempo demo` are
the authoritative executable proof for `EXPERIMENT_REQUIRED`, readiness while
`build_allowed: false`, bounded start, and drift denial.

## Devpost fields

- [x] Draft project name: TEMPO.
- [x] Draft tagline and full description prepared.
- [x] Category: Work & Productivity.
- [x] Final repository URL.
- [x] Final judge-accessible YouTube URL.
- [x] Confirmed `/feedback` session ID.
- [x] Precise Codex/GPT-5.6 build-time usage statement drafted and mapped to
  repository artifacts.
- [x] Team/member information and organizer-required submission fields completed.
- [x] Final project read back after submission with repository, video, category,
  and OpenAI Build Week association intact.

## Submission receipt

- Project ID: `1350574` (`TEMPO`; legacy URL slug `understand-video`).
- Submission ID: `1103781`.
- Submitted at: `2026-07-19T04:30:16.341Z`.
- Live URL: <https://devpost.com/software/understand-video>.
- The separate empty project `1351822` remains an unsubmitted pre-draft.

## Final command pass

Run from a clean clone and retain actual outputs/receipts:

```bash
python bin/tempo context
python bin/tempo selfcheck
python bin/tempo demo
python bin/tempo verify --level all
python bin/tempo ledger verify
python bin/tempo submit-check
```

Future accessibility is an ongoing owner obligation and remains unchecked until
the judging period ends.

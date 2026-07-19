# Understand Video single-founder dogfood

TEMPO was used on one real downstream build, not only on its synthetic judge
fixture. The subject was
[`vemodalen-x/understand-video`](https://github.com/vemodalen-x/understand-video),
an independent code-to-video product. This is internal process evidence from
one repository owner; it is not an independent customer pilot or a claim of
measured productivity savings.

## Observed control sequence

Three preserved governance workspaces capture preflight, canonical, and
recovery attempts. They include recovery and replay, so the counts below must
not be read as independent business decisions or unique work items.

| Preserved workspace | Events | Readiness blocks | Human authorization events | Operational result |
| --- | ---: | ---: | ---: | --- |
| Preflight, later identified as misattributed | 13 | 7 | 0 | No implementation start |
| Canonical | 16 | 4 | 1 | Authority revoked after `START_LEDGER_SCHEMA_FAILURE` |
| Recovery | 50 | 2 | 1 | One valid start and 38 exact-path lease rotations |

The recovery task bound one repository owner, a `$25` budget cap, the
`video-core` lane, and explicit code, test, build, media, and documentation
paths. The public outcome is inspectable in the downstream repository:

- [`8617fd0`](https://github.com/vemodalen-x/understand-video/commit/8617fd0530d21dbe37283b62ee249c9f71b3683c)
  added the governed MVP and 54-case acceptance suite;
- [`7b6edf5`](https://github.com/vemodalen-x/understand-video/commit/7b6edf54602ecbc5d3bf2e0beed6b74cf8ce0c3f)
  added the working TEMPO explanation and media evidence; and
- [`4b1d526`](https://github.com/vemodalen-x/understand-video/commit/4b1d5267ace67d99043305e9b1e610a71bff0ff7)
  is the public main revision read back for this case.

The MVP change from its product-only base to `8617fd0` contained 8,816 added
lines across 83 files. Size is not presented as value; it establishes that the
governed subject was a nontrivial implementation rather than a documentation
toy.

## What this demonstrates

The internal case supports three narrow claims:

1. repeated readiness/input failures prevented an implementation start;
2. an unsafe start-accounting failure caused authority to be revoked instead
   of being converted into a pass; and
3. after recovery and a new human authorization, TEMPO admitted one start and
   preserved 38 bounded lease rotations across the declared product paths.

This is the behavior TEMPO is designed to change: not whether an agent can
write code, but whether the current decision, authority, task, path, lane, and
action permit that write now.

## Evidence and limitations

The machine-readable derived record is
[`docs/evidence/understand-video-dogfood-summary.json`](evidence/understand-video-dogfood-summary.json).
It includes the three source-ledger SHA-256 values, counts, public product
commits, and claim boundary.

The original source ledgers remain local and unpublished so the downstream
product repository stays independent of the governance workspace. Their hashes
make this derived summary stable, but a public reader cannot independently
replay those private ledgers. The dogfood also used earlier TEMPO baselines
(`4afc6a3` and the `4a73350` product target), not the final `7d320b5` release.
Understand Video's media receipts are explicitly fixture-mode and
`authoritative: false`; they are not treated as authoritative TEMPO receipts.

No customer demand, adoption, time saving, avoided cost, or causal product
impact is inferred from this case. Those outcomes still require an independent
pilot.

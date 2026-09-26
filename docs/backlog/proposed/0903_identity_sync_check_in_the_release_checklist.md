# 0903 — Run `scripts/check_identity_sync.py` as a release-checklist step (recurrent), not in CI

> Package: abstractframework (scripts/check_identity_sync.py, docs/backlog/recurrent/, abstract-release skill)
> Type: task
> Created: 2026-09-26
> Priority: normal
> Labels: release, identity, tooling, recurrent

## Summary

The canonical About descriptor `identity/abstractframework.json` is vendored byte-for-byte into four
sibling repos (abstractcore, abstractuic ui-kit, abstractcode TUI, abstractgateway console-TUI).
`scripts/check_identity_sync.py` (strict by default, compares bytes, root `3bc1de7`) catches drift,
but no CI runs it: it needs the sibling checkouts side by side, which only the monorepo workspace
has. Instead of forcing it into CI, make it a named step of the release checklist: a recurrent task
under `docs/backlog/recurrent/` plus a line in the `abstract-release` skill's pre-publish gates.

## Why

CONTRACTS A-5 made the script strict; the About track (B/U reports) vendored the copies. A root CI job
would fail on a lone checkout, and per-repo CI cannot see the canonical file. Drift would ship
silently between waves.

## Current code reality (2026-09-26; root `3bc1de7`)

- `scripts/check_identity_sync.py`: `CANONICAL = ROOT/identity/abstractframework.json`;
  `KNOWN_COPIES` = the four sibling paths; `--lenient` only reports missing copies.
- `.github/workflows/ci.yml`, `release.yml` (root): no reference to the script (grep 2026-09-26);
  no sibling repo workflow references it either.
- `docs/backlog/recurrent/` holds two tasks (hygiene, follow-up triage); no release-checklist task.
- abstractcore `f23e142` pins its vendored copy's sha256 in a test (REVIEW/07 R2 follow-up), which
  covers one copy only.

## Scope

### In scope

- New recurrent task (e.g. `recurrent/release-wave-gates.md`) listing the monorepo-only gates, first
  of all `python3 scripts/check_identity_sync.py`; link it from `recurrent/README.md` and the overview.
- A line in the `abstract-release` skill's gates (operator-owned skill; propose the edit).

### Out of scope

- Moving the check into any CI.

## Dependencies

- None.

## Expected outcomes

- Every release wave runs the check before publishing; a drifted copy blocks the wave.

## Acceptance criteria

- [ ] Recurrent task exists and is indexed; the next release record cites its run.
- [ ] Deliberate break: alter one vendored copy by a byte → the script exits non-zero.

## Validation

- `python3 /Users/albou/tmp/abstractframework/scripts/check_identity_sync.py; echo $?`

## Evidence

- `untracked/missions-2026-09-25/CONTRACTS.md` (B, A-5)
- `untracked/missions-2026-09-25/B/REPORT.md` (parity fix), `untracked/missions-2026-09-25/U/REPORT.md`
- `untracked/missions-2026-09-25/REVIEW/02-about-track.md`, `REVIEW/07-xa-recheck.md` (R2)

## ADR status

- ADR impact: None.

## Receipts

- None yet.

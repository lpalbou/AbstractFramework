# 0902 — abstractskill: bundle pin history, a wheel-content test in CI, and the stale refresh_shelf pin

> Package: abstractskill (tests/test_bundled.py, .github/workflows/ci.yml, scripts/refresh_shelf.py)
> Type: improvement
> Created: 2026-09-26
> Priority: normal
> Labels: skills, packaging, ci

## Summary

abstractskill 0.3.0 (unreleased, `eafc62e`) ships the curated registry inside the wheel and pins its
content with one `(PINNED_VERSION, PINNED_DIGEST)` pair. Three gaps: (1) a contributor can update the
digest without bumping the bundle version, so two different bundles can carry the same version —
the thing `seed_registry`'s upgrade logic relies on; (2) nothing in CI checks that the built wheel
contains exactly the tracked registry files (checked by hand in REVIEW/01); (3)
`scripts/refresh_shelf.py` pins `entity-self-knowledge` at a tree hash that no longer matches the
registry (pre-existing).

## Why

REVIEW/01 S7 and REVIEW/07 ("S7 … OPEN (should-fix) for the release step"); X-a report
("refresh_shelf.py pin for entity-self-knowledge stale (pre-existing)").

## Current code reality (2026-09-26; abstractskill `eafc62e`)

- `tests/test_bundled.py` l.41–42 `PINNED_VERSION = "2026.09.25"`, `PINNED_DIGEST = "61d8b95a…"`; l.86
  asserts the pair — no `{version: digest}` history.
- `.github/workflows/ci.yml` l.40–48: `python -m build` + `twine check`; no wheel-content assertion.
- `scripts/refresh_shelf.py` l.105–106: `entity-self-knowledge` `expected_tree_hash 08cdb23c…`;
  `src/abstractskill/registry/validations.yaml` l.266–268: `tree_hash 7e6fc34a…`.
- REVIEW/07 S4 partial: after a lost manifest, items from an OLDER bundle are never refreshed
  (labelled `kept_unknown_provenance`); per-version item hashes would fix it and share (1)'s history.

## Scope

### In scope

- A checked-in `{bundle_version: digest}` (and per-item hash) history; the test fails when the digest
  changes without a new version and when a version repeats.
- CI step: build the wheel, list `abstractskill/registry/**`, compare with `git ls-files`.
- Refresh the `entity-self-knowledge` pin (or derive it from validations.yaml) and test that every
  refresh_shelf pin equals the registry's `tree_hash`.

### Out of scope

- Registry content changes; gateway shelf behaviour.

## Dependencies

- abstractskill 0.3.0 release (gateway requires `abstractskill>=0.3.0`).

## Expected outcomes

- A bundle version always identifies one content; the wheel provably ships the registry.

## Acceptance criteria

- [ ] Deliberate break: change a SKILL.md without bumping → test red; bump → green.
- [ ] CI fails when a registry file is dropped from the wheel.
- [ ] `refresh_shelf.py` pins match `validations.yaml` (test).

## Validation

- `python -P -m pytest abstractskill/tests` (scratch HOME); `python -m build` in a clean copy
  (not the in-tree stale `build/`, REVIEW/01 N5).

## Evidence

- `untracked/missions-2026-09-25/Xa/REPORT.md` (Open; Review fixes "Not done")
- `untracked/missions-2026-09-25/REVIEW/01-xa-abstractskill.md` (S7, N5)
- `untracked/missions-2026-09-25/REVIEW/07-xa-recheck.md` (S4 partial, S7 open)

## ADR status

- ADR impact: None.

## Receipts

- None yet.

# 0907 — Curated skills ship inside abstractskill and the gateway seeds its shelf from them

> Package: abstractskill (0.3.0, unreleased); abstractgateway (skills shelf); abstractcode (web + TUI skills views)
> Type: feature
> Created: 2026-09-26
> Completed: 2026-09-26
> Priority: high
> Labels: skills, gateway, packaging, mission-wave-2026-09-25, unreleased

## Summary

Completed record for missions X-a and X-b of the 2026-09-25/26 wave (committed locally, not
released; release staged, waiting for the operator's go). The curated skill registry now lives in
the `abstractskill` wheel, a public seed API copies it into a shelf without overwriting operator
edits, and the gateway seeds `<data>/skills/registry` at service start, so a fresh install has
skills without a source checkout.

## Why

Operator request, as recorded by the orchestrator (`PLAN.md`, track X-a): "ship skill registry in
the abstractskill wheel + seed API"; X-b (gateway skills shelf) was part of mission G1. Before the
wave the gateway only found skills in a developer checkout.

## What landed

- **abstractskill** `bed8410`: registry moved into `src/abstractskill/registry/` (one copy; wheel
  ships 48 files: 14 skills, 4 yaml, 2 licenses); `abstractskill.bundled` with
  `bundled_registry_dir()`, `bundled_registry_version()` (catalog `2026.09.25`, digest-pinned by a
  test) and `seed_registry(dest) -> SeedReport`. Version 0.3.0. `eafc62e` (review fixes): exclusive
  `<dest>/.seed.lock` for the whole call and per-call staging names; a failed swap restores the old
  folder; an older bundle never replaces a newer seed (`kept_newer`); dropped skills reported
  `not_in_bundle`, never deleted; unknown manifest schema → `SkillError`; kept reasons split.
  Docs `08226a3`, llms generator with `--check` `0088e0e`.
- **abstractgateway** `5be07b0`: `skills.shelf` resolution stored > legacy env > seeded
  `<data>/skills/registry` > checkout; a wrong stored/env value is "unavailable" with a reason, no
  fall-through; seed once at service start; `POST /admin/skills/reseed`; `/skills` reports
  `shelf_source` and `bundled_version`; three doors (CLI, console "Refresh the curated shelf", TUI
  form); dependency `abstractskill>=0.3.0`. `e441a2c`: console Skills block always shows bundled
  version + count.
- **Clients**: Code web `c83a82b` and TUI `643a79f` show shelf, source and warnings when the shelf is
  empty.

## Completion report

- Tests: abstractskill 211 → 221 passed (4-process seed test passes 20/20, fails 5/5 without the
  lock); gateway suite green at the G1 final (2350 passed); hermetic gateway 18852 `/skills` seeded 14.
- Reviews: REVIEW/01 ACCEPT-WITH-FIXES (B1 concurrent seeds corrupted the shelf in 15/15 trials and
  froze truncated skills as "operator content"; B2 a failed directory swap deleted the skill; B3
  contract names; B4 moving the registry removed the gateway's current shelf until G1 landed) →
  REVIEW/07 (a) ACCEPT after `eafc62e`. CONTRACTS amended to the shipped names
  (`abstractskill.bundled`, `previous_version`).
- Release order: abstractskill 0.3.0 must publish before the gateway (STAGING step 1).
- Follow-ups: digest history per version, a wheel-content CI check and the stale
  `entity-self-knowledge` pin in `scripts/refresh_shelf.py` →
  [0902](../proposed/0902_abstractskill_bundle_pin_history_wheel_test_and_refresh_pin.md).
- ADR state: none.

## Receipts

- `untracked/missions-2026-09-25/Xa/REPORT.md`, `G1/REPORT.md` (5be07b0), `G2/REPORT.md`, `CD/REPORT.md` (abstractskill rows)
- `untracked/missions-2026-09-25/REVIEW/01-xa-abstractskill.md`, `07-xa-recheck.md`

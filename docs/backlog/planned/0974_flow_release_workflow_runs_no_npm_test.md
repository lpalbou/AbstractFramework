# 0974 — AbstractFlow: the release workflow publishes without running the npm tests

> Package: abstractflow (.github/workflows/release.yml)
> Type: task
> Created: 2026-09-28
> Priority: normal
> Labels: ci, release, tests

## Summary

Flow's CI runs vitest and the smokes, but `release.yml` builds and publishes without running `npm test`, so a tag can publish a build whose tests fail.

## Why

Ledger: "flow release.yml no npm test" (apps gate).

## Current code reality (2026-09-28)

- `abstractflow/.github/workflows/release.yml` (flow 0.4.0 head `d59b6b0`) has no `npm test` / vitest step.

## Scope

### In scope

- Run the same test job as CI before publish, or require the CI run for the tagged commit.

### Out of scope

- Changing the smokes.

## Acceptance criteria

- [ ] A failing test blocks the publish job.

## Validation

Workflow review; a deliberately failing test on a branch run.

## Receipts

- Source: `untracked/wave2/PLAN.md` (wave-2 ledger); root staging note `untracked/wave2/stage-root.md`.

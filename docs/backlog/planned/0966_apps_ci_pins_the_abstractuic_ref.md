# 0966 — Apps CI checks out a pinned AbstractUIC ref, not the default branch

> Package: abstractflow, abstractcontinuum, abstractentity (CI workflows)
> Type: task
> Created: 2026-09-28
> Priority: normal
> Labels: ci, reproducibility, abstractuic

## Summary

Flow, Continuum and Entity CI and release workflows clone AbstractUIC's default branch to build against its source packages. A release then builds against whatever AbstractUIC main holds at that moment, not the kit version it was tested with. The Observer already pins `v0.1.15`.

## Why

Ledger: "CI clones AbstractUIC default branch (pin ref)" (apps gate) and observer "CI pins uic v0.1.15".

## Current code reality (2026-09-28)

- `abstractflow/.github/workflows/ci.yml:22` and `release.yml:32,122`: `git clone --depth 1 https://github.com/lpalbou/AbstractUIC.git`; Continuum `ci.yml:30`, `release.yml:31` check out `lpalbou/AbstractUIC` without a ref.

## Scope

### In scope

- Pin a tag (one variable per workflow), bumped with the kit floor.

### Out of scope

- Changing how apps consume the kit.

## Acceptance criteria

- [ ] Each app's CI and release name the AbstractUIC tag they build against.

## Validation

`grep -n AbstractUIC .github/workflows/*.yml` shows a ref in each.

## Receipts

- Source: `untracked/wave2/PLAN.md` (wave-2 ledger); root staging note `untracked/wave2/stage-root.md`.

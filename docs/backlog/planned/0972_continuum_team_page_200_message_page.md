# 0972 — Continuum: the team page loads at most 200 messages

> Package: abstractcontinuum
> Type: task
> Created: 2026-09-28
> Priority: low
> Labels: adr-0026, continuum, paging

## Summary

Continuum's team page fetches messages with `PAGE_LIMIT = 200`. Under ADR-0026 a view may page, but it must not silently hide older messages: the page needs a working "load earlier" path or a stated window.

## Why

Ledger: "continuum analyst 200-msg page" (apps gate).

## Current code reality (2026-09-28)

- `abstractcontinuum/src/ui/team_page.tsx:76` `const PAGE_LIMIT = 200;` (continuum 0.4.0).

## Scope

### In scope

- Load earlier messages on demand, or show that older ones exist.

### Out of scope

- The analyst transcript window (done in 0.4.0).

## Acceptance criteria

- [ ] A channel with more than 200 messages shows all of them on demand.

## Validation

UI test with 250 messages.

## Receipts

- Source: `untracked/wave2/PLAN.md` (wave-2 ledger); root staging note `untracked/wave2/stage-root.md`.

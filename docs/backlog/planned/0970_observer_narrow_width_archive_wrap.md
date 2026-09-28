# 0970 — Observer: the automation row's Archive control wraps at narrow widths

> Package: abstractobserver (Automations page)
> Type: task
> Created: 2026-09-28
> Priority: low
> Labels: ui, layout, observer

## Summary

On the Observer's Automations page at narrow widths, the Archive icon button at the end of a row wraps onto its own line, breaking the row layout that Observer 0.2.0 made compact.

## Why

Observer UX gate, wave 2 (2026-09-28).

## Current code reality (2026-09-28)

- Observer 0.2.0 (`541fb1e`): Archive is the icon at the end of a row.

## Scope

### In scope

- Keep the row's action group on one line (or collapse into a menu) at narrow widths.

### Out of scope

- Other layout changes.

## Acceptance criteria

- [ ] At phone width the row stays one visual unit (screenshot).

## Validation

Playwright screenshot at 400 px width.

## Receipts

- Source: `untracked/wave2/PLAN.md` (wave-2 ledger); root staging note `untracked/wave2/stage-root.md`.

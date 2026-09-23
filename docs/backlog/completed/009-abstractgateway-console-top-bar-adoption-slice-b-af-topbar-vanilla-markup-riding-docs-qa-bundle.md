# 009-abstractgateway: [TASK] Console top-bar adoption (slice b): .af-topbar vanilla markup riding docs-qa bundle

> Package: abstractgateway
> Type: task
> Created: 2026-07-14 05:55:55 +0200
> Priority: P2
> Labels:

## Summary
The server-rendered gateway console adopts the shared .af-topbar markup (assistant drawer, theme, disconnect) so its assistant drawer rides the published docs-qa@0.1.0 bundle, grounded on the console's own llms.txt.

## Why

Slice a (the docs-qa bundle) shipped + live-proven 2026-07-14 (c2103: grounded, cited, honest-gap answer). Slice b is the remaining half of uic's c1648 ask — the console is the last app without the unified top-right cluster.

## Scope

### In scope

- Console pages render the shared .af-topbar cluster (vanilla markup, no React dependency)
- Console assistant drawer answers via docs-qa@0.1.0 grounded on the console's llms.txt
- uic conformance check

### Out of scope

- Rewriting the console as a SPA
- Changes to the docs-qa bundle contract (published, versioned)

## Acceptance criteria

- [x] Top-bar renders on console pages in both themes (gateway SHIP c2118; agency live-probe c2120: served /console HTML carries .af-topbar cluster + drawer markup)
- [x] One live drawer Q&A run through docs-qa@0.1.0 with ledger receipt (slice a run b7a37c59, c2103; drawer transport live-verified c2118/c2120)
- [x] uic co-sign recorded (c2122: CONFORMANT — class families, contract order, keep-alive drawer, a11y all verified line-by-line)

ALL ACCEPTANCE MET 2026-07-14 06:10 — ready for continuum to promote to completed.

PROMOTED 2026-07-14 06:18 +0200 by continuum (supervisor): acceptance receipts verified (c2118 ship, c2120 agency live probe, c2122 uic conformance), moved planned/ → completed/.

Follow-through beyond scope (same claim, gateway): docs-qa consumer contract documented in docs/api.md + corpus packaged into the wheel (c2125, 696 green). Named design question spun out, NOT part of this card: auto-publishing shipped bundles into the tenant catalog at boot (fresh installs see an honest "Bundle not found" until an admin publishes; one curl, documented).

## Receipts

- Slice a receipt: commons c2103 (docs-qa@0.1.0, run b7a37c59)
- Slice b SHIP: c2118; agency live co-sign: c2120; uic conformance: c2122; packaging follow-through: c2125
- uic ask: c1648; unified top-bar plan: commons fs plans/unified-top-bar.md

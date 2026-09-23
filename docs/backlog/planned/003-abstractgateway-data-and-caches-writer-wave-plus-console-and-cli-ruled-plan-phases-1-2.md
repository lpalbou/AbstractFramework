# 003-abstractgateway: [FEATURE] Data and Caches writer wave plus console and CLI (ruled plan phases 1-2)

> Package: abstractgateway
> Type: feature
> Created: 2026-07-13 19:57:22 +0200
> Priority: normal
> Labels: wave-data-caches, seat-gateway

## Summary
Register every gateway-owned data home at boot (runs, ledgers, artifacts, entity homes safe_to_purge=false, logs, workspaces, dev) using core's ensure-lane; then the one management surface: GET /admin/data-homes, purge with dry-run-first UX, CLI parity. Core's half DONE (blocs 563GB and repl-sessions 30GB registered after agency's gap find). Receipts: hub fs plans/data-caches-console.md, hub c1580/c1608/c1616/c1622. Labels: wave-data-caches, seat-gateway.


(1 paragraph: what this item is and why it matters. For operator DECISION GATES,
open with "OPERATOR DECISION GATE (never assignable):" and carry the
`decision-gate` label — gate cards are non-draggable/non-executable on the
continuum board by structural rule.)

## Why

(The problem or directive this answers. Quote operator rulings verbatim.)

## Scope

### In scope

-

### Out of scope

-

## Acceptance criteria

- [ ] (per-seat receipts for waves: "- [ ] <seat>: <what> (<message id>)")

## Receipts

- (hub message ids, board rows, decision-store keys, evidence paths)

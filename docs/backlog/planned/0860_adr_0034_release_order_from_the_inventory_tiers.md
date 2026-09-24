# 0860 — ADR-0034: replace the release order list with the inventory tiers

> Package: abstractframework (docs/adr/0034-framework-release-sequence-and-gates.md)
> Type: task
> Created: 2026-09-23
> Priority: low
> Labels: adr, release

## Summary

ADR-0034's Standard Order list still places AbstractRuntime in Tier 1 and treats AbstractCode as a
Python package. `scripts/lib/packages.txt` is now the authoritative dependency inventory
(`scripts/deps.sh` prints the tiers, `deps.sh check` validates them) and the ADR only carries an
"Updated" note saying so. Revise the ADR so its order is the tier table (Python, npm and Rust,
including `abstractcore-console` at tier 1 and `abstractgateway-console` at tier 2) or a pointer to
`deps.sh`, with no second list that can drift.

## Acceptance criteria

- [ ] ADR-0034 revised (or superseded) with no hand-maintained package order.
- [ ] `abstract-release` skill references the same source.

## Status update 2026-09-25 (post-release trace)

Still open: the ADR's "Standard Order" still lists abstractcore and abstractruntime together in
Python Tier 1, while the 2026-09-24 patch wave had to run core 2.15.1 → runtime 0.4.34 (runtime
floors core>=2.15.1) → gateway 0.4.2 → root 0.3.1. The ADR's own 2026-09-23 "Updated" note points
at `packages.txt` / `deps.sh`, so the document contradicts itself. Related: 0871 (planner scratch
discovery), 0867 (release trace).

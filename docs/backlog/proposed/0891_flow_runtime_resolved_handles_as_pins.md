# 0891 — AbstractFlow: draw runtime-resolved handles as real pins (root pointer to abstractflow 0157)

> Package: abstractflow (owner of the work: `abstractflow/docs/backlog/proposed/0157_runtime_resolved_handles_as_pins.md`)
> Type: improvement
> Created: 2026-09-26
> Priority: normal
> Labels: flow, editor, pointer

## Summary

Root-level pointer, not a second copy: the work is specified in AbstractFlow's own backlog item
`abstractflow/docs/backlog/proposed/0157_runtime_resolved_handles_as_pins.md` (operator ruling on
REVIEW/14: badge now, pins later). 336 stored connections in 24 shipped flows wire handles the
editor cannot draw (code-node dict keys, a subflow's `child_output`). The interim is the persistent
"N hidden" badge per node (abstractflow `5f19d38`, `0df9c65`). This root item exists so the
framework overview shows the limitation and its owner.

## Why

REVIEW/14 F4: the canvas under-represents entity-chat (8 of 22 edges), coding-agent, deep-research,
diagram-render and the entity family; users cannot select or delete these connections one by one.

## Current code reality (2026-09-26; abstractflow `0df9c65`)

- `loadFlow` keeps undeclared-handle edges as `preservedEdges`, `getFlow` saves them back; the
  "N hidden" badge lists them; docs `web-editor.md` "Hidden Connections".
- abstractflow 0157 records the two constraints that make "declare the pin" unsafe
  (`child_output` overwritten by the `start_subworkflow` spread; reserved exec-lane keys).

## Scope

### In scope

- Track abstractflow 0157 to completion; close this pointer when 0157 closes.

### Out of scope

- Any duplicate specification here. Changes to runtime handle resolution (owned by 0157's runtime lane).

## Dependencies

- abstractflow 0157; abstractruntime for the `child_output` declaration bug.

## Expected outcomes

- Every preserved edge is visible and editable; the badge remains only for edges that still cannot be drawn.

## Acceptance criteria

- [ ] abstractflow 0157 moved to its `completed/` with receipts; this item then moved to root `completed/`.

## Validation

- `npm --prefix abstractflow test -- --exclude 'untracked/**'` (includes `src/hooks/loadFlowEdges.test.ts`).
- Load→save census over `examples/flows` + the bundled catalog loses 0 edges (REVIEW/14 probe method).

## Evidence

- `untracked/missions-2026-09-25/REVIEW/14-flow-edges.md` (F1–F4)
- `untracked/missions-2026-09-25/F/REPORT.md` (`82539eb`, `5f19d38 + 0df9c65`)

## ADR status

- ADR impact: None.

## Receipts

- None yet.

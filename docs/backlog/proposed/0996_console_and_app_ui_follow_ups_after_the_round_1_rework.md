# 0996 — Console and app UI follow-ups after the round-1 rework

> Package: abstractentity, abstractuic (monitor-active-memory), abstractobserver, abstractgateway (console + TUI), abstractcore (console), browser apps
> Type: task
> Created: 2026-10-01
> Priority: low
> Labels: follow-up, responsive, ui, tui

## Summary

Small follow-ups recorded by the round-1 console/UX rework (2026-09-30/10-01) that are not part of
the 0.8.0 wave's scope. Each line is independent; split one into its own item when it is picked up.

## Items

- Entity blueprint map: a phone layout (its SVG labels are map units and cannot be forced to 14 px without overlapping; today the map is a documented zoomable exception like the graph canvas).
- monitor-active-memory 0.2.2: `.amx-small` 14 px on touch (kit repo a713826) — republish and drop Observer's scoped override (`.runtime_memory_panel` in space.css).
- Gateway TUI: add a test that the "Signed in with a new token" status line is set after a successful sign-in code (today only the snapshot seeds it).
- Observer: phone landscape keeps the run panel's own scroll (accepted, revisit with a landscape layout).
- Gateway/core consoles: helper text 13 px on touch is a DESIGN §3 rule now — re-measure both consoles after the integration build.
- 00:16 B (integration review): apps still use their local https sentence; kit insecureContextReason() unused at the integration heads → one-line switch per app before release (A/whoever cuts the apps).

## Current code reality (2026-10-01)

Recorded against the integration heads of 2026-10-01 00:16; re-check each line against the 0.8.0
release heads before acting (the apps' https sentence in particular may be closed by the kit's
`insecureContextReason()` adoption in round 2).

## Acceptance criteria

- [ ] Each line closed with a test or a measurement, or moved to deprecated with the reason.

## Receipts

- `untracked/day-review/backlog/A-followups.md` (draft), `untracked/day-review/DESIGN.md` §3.

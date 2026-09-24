# Recurrent: Backlog and ADR hygiene

## Metadata
- Created: 2026-09-25
- Status: Recurrent
- Completed: N/A (runs repeatedly)

## Purpose
Keep the root backlog countable, searchable by ID and true to the code.

## Run conditions
After every release wave (the `abstract-release` trace step), after several agents worked in the
workspace, or monthly.

## Scope
`docs/backlog/**` and `docs/adr/**` links. Never code.

## Checklist
- [ ] Overview counts equal on-disk counts per lifecycle folder (nested tracks included).
- [ ] New files use unique four-digit `NNNN_` IDs; flag legacy violations into 0889 until it lands.
- [ ] No filename in two lifecycle folders.
- [ ] Sample planned items against the code; append a dated status note where stale.
- [ ] Items whose work shipped are moved to `completed/` with evidence (registry version, tag, report).
- [ ] Moved files: `grep -rn` for the old path (docs, scripts/gen_llms_full.py).
- [ ] ADRs contradicted by practice get a drift item (e.g. 0860).

## Expected output
A `backlog: …` commit and a dated line in the overview's planning notes.

## Non-goals
Implementing items; rewriting history.

## Last run
- 2026-09-25: post-release trace (0233 closed; 0863–0867 recorded; 0868–0889 created; 0889 opened
  for the legacy findings).

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
- 2026-09-26: after the 2026-09-25/26 mission wave (0906–0915 recorded; 0875 and 0900 closed).
  Counts recounted (planned 117, proposed 36, completed 234); new IDs 0890–0915 unique; legacy
  findings unchanged (four-digit reuse 0212–0214, 24 planned/completed duplicates, 230 non-`NNNN_`
  files → 0889). Drift flagged in the overview: 0872, 0874, 0884, 0888 look fixed by the unrecorded
  2026-09-25 patch wave.

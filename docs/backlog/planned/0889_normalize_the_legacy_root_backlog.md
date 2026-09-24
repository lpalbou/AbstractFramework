# 0889 — Normalize the legacy root backlog (stale planned copies, duplicate and non-four-digit IDs)

> Package: abstractframework (docs/backlog/**, scripts/gen_llms_full.py)
> Type: task
> Created: 2026-09-25
> Priority: normal
> Labels: backlog, hygiene

## Summary

The 2026-09-25 hygiene scan found the root backlog cannot be counted or searched by ID reliably:
24 items exist under the same filename in both `planned/` and `completed/` (035, 036, 041, 042,
043, 102–120: the stale planned copies were never removed); 231 item files lack a four-digit
`NNNN_` prefix (three-digit legacy names, `NNN-<package>-…` hub-era names, two date-prefixed
`2026-05-08_*` files); ~70 numeric IDs are reused (e.g. `001`–`018` by both legacy and hub-era
items; `0212`–`0214` by `planned/agency-parity/` and `proposed/`); `planned/agency-parity/` holds
items whose status is "Done (tested)"; `docs/backlog/fable-opinions/` is an unindexed folder.

## Current code reality (root at the 2026-09-25 trace)

- On-disk item counts (excluding README, overview, template, evidence): planned 116, proposed 23,
  completed 222, deprecated 0, recurrent 2 (the two process files added by this trace).
- `scripts/gen_llms_full.py` references ~30 backlog paths by name, including
  `planned/074_agent_skills_integration*.md`: any move must update or (better, 0883) remove those
  references in the same commit or the generator exits on the missing file.

## Scope

### In scope

- Delete the 24 stale planned copies after diffing each pair (keep the completed file; move any
  extra text into its completion report).
- Move Done items out of `planned/agency-parity/` with completion reports.
- Rename non-compliant files to fresh unused `NNNN_` IDs with a legacy-ID line inside each file
  (`Legacy ID: 074`), fix every link, and add a mapping table to the overview.
- Rename the two date-prefixed files; decide on `fable-opinions/` (index it or move it to `docs/`).

### Out of scope

- Re-triaging the content of legacy planned items (a separate pass per track).

## Acceptance criteria

- [ ] Every item file matches `^[0-9]{4}_` and every ID is unique across all lifecycle folders.
- [ ] No filename exists in two lifecycle folders.
- [ ] Overview counts equal the on-disk counts (scripted check).
- [ ] `python scripts/gen_llms_full.py` still runs.

## Testing

- `find docs/backlog -name "*.md" ! -name README.md ! -name overview.md ! -name template.md ! -path "*/evidence/*" ! -path "*/recurrent/*" | sed 's|.*/||' | grep -v -E "^[0-9]{4}_" | wc -l` (expect 0)
- `python scripts/gen_llms_full.py`

## ADR status

- ADR impact: None.

## Receipts

- Hygiene scan of this trace (see overview "Hygiene findings").

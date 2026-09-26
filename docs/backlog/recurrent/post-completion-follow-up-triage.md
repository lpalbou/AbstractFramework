# Recurrent: Post-completion follow-up triage

## Metadata
- Created: 2026-09-25
- Status: Recurrent
- Completed: N/A (runs repeatedly)

## Purpose
Residual risks named in completion reports, mission reports and release ledgers must become
backlog items or be recorded as intentionally dropped, so they do not live only in `untracked/`.

## Run conditions
After each completion report, release wave or docs pass.

## Scope
`docs/backlog/**`; reads `untracked/**` reports as evidence.

## Checklist
- [ ] List every "follow-up", "open", "operator must" and "known limit" line of the new reports.
- [ ] Classify: covered by planned / covered by proposed / doc-only / stale / new proposed / new
      planned (urgent or well understood).
- [ ] Create items standalone (evidence path, code reality, validation); link them from the
      completion record.
- [ ] Owner-only actions with no code change: list them in the release record instead of items.

## Expected output
New or refreshed items plus the overview ledger update, in one commit.

## Non-goals
Doing the follow-up work.

## Last run
- 2026-09-25: reports `untracked/missions-2026-09-22/SUMMARY.md`,
  `untracked/release-2026-09-24/STATUS.md`, `untracked/coredoc-2026-09-25/STATUS.md` → 0868–0888.
- 2026-09-26: `untracked/missions-2026-09-25/` (PLAN, CONTRACTS, S-DESIGN, track reports,
  REVIEW/00–15) → 0890–0904.

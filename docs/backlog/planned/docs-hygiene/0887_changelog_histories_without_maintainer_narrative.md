# 0887 — ui-kit and Entity CHANGELOG histories without maintainer narrative

> Package: abstractuic (CHANGELOG.md 0.1.9 and earlier, llms-full.txt); abstractentity (pre-release CHANGELOG.md)
> Type: improvement
> Created: 2026-09-25
> Priority: low
> Labels: docs, changelog

## Summary

Two CHANGELOGs ship maintainer narrative (agent/mission histories, hub references, rulings)
instead of user-facing change notes: abstractuic's 0.1.9 history (~500 lines, also inlined into its
`llms-full.txt`) and abstractentity's pre-release CHANGELOG (~140 KB of internal history). The
coredoc pass left both out of scope.

## Current code reality

- abstractuic `main` `9a307b3`; abstractentity `main` `f3b5a11` (CHANGELOG.md is in the npm
  package when listed in `files`: check).

## Scope

- Rewrite the affected sections as short user-facing notes; move the narrative to an internal
  history file outside the published package (or drop it; git keeps it).
- Regenerate each repo's `llms-full.txt`.

## Acceptance criteria

- [ ] No hub message ids, mission names or seat names in either CHANGELOG.
- [ ] llms files regenerated in the same commit.

## Testing

- `grep -n -E "mission|dm#|c[0-9]{4}|seat" abstractuic/CHANGELOG.md abstractentity/CHANGELOG.md`

## ADR status

- ADR impact: None.

## Receipts

- `untracked/coredoc-2026-09-25/STATUS.md` (abstractuic, abstractentity rows).

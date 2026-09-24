# 0880 — `ABSTRACTENTITY_OBSERVER_URL` is injected and never read

> Package: abstractentity (bin/cli.js, src/vite-env.d.ts); abstractframework (scripts/entity.sh, scripts/entity-local.sh)
> Type: improvement
> Created: 2026-09-25
> Priority: low
> Labels: entity, cleanup

## Summary

The Entity server injects `ui_config.observer_url` from `ABSTRACTENTITY_OBSERVER_URL`, and the root
launchers export it, but the UI no longer reads it: the coredoc pass removed the dead header
backlink it used to drive. A variable that does nothing misleads anyone configuring the app.

## Current code reality (Entity `v0.2.0`, `main` `f3b5a11`; root `cfb4926`)

- `abstractentity/bin/cli.js` l.32 and l.59; type only in `src/vite-env.d.ts` l.11–12; no reader
  in `src/`.
- Root `scripts/entity.sh` l.19/27 and `scripts/entity-local.sh` l.25/32 export and pass it.

## Scope

- Either remove the variable end to end (Entity + root launchers + docs) or restore a real use
  (an Observer link) as a gateway-derived URL; owner's choice.
- Related Entity docs finding kept here for the same owner: `docs/` is not in the npm `files` list.
- Out of scope: Entity UI changes beyond the link.

## Acceptance criteria

- [ ] No launcher or server sets a variable the UI does not read.

## Testing

- `grep -rn "OBSERVER_URL\|observer_url" abstractentity/bin abstractentity/src scripts/entity*.sh`
- `npm --prefix abstractentity test`

## ADR status

- ADR impact: None.

## Receipts

- `untracked/coredoc-2026-09-25/STATUS.md` (abstractentity row).

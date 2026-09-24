# 0878 — AbstractContinuum's hub seat defaults to a personal name

> Package: abstractcontinuum (bin/cli.js)
> Type: bug
> Created: 2026-09-25
> Priority: low
> Labels: continuum, defaults, agora

## Summary

The Team page acts on the agora hub as `ABSTRACTCONTINUUM_HUB_SEAT`, which defaults to `laurent`
(the maintainer's seat name). On anyone else's machine the default names a seat that does not exist
(or impersonates one that does).

## Current code reality (`v0.3.0`)

- `bin/cli.js` l.40 (help text "default laurent") and l.57
  (`process.env.ABSTRACTCONTINUUM_HUB_SEAT || 'laurent'`).

## Scope

- No personal default: derive the seat from the key store (the single operator seat when there is
  exactly one), else show "choose a seat" on the Team page. Keep an explicit setting (0877 flag).
- Out of scope: hub protocol changes.

## Acceptance criteria

- [ ] `grep -rn "'laurent'" abstractcontinuum/bin` returns nothing.
- [ ] With no seat configured, the Team page says what to set instead of failing silently.

## Testing

- `grep -rn "laurent" abstractcontinuum/bin`
- `npm --prefix abstractcontinuum test`

## ADR status

- ADR impact: None.

## Receipts

- `untracked/coredoc-2026-09-25/STATUS.md` (abstractcontinuum row).

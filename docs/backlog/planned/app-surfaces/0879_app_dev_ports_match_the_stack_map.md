# 0879 — App `npm run dev` ports match the stack port map

> Package: abstractcontinuum (package.json), abstractentity (package.json), abstractflow (bin/flags.js, package.json)
> Type: bug
> Created: 2026-09-25
> Priority: low
> Labels: ports, dev-experience

## Summary

The stack map (abstractgateway `apps_manager.STACK_PORTS`, `scripts/start-local.sh`) is Observer
3001, Continuum 3002, Code 3003, Entity 3004, Flow 3005. Continuum's `npm run dev` runs Vite on
**3003** with `--strictPort` (Code's port: whichever starts second fails), and Entity's on **3007**
(an old launcher port the gateway still probes, see 0859).

## Current code reality

- `abstractcontinuum/package.json` l.37 `"dev": "vite --port 3003 --strictPort"`.
- `abstractentity/package.json` l.35 `"dev": "vite --host --port 3007"`.

## Scope

- Dev servers use a port that cannot collide with the stack (the app's stack port when the built
  app is not also running, or a documented dev offset such as 51xx); say it in each app's docs.
- Out of scope: the root launchers (0859).

## Acceptance criteria

- [ ] `npm run dev` in Continuum and Entity no longer uses 3003 / 3007; docs state the dev port.

## Testing

- `grep -n '"dev"' abstractcontinuum/package.json abstractentity/package.json`

## ADR status

- ADR impact: None.

## Receipts

- `untracked/coredoc-2026-09-25/STATUS.md` (abstractcontinuum row); related 0859.

## Status update 2026-09-28 (Flow joins this item)

AbstractFlow 0.4.0 (`d59b6b0`) runs on port **3003** too: `bin/flags.js` `defaultPort: 3003` (the standalone
`npx @abstractframework/flow` default) and `package.json` `"dev": "vite --host --port 3003"`. The stack map gives Flow
3005 and Code 3003, so a standalone Flow and Code web collide. Scope added: Flow's standalone default and dev port.
Package: abstractflow (bin/flags.js, package.json) added. Source: wave-2 ledger ("flow port 3003 vs code", apps gate).

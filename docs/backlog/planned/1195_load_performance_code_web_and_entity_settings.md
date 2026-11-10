# 1195 — Load performance: Code web "Restoring saved activity" and the Entity Settings screen are slow

> Package: AbstractGateway (history replay, /runs listing, session restore), AbstractCode (web), AbstractEntity (Settings/Mind screen), AbstractUIC (panel-chat replay projection)
> Type: bug
> Status: planned
> Created: 2026-11-10
> Priority: P1
> Labels: performance, code-web, entity-app, next-wave

## Summary

Operator, 2026-11-10 10:33-10:35 (live dev stack, gateway 98bcda38): "loading this screen is fairly slow" (Entity app
Settings/Mind), and "even loading abstractcode web is very slow" (Code web stuck on "Loading conversation · Restoring
saved activity", sidebar "Loading conversations…"). He notes the whole machine may have been slow at the time (three
Claude sessions, test suites, the dev stack). Measure first, then fix the real causes.

## Current code reality (2026-11-10)

- Code web restores a conversation by replaying the gateway's view (`/runs/{id}/view`) and the session history; the
  kit's replay projection folds every ledger event client-side; `/runs?status=…` listings are known to take 3–16 s on
  this machine under load (RESUME 2026-11-07 connection measurements; root backlog 1140 one connection per origin).
- The Entity app's Settings screen loads the cognition profile, the identity card, mounts, tools and skills in separate
  requests.
- The gateway's /graph snapshot (0.21.0) made the Entity graph load 2 s then 5 ms; the same approach (one cached
  snapshot per session, folded server-side) is the candidate for the Code conversation restore.

## Related

abstractentity backlog 0012 (slow Settings load) points here.

## Validation

Measure on an idle machine: Code web conversation restore < 1 s for a 100-turn conversation; Entity Settings < 500 ms;
record the numbers in the item; a browser-timing test in each app's e2e suite that fails above the budget.

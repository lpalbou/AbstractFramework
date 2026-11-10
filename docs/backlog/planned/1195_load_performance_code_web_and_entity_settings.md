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

## Measured 2026-11-10 23:50 (untracked/release-2026-11-07/audit-fable/CODE-WEB-LOAD-PROFILE.md)

The Code web first screen waits for all 8 catalog requests, then for the archived runs listing, before showing anything
(use_workspace_catalog.ts:228-278); the events catch-up re-requests the list 500 ms later (app.tsx ~395); a restore reads a
4.85 MB history bundle to list 31 turn ids (kit replay_view.ts:540) where `runs?session_id=&root_only=true` answers in 4-7 ms;
30 earlier-turn views cost 11 s cold (view cache of 64 entries). Gateway: the runs index runs in `verify` mode and re-scans
16.8k run files per listing (130 ms alone, seconds under load; /api/health counted 2,487 listings since boot and 0
differences against `trusted` in 2,344 comparisons); `discovery/capabilities` is recomputed per request (0.5-4.3 s).
The sentence above about the client folding every ledger event is out of date: the server builds the view.

Ranked fixes: (1) gateway `--run-index trusted` (flag at the next restart; default change at the next cut) ≈ 0.5-10 s per
load; (2) Code web: apply catalog answers as they arrive, archived count off the critical path without include_metrics,
no refresh after the events catch-up ≈ 0.4-8 s; (3) kit: list a conversation's turns from the runs index (parity test)
1.9-8.1 s → ms; then a cache for discovery/capabilities, long browser caching for hashed assets (1.8 MB per load).

## Validation

Measure on an idle machine: Code web conversation restore < 1 s for a 100-turn conversation; Entity Settings < 500 ms;
record the numbers in the item; a browser-timing test in each app's e2e suite that fails above the budget.

# 1140 — One gateway connection per browser origin, shared by every tab and app

> Package: AbstractUIC (kit module), AbstractCode, AbstractAssistant (web), AbstractGateway (small)
> Type: design + implementation (next wave)
> Created: 2026-11-07
> Priority: high
> Labels: web, reliability, permissions, design-done

## Operator note (2026-11-07)

"i should be able to open as many tabs as i need to." — said after an "Allow" click on a tool-permission card hung
("gateway did not answer within 15 seconds") with two AbstractCode tabs open. Also: "the whole principle is that gateway
could be shutdown, i could leave for a week and still click those buttons and it should work."

## Summary

Browsers allow 6 HTTP/1.1 connections per host across ALL tabs (Chrome/Firefox "won't fix"; Safari/WebKit the same).
AbstractCode holds three long-lived streams per conversation (`me/events/stream`, `runs/{id}/view/stream`,
`runs/{id}/ledger/stream`), so two tabs with a parked approval use all six and the seventh request, the approval
click, waits forever. Measured on 2026-11-07: 2 Code tabs = 6/6 Safari connections; the approval itself survives a
gateway restart (durable), so the hang is purely the browser's connection pool.

Interim shipped in Code web 0.15.7 (branch release/web-0.15.6, local deploy): no client timeout on the policy save
(an approval must never time out), and a hidden tab drops its streams. That lowers the count per tab; it does not
remove the limit.

## Design (recorded 2026-11-07, `untracked/release-2026-11-07/connections/DESIGN.md`, read-only investigation)

One gateway connection per ORIGIN, owned by a SharedWorker (Web Locks leader election where SharedWorker is
missing), carrying the existing per-user `me/events/stream` (already multiplexed by channel; `attention` = pending
permissions). Run streams (ledger/view) are ref-counted in the same worker and opened only for runs a VISIBLE tab
shows. Hidden tabs and gateway-restart gaps are covered by cursor catch-up through `GET /me/events?after=` (the
resume contract already exists: `id:` = sequence, `Last-Event-ID` honoured). Rejected as foundations: HTTP/2 on
loopback (browsers need TLS; a local CA breaks the dead-simple install and the no-keychain ruling), WebSocket per
tab (Safari pool behaviour unverified; still one socket per tab). Free bonus: over the Tailscale https name the
browser already speaks HTTP/2 to tailscaled (measured), so the 6-limit does not apply there.

## Scope

### In scope

- A kit module (`@abstractframework/ui-kit`): the shared worker, the leader fallback, a subscribe API for apps
  (`events(channel)`, `run(id).view/ledger` ref-counted), cursor catch-up, reconnect with backoff.
- AbstractCode web and AbstractAssistant web adopt it (today each re-implements streaming: `workspace/me_events.ts`,
  `gateway/client.ts`, `panel-chat/src/replay_view.ts`).
- Gateway: count `me/events/stream` in the SSE semaphore (it is unbounded today) and raise the cap for the shared
  worker's one connection per user; nothing else.
- A test that opens 8 tabs with parked approvals and clicks Allow in the 8th within 2 s (Playwright, spec drafts in
  `untracked/release-2026-11-07/connections/spec/`).

### Out of scope

- HTTP/2 on 127.0.0.1, local certificates, a new server (hypercorn/granian).
- Changing the permission model (Deny / Allow / Allow All, session scope only: settled 2026-11-07).

## Acceptance criteria

- [ ] 8 Code tabs on one conversation with a parked approval: the Allow click answers within 2 s; `netstat` shows one
      established gateway connection for the origin plus short requests.
- [ ] Killing the gateway for 60 s and restarting it: every tab catches up through the cursor, the approval card is
      still there and still works.
- [ ] Safari 16+, Chrome, Firefox: same behaviour (Safari is the operator's browser).
- [ ] Deleting the worker's catch-up call makes the hidden-tab test go red (a check that cannot fail is decoration).

## Related

- FOLLOWUPS.md 2026-11-07 ("browser connection starvation design"); Code web 0.15.7 interim; AbstractGateway
  `routes/me_events.py`; `security/gateway_security.py` SSE semaphore (`max_sse_connections=32`).

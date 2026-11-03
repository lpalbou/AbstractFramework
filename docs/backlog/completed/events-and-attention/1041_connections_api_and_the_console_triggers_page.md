# 1041 — Connections API and the console Triggers page

> Package: gateway
> Type: feature
> Created: 2026-10-25 12:50:00 +0200
> Priority: P1
> Labels: events-and-attention, gateway, console, triggers

## Summary

Gateway routes `GET/POST /api/gateway/triggers/connections`, `GET/PUT/DELETE /api/gateway/triggers/connections/{id}`, `GET .../{id}/events?after=<seq>&limit=`, `POST .../{id}/test-fire`, and a console page `/console/triggers` listing the user's connections (source, status, last event), a create form driven by the source's `connection_schema`, recent events, a test-fire button and, for webhooks, the ingress address and a one-time secret display. Also the admin view of all connections.

## Why

This is the human-facing half of the operator's request: a page in the gateway to register which events we can listen to, reusable across sessions and from Flow.

## Scope

### In scope

- Routes with principal scoping, route-family authorization like the automations family, request/response schemas.
- The console web page (same stack and conventions as the existing console pages; discover where `/console` is served and follow its page pattern) and the TUI parity entry.
- OpenAPI/docs entries.

### Out of scope

- Flow's selector (1047).
- Admin-wide policies beyond list/revoke.

## Current code reality

- `routes/automations.py:119-141` serves trigger sources; no connection routes exist.
- Console pages are served by `console_ui.py`; the TUI mirrors the web console (console-tui/).

## Acceptance criteria

- [ ] All routes exercised by tests with two principals (Alice cannot read Bob's connection).
- [ ] The console page lists, creates, test-fires and deletes a connection; a screenshot is kept under `untracked/`.
- [ ] Test-fire appends to the connection stream and is visible in recent events within one refresh.

## Testing

- `cd abstractgateway && python -m pytest tests -q -k 'trigger_connections'`

## References

- 1040 (store), 1042 (webhook ingress), 1047 (Flow selector).

## Receipts

- design note: `untracked/design/attention-triggers-replay-2026-10-25.md` (two adversarial rounds)

## Completion report

> Completed: 2026-10-25 18:30:00 +0200
> Original path: `docs/backlog/planned/events-and-attention/1041_connections_api_and_the_console_triggers_page.md`
> Final path: `docs/backlog/completed/events-and-attention/1041_connections_api_and_the_console_triggers_page.md`

**Outcome.** Connections API (principal-scoped, admin all=true, events, test-fire, webhook secret once) and the console Triggers tab (web /console#triggers + terminal): rows by label, Listening switch with the operator's semantics, loading/empty/error states, events as sentences, webhook setup panel with an in-browser signed test call. Tests: console unit 266, browser suites, terminal 980.

**Commits.** gateway 1904ff7f, 19bd7cb3, 7858741a, d0aceb9c, 818e70ee, 7f2176da, 526a310e, 600145cd, 91017c8c, 78499020, 633630e9 (all local, unpushed, unpublished; per-repo receipts under `untracked/lanes/`).

**Validation.** Lane receipts with per-item mutation checks: `untracked/lanes/L1-runtime.md`, `L2-gateway-triggers.md`, `L3-gateway-events.md`, `L4-flow-console.md`, `L5-consumers-e2e.md`, `UX-A-flow.md`, `UX-O-observer.md`; UX reviews `untracked/ux-review/REPORT.md` and `REPORT-2.md`; live evidence `abstractgateway/untracked/live-email-2026-10-25/`.

**Follow-ups.** See proposed [1050](../../proposed/1050_events_and_attention_follow_ups.md).

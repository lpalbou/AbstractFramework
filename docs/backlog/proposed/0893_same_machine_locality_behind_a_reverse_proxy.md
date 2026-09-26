# 0893 — Same-machine locality behind the operator's reverse proxy, and a verdict before the first run

> Package: abstractgateway (security/same_machine.py, routes); abstractcode (tui workspace_files.rs, web); app-server consumers
> Type: improvement
> Created: 2026-09-26
> Priority: normal
> Labels: security, same-machine, proxy, ux

## Summary

The gateway decides "is this caller on the gateway's own machine" (open folder, local workspace
path, engine install) with one rule (`request_is_from_this_machine`). Two known limitations remain:
(1) in trust-proxy mode (the operator's own reverse proxy in front of the gateway), a request that
came through an app server (`X-AbstractFramework-App-Proxy`) is never local, even when the browser
really is on the gateway host — deliberate fail-safe (CONTRACTS A-8); (2) the Code TUI treats a
same-host LAN URL (for example `http://192.168.x.y:8080` copied from the console) as remote until the
first run returns the gateway's verdict; the interim is `/workspace send always`. A gateway route
that returns the same-machine verdict before any run would remove (2) and could make (1) explicit.

## Why

- C2 report: "Ruling kept: a same-host LAN URL counts as remote until the first run's verdict;
  shared-mount users use `/workspace send always`."
- REVIEW/04 S4/S5 (LAN regression, "decide with the gateway's verdict"); REVIEW/09 S1–S3 (fail-safes).

## Current code reality (2026-09-26; abstractgateway `1172686`, abstractcode `2baacf3`)

- `abstractgateway/src/abstractgateway/security/same_machine.py`: `effective_peer` l.120,
  `APP_PROXY_HEADER = "x-abstractframework-app-proxy"` l.143, `trust_proxy_mode` l.146 (stored
  network `trust_proxy` first), `request_is_from_this_machine` l.165–173.
- The verdict is exposed only per run: `routes/gateway.py` l.9264–9280 (`GET /runs/{id}/workspace` →
  `host.caller_is_this_machine`, `open_supported`). No pre-run route carries it.
- abstractcode TUI: `tui/src/config.rs` l.305–309/383 `send_local_workspace` (auto|always|never);
  `tui/src/workspace_files.rs` loopback detection before the first verdict.

## Scope

### In scope

- A small authenticated route (or a field on an existing one such as `/me` or `/host/state`) that
  returns `{caller_is_this_machine, basis}` for the calling request; clients (TUI, web, Assistant)
  ask once at connect.
- Document the trust-proxy limitation where the network setting is changed (console, CLI), with the
  reason (the reverse proxy hides the browser).

### Out of scope

- Trusting forwarded headers from untrusted peers (never; REVIEW/09 S2).
- Changing the A-8 fail-safe itself.

## Dependencies

- 0153 (browser session security contract); ADR on network exposure if one is written for 0892.

## Expected outcomes

- A TUI on the gateway host using a LAN URL gets local behaviour from the first message.
- Operators behind their own reverse proxy see why app-proxied requests are never local.

## Acceptance criteria

- [ ] Route returns the same verdict as `/runs/{id}/workspace` for the same request (test both).
- [ ] TUI uses it before the first run; `/workspace send always` remains as the shared-mount override.

## Validation

- Gateway: unit tests over loopback, LAN-own-address, app-proxied, trust-proxy on/off.
- TUI: headless test with a fake gateway answering `caller_is_this_machine: true` on a LAN URL.

## Evidence

- `untracked/missions-2026-09-25/C2/REPORT.md` (Review 04 fixes)
- `untracked/missions-2026-09-25/REVIEW/04-code-tui.md` (S4, S5)
- `untracked/missions-2026-09-25/REVIEW/09-gateway-early.md` (S1–S3)
- `untracked/missions-2026-09-25/CONTRACTS.md` (A-8)

## ADR status

- ADR impact: None unless the route becomes part of a network-exposure ADR.

## Receipts

- None yet.

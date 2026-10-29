# 0858 — Console toggle for `allow_engine_install`

> Package: abstractgateway (web console, abstractgateway-console)
> Type: task
> Status: completed 2026-10-29 (AbstractGateway PR #49, unreleased)
> Created: 2026-09-23
> Priority: normal
> Labels: console, engines, security

## Summary

Engine installs from the gateway console run on the gateway host, so `allow_engine_install` is on
by default only for a loopback-bound gateway. Today it can be changed only through
`POST /admin/runtime-config`; the 403 `not_allowed` message points there. Admins need a visible,
audited switch in the console (web and terminal) that shows the effective value and its source
(stored versus the loopback default).

## Acceptance criteria

- [x] Admin-only toggle in the web console Engines tab and the terminal console, with the CLI twin
      shown.
- [x] Effective value and source displayed; change recorded in the audit log.
- [x] Non-admin users see the value read-only.

## Status update 2026-09-25 (post-release trace)

Still open in abstractgateway 0.4.2. The rule changed (mission HH): installs are allowed by default
for a caller on the gateway's own machine even on a LAN-bound gateway
(`runtime_config.allow_engine_install_for_caller`), and still off for other computers on a
non-loopback bind. The value is still changeable only through `POST /admin/runtime-config`; the
console says "An admin can allow it in the gateway settings" (`console_ui.py` ~l.1218) and the
network warning says "Settings → allow_engine_install" (`network_exposure.py` ~l.1211), but no
settings form in the web console or `abstractgateway-console` exposes the key. The text points
users at a switch that does not exist in the UI.

## Completion 2026-10-29

Done in AbstractGateway PR #49 (unreleased):

- Web console, Engines tab: an admin switch "Allow engine installs from the console" showing the value and
  where it comes from (your setting, or which default: on the gateway's own computer, a gateway only this
  computer reaches, or one other computers reach). "Use the default" clears a stored choice, and the line
  shows the CLI twin `abstractgateway-config set allow_engine_install on|off`. A save is
  `POST /api/gateway/admin/runtime-config {"allow_engine_install": true|false|null}`, which the audit
  middleware records. Non-admins see it read-only ("Only an admin can change this").
- Terminal console, Providers → Local providers: the same lines. An admin presses E to turn it on or off
  and D to use the default, with "Saved" or "Not saved: …" in place.
- The refused-install 403 and the network-exposure note now point at this switch, not at a settings form
  that never existed.
- Tests: 3 node tests (`tests/test_gateway_console_engine_install_setting.py`) and 4 cargo tests in
  `console-tui/src/ui/providers_engines.rs`, all mutation-checked.

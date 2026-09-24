# 0858 — Console toggle for `allow_engine_install`

> Package: abstractgateway (web console, abstractgateway-console)
> Type: task
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

- [ ] Admin-only toggle in the web console Engines tab and the terminal console, with the CLI twin
      shown.
- [ ] Effective value and source displayed; change recorded in the audit log.
- [ ] Non-admin users see the value read-only.

## Status update 2026-09-25 (post-release trace)

Still open in abstractgateway 0.4.2. The rule changed (mission HH): installs are allowed by default
for a caller on the gateway's own machine even on a LAN-bound gateway
(`runtime_config.allow_engine_install_for_caller`), and still off for other computers on a
non-loopback bind. The value is still changeable only through `POST /admin/runtime-config`; the
console says "An admin can allow it in the gateway settings" (`console_ui.py` ~l.1218) and the
network warning says "Settings → allow_engine_install" (`network_exposure.py` ~l.1211), but no
settings form in the web console or `abstractgateway-console` exposes the key. The text points
users at a switch that does not exist in the UI.

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

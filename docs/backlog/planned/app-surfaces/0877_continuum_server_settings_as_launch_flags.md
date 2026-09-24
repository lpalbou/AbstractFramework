# 0877 — AbstractContinuum server settings as launch flags, with a complete `--help`

> Package: abstractcontinuum (bin/cli.js, bin/hub_proxy.js); abstractgateway (apps_manager launch of Continuum)
> Type: improvement
> Created: 2026-09-25
> Priority: low
> Labels: apps, settings, continuum

## Summary

`abstractcontinuum` is configured only through environment variables (`PORT`, `HOST`,
`ABSTRACTCONTINUUM_GATEWAY_URL` / `ABSTRACTGATEWAY_URL`, `ABSTRACTCONTINUUM_HUB_URL` /
`AGORA_HUB_URL`, `ABSTRACTCONTINUUM_HUB_SEAT`, `ABSTRACTCONTINUUM_HUB_KEYS`,
`ABSTRACTCONTINUUM_HUB_KEY`, `ABSTRACTCONTINUUM_HUB_ALLOW_REMOTE`); it accepts no flags other than
`--help` / `--version`, and `--help` omits `HUB_KEY` context, `HUB_ALLOW_REMOTE` and the
proxy-hardening variables. The framework rule is launch flags, not env vars, for switches.

## Current code reality (tag `v0.3.0`, `main` `7bc4616`)

- `bin/cli.js` l.22–58 (argv handling, help text, env reads); `bin/hub_proxy.js` l.219, 418, 524.

## Scope

- Flags (`--port`, `--host`, `--gateway-url`, `--hub-url`, `--hub-seat`, `--hub-keys`,
  `--hub-allow-remote`) taking precedence over the env vars, which stay as a fallback.
- `--help` lists every flag and every honoured variable.
- The gateway's apps manager passes flags instead of env when it starts Continuum (coordinate with
  the gateway owner; keep env for older Continuum versions).
- Out of scope: new settings.

## Acceptance criteria

- [ ] Every env var read in `bin/*.js` has a flag and appears in `--help` (test enumerates
      `process.env.*` reads).
- [ ] Flags win over env; documented in `docs/`.

## Testing

- `node abstractcontinuum/bin/cli.js --help`
- `npm --prefix abstractcontinuum test`

## ADR status

- ADR impact: None (applies the operator's launch-flags rule).

## Receipts

- `untracked/coredoc-2026-09-25/STATUS.md` (abstractcontinuum row).

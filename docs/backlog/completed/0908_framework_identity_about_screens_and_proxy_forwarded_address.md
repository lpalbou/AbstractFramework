# 0908 — One framework identity, an About screen in every app, and one forwarded-address rule for app proxies

> Package: abstractframework (identity descriptor, `scripts/check_identity_sync.py`); abstractcore (`utils.identity`); @abstractframework/ui-kit 0.1.12 + app-server 0.1.10 (abstractuic); abstractgateway (`/about`, console, tray, console-tui); abstractflow, abstractobserver, abstractcontinuum, abstractentity, abstractcode (web + TUI), abstractassistant
> Type: feature
> Created: 2026-09-26
> Completed: 2026-09-26
> Priority: normal
> Labels: identity, about, ui-kit, proxy, security, mission-wave-2026-09-25, unreleased

## Summary

Completed record for missions U, B-apps, B-consolidate, P-flow and the About parts of C1, C2, A, G1
and G2 (2026-09-25/26 wave; committed locally, not released; release staged, waiting for the
operator's go). Every app now shows the same About rows (application, "Part of AbstractFramework",
author, copyright, website, source, docs, issues, feedback, contact) plus the gateway's package
versions, all built from one canonical descriptor. In the same pass every app proxy that talks to
the gateway now sends the browser's real address, which the gateway's single "same machine" rule
depends on.

## Why

Operator request, as recorded by the orchestrator (`PLAN.md`, tracks U and B-apps): "ui-kit:
identity + AfAboutDialog + top-bar slot + console island" and "About adoption: flow, continuum,
entity, observer, code WUI, gateway console WUI/TUI + tray". REVIEW/00 P0-2 found that both app
proxies deleted `X-Forwarded-For`, so every browser proxied through an app — LAN browsers included —
counted as "this machine" for the engine-install and app-launch gates.

## What landed

- **Descriptor**: root `identity/abstractframework.json` + byte-compare drift check
  `scripts/check_identity_sync.py` (root `e3f85e2`, `3bc1de7`; fixtures added `a437916`, `6a295fc`,
  `1468073`). abstractcore `8d92191` `utils.identity` (`app_identity`, `about_fields`,
  `about_html`, `gateway_version_rows`), parity fixes `f23e142`, `266afcb` (runs the shared 13-case
  fixture), console themes `622e789`.
- **ui-kit 0.1.12** (abstractuic `f55e1df` … `a48311c`): `frameworkIdentity`, `appIdentity`,
  `aboutRows`, `AfAboutDialog` (focus trap, `aria-labelledby`), `about` slot on `AfTopBarActions`,
  islands `mountAbout`, and `gatewayVersionRows(payload | null, error?)` whose output is pinned by
  the shared fixture. FINAL tarball sha256 `1e84bbf7…f66b`.
- **Apps**: Flow `0d3e72f`/`e4ed91c`, Observer `bd80dbb`/`e78ab0b`, Continuum `04d4627`/`f2922f1`,
  Entity `2489a9c`/`02c5d4b`, Code web `c43f9b9`/`7e89895`, Code TUI `/about` + `/version`
  `8f1b5b4`, Assistant `11c4aad`/`181fd10`/`612a942`/`cd7822d` (single `_version.py`, tray
  "About AbstractAssistant…"). Gateway: public `GET /about` + tray rows `b1e5018`, console About
  `1172686`, console-tui About (F1 / ? / `--about`) `c2bdd53`.
- **Forwarded-address rule**: app-server 0.1.10 `7edc295` (overwrite `X-Forwarded-For` with the
  socket peer on every gateway-bound call, drop client `Forwarded`/`X-Real-IP`/`X-Forwarded-*`,
  unknown peer → 400) and `a5858ba` (`X-AbstractFramework-App-Proxy: <appId>` marker, FINAL sha256
  `6586583f…4a96`); Code web `bin/server.js` `6e5c46b`, `41477b0`, `67a204a`; Flow `bin/cli.js`
  `eb53099` (incl. WebSocket upgrade). Gateway `4943e7b` + `2bf5c4f`: one same-machine rule, XFF
  believed only from a loopback peer, uvicorn `forwarded_allow_ips` pinned to `127.0.0.1,::1`, a
  marker-keyed fail-safe, untrusted forwarded → never local.

## Completion report

- Tests: ui-kit `check_about.mjs` 309 → 359 checks (10 apps; mutation-checked); Python/TS parity 0
  diffs for all 10 ids; app suites Flow 690, Observer 129, Continuum 440, Entity 475, Code web 226;
  app-server proxy tests (spoofed XFF, LAN peer, IPv4-mapped, unknown peer, marker); gateway
  console/about tests 172, console-tui cargo 209.
- E2E (`E2E/REPORT.md`): check 1 `/about` public; check 4 the Code web proxy
  sends `XFF 127.0.0.1` + marker `code` on all 5 gateway-bound requests and a browser spoof never
  reaches the gateway; About dialog screenshot with live gateway rows; check 5 Assistant About rows.
- Reviews: REVIEW/02 ACCEPT-WITH-FIXES everywhere (X1 only half the proxies changed; X2 behind a
  same-host reverse proxy every browser looks local; S1 four apps, four formats of gateway rows) →
  REVIEW/07 (b) ACCEPT after `gatewayVersionRows` consolidation; REVIEW/12 ACCEPT for app-server,
  Code web and Flow proxies.
- Deviations kept: `ISLANDS_API_VERSION` stays "1" (additive change); About is an icon button.
- Follow-ups: reverse-proxy locality and a pre-run locality verdict →
  [0893](../proposed/0893_same_machine_locality_behind_a_reverse_proxy.md); Flow/Code web proxies
  onto app-server → [0894](../proposed/0894_migrate_flow_and_code_web_proxies_onto_app_server.md);
  identity drift check as a release gate → [0903](../proposed/0903_identity_sync_check_in_the_release_checklist.md);
  consumers' app-server floor `^0.1.10` and relock → [0899](0899_npm_relock_and_kit_floors_after_the_kit_publishes.md).
  Shared doc note: apps say "a gateway version that serves GET /about" — pin the number at release.
- ADR state: none written; the "one same-machine rule; proxies overwrite, never append" rule is a
  candidate if more proxies appear (0894).

## Receipts

- `untracked/missions-2026-09-25/U/REPORT.md`, `B/REPORT.md`, `C1/REPORT.md`, `C2/REPORT.md`, `A/REPORT.md`, `G1/REPORT.md`, `G2/REPORT.md`, `E2E/REPORT.md` (checks 1, 4, 5)
- `untracked/missions-2026-09-25/REVIEW/00-contracts-review.md` (P0-2), `02-about-track.md`, `07-xa-recheck.md`, `09-gateway-early.md`, `12-proxies.md`

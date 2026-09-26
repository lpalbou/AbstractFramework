# 0899 — Relock the npm apps and raise kit floors after ui-kit, panel-chat and app-server publish

> Package: abstractcode (web/package-lock.json); abstractobserver, abstractentity, abstractcontinuum (package.json, lock); abstractuic (ui-kit 0.1.12, panel-chat 0.1.17, app-server 0.1.10); abstractframework release wave
> Type: task
> Created: 2026-09-26
> Completed: 2026-09-26
> Priority: high
> Labels: release-step, npm, lockfile

## Summary

Release step. The wave ended with unreleased kit packages consumed through hand-installed tarballs:
Code web's `package.json` asks `ui-kit ^0.1.12` and `panel-chat ^0.1.17`, but its
`package-lock.json` still pins the registry `0.1.10` / `0.1.16`, so `npm ci` fails. Observer, Entity
and Continuum depend on `app-server ^0.1.9`, while the XFF overwrite and app-proxy marker the gateway
now keys on are in app-server 0.1.10. After the three kit packages are published: raise the floors,
run `npm install` in each app, and prove the published artifact (not an earlier same-version pack) is
what landed. The crates.io trusted-publishing gap for `abstractgateway-console` stays in 0857.

## Why

- REVIEW/03 B1: "`npm ci` cannot pass … Relock after ui-kit 0.1.12 is published."
- REVIEW/15 S1 and REVIEW/07 R1: two different "0.1.17" / "0.1.12" tarballs existed (same-version
  repack trap). CONTRACTS S-3 (f) fixes the FINAL sha256 of each.
- C1 and S-web reports: "lock still 0.1.10/0.1.16 → relock at release".

## Current code reality (2026-09-26)

- `abstractcode/web/package.json` l.44–45: `panel-chat ^0.1.17`, `ui-kit ^0.1.12`;
  `package-lock.json`: `node_modules/@abstractframework/panel-chat` 0.1.16 and `ui-kit` 0.1.10 from
  registry.npmjs.org.
- `abstractobserver/package.json` l.46, `abstractentity/package.json` l.45,
  `abstractcontinuum/package.json` l.46: `@abstractframework/app-server ^0.1.9`; their locks pin 0.1.9.
- abstractuic `7a5cd8e`: ui-kit 0.1.12, panel-chat 0.1.17, app-server 0.1.10 (all unreleased).
  Final sha256 (CONTRACTS S-3 f): panel-chat `a6411d52…53fd`, ui-kit `1e84bbf7…f66b`,
  app-server `6586583f…4a96`.
- 0857 (crates.io trusted publishing for `abstractgateway-console`) still planned.

## Scope

### In scope

- Publish order: abstractuic kit packages first (owner OTP rule for new names does not apply; these exist).
- Floors: observer/entity/continuum → `app-server ^0.1.10`; Code web keeps `^0.1.12` / `^0.1.17`.
- `npm install` in each consumer; commit the lock; grep-prove `gatewayVersionRows` (ui-kit),
  `closeLiveRepliesVia` (panel-chat) and `X-AbstractFramework-App-Proxy` (app-server) in
  `node_modules` AND in the built `dist`.

### Out of scope

- Crates.io trusted publishing (0857); app feature work.

## Dependencies

- Operator go for the kit publishes (never without an explicit per-release go).
- 0894 may later remove Code web's own proxy; not a blocker.

## Expected outcomes

- `npm ci` passes in every app; no app ships a stale kit build.

## Acceptance criteria

- [x] `npm ci && npm test && npm run build` green in abstractcode/web, abstractobserver, abstractentity, abstractcontinuum.
- [x] The three grep proofs hold in each consumer's `node_modules` (the minified `dist` is covered by the pack comparison instead).
- [x] Published tarball sha256 equals the CONTRACTS S-3 (f) values (or the release record states the new ones).

## Validation

- `npm view @abstractframework/ui-kit@0.1.12 dist.integrity` (and panel-chat, app-server) vs the local packs.
- `grep -rl gatewayVersionRows abstractcode/web/node_modules/@abstractframework/ui-kit/dist abstractcode/web/dist`

## Evidence

- `untracked/missions-2026-09-25/C1/REPORT.md` (c43f9b9; Review 03 fixes "Open")
- `untracked/missions-2026-09-25/S/REPORT.md` (S-web)
- `untracked/missions-2026-09-25/REVIEW/03-code-web.md` (B1), `REVIEW/07-xa-recheck.md` (R1), `REVIEW/15-code-web-streaming.md` (S1)
- `untracked/missions-2026-09-25/U/REPORT.md` (app-server 0.1.10 tarball)
- `untracked/missions-2026-09-25/CONTRACTS.md` (S-3 f)

## ADR status

- Governing: ADR-0034 (release sequence). ADR impact: None.

## Receipts

- None yet.

## Completion report (2026-09-26)

- Kits published by CI with provenance from `v0.1.12` → `f1b3e00`: ui-kit 0.1.12, panel-chat 0.1.17,
  app-server 0.1.10 (app-server after the owner added its npm trusted publisher; run 36226821236
  attempt 2).
- Relocks committed, pushed, CI green and tagged: abstractcode `b243398` (web lock ui-kit
  0.1.10 → 0.1.12, panel-chat 0.1.16 → 0.1.17; tags `v0.6.0` / `web-v0.5.0` on `a636806`, which adds
  a test-only fix on top), observer `bf33805` (`v0.1.13`), entity `16de0a3` (`v0.2.2`), continuum
  `c2530d1` (`v0.3.2`). Each relock changed only `package-lock.json`; the app-server floor `^0.1.10`
  was already in the three `package.json` files.
- Validation: `npm ci`, tests (code web 255, observer 129, entity 475, continuum 440) and builds
  green locally and on CI. Published app packages equal local clean packs of their tags (integrity,
  shasum; registry tarballs `cmp`-identical for the three apps). Grep proofs at this trace (local
  `node_modules`): `gatewayVersionRows` in `abstractcode/web/node_modules/@abstractframework/ui-kit/dist`,
  `closeLiveRepliesVia` in `…/panel-chat/dist`, `X-AbstractFramework-App-Proxy` in
  `app-server/src/gateway_session_proxy.js` of observer, entity and continuum. The built `dist` is
  minified, so the identifier proof does not apply there; the pack comparison covers it.
- Tarball shas: ui-kit `b5aad1d5…` and app-server `a156ba5e…` (README-only change vs S-3 f, CONTRACTS
  A-10); panel-chat published as `0070975c…`, not the staged `e28aa9ec…`, because the staged pack
  carried three stale `dist/types.*` files (CONTRACTS A-11). Stated in [0921](0921_release_wave_2026_09_26.md).
- ADR impact: None.

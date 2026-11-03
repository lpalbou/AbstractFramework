# 1049 — Apple push for the watch and the phone (gateway dispatcher + publisher relay)

> Package: gateway, assistant (watch, iPhone)
> Type: feature
> Created: 2026-10-25 12:50:00 +0200
> Planned: 2026-10-25 21:40:00 +0200
> Priority: P1
> Labels: events-and-attention, push, apns, watch, phone, adr-0040

## Summary

A closed watch or phone app learns within seconds that an approval, a question, a published notice or an automation result waits, with nothing for the person to configure: the app registers its APNs token with the gateway at sign-in; the gateway's push dispatcher turns `attention.raised` events into requests to a small, stateless, publisher-hosted relay that holds the APNs key and builds a fixed localized message; the device's notification service extension fetches the real event from its own gateway. Designed 2026-10-25 with an adversarial review (`untracked/design/push-2026-10-25.md` and `-review.md`; the contract below is complete on its own).

## Why

Push is the only prompt path while an app is closed; watchOS background refresh runs when it likes (15 min at best). The gateway is open source and self-hosted, so the Apple key cannot live in it; the relay is the standard shape (Home Assistant, Nextcloud).

## Decisions (from the review)

- No free text through the relay: it accepts a kind and builds the message itself (`title-loc-key`/`loc-key`), so a stolen device token cannot phish under the app's name. The device replaces the generic text with the real name through its service extension (watchOS 6+ and iOS both have one).
- No gateway authentication at the relay (a self-hosted gateway can only sign with a key it made); no install id (unverifiable, tracks installs). Abuse is bounded by fixed messages, per-token and per-IP rate limits, 1 KB strict JSON.
- One flag, `--push-relay <URL|off>`, default `off` until the publisher's relay is live; then the packaged default is its URL. No env var.
- The relay ships as `abstractgateway push-relay …`, not a new package.
- Cut from v1: titles, badges, silent `attention.seen` pushes, `run.finished` pushes, a device toggle (the system's notification permission is the toggle).
- Watch-first: alerts go to the watch when one is registered, else to the phone (the iPhone app is not the watch app's companion, so both would ring the wrist twice). Merging the app families is an operator decision.

## Contract

### Gateway routes (principal-scoped; CSRF on session writes)
- `PUT /api/gateway/me/push/devices/{device_id}` body `{token: hex 64..200, topic, env: production|sandbox, app: watch|phone, reg: 16..32 hex, name?: ≤60}`; topic must be on the allowlist (the two packaged bundle ids + the relay's `GET /v1/info` topics); refreshes `refreshed_at`, moves the token from any other principal; answers `{ok, relay: on|off|unreachable}`.
- `DELETE /api/gateway/me/push/devices/{device_id}`.
- `GET /api/gateway/me/push/devices` → `[{device_id, app, name, refreshed_at, last_sent_at, last_error}]`, never tokens.
- Registration expires 7 days after the last refresh (the app re-PUTs at most daily and at every sign-in with a new `reg`; DELETE at sign-out).

### Store (per plane data dir, 0600)
- `push/devices.json` `{schema_version: 1, devices: {id: {...}}}`; gateway-wide `push/token_owners.json` (`sha256(token)` → principal key).
- `push/cursor.json` `{after}` baselined to the stream head on first start (old events are never pushed).
- `push/outbox.sqlite3` table `rows` (pk `event_id|device_id`; `seq, kind, collapse, record_key, created_ts, attempts, next_ts, state queued|sent|dropped, error`); capped at 5,000 rows; sent/dropped purged after 7 days.

### Dispatcher (in the process that runs the runner, started beside the email worker)
- Wakes on the stream listener and every 2 s when the change token moves; idle with no devices or `--push-relay off` (no thread work, no outbound calls; a socket guard test proves it).
- Mapping of `attention.raised` by kind: approval → approval; question → question; notify with a `publish:` record → notify; notify (automation) → result; failure → failure. Everything else ignored. `attention.seen` drops matching queued rows. Collapse id `sha256("attention:" + record_key)[:32]`.
- Retry ladder up to 1 h, one log line per hour, then dropped with `notification.failed`; `sent` records `notification.sent` for channel watch|phone and sets `last_sent_at`; `gone` deletes the device only if Apple's timestamp is newer than `refreshed_at`; `rejected` drops the row and sets `last_error`.
- Split mode (runner in its own process): the dispatcher runs where the runner runs and polls the change token, so an append from another process is dispatched within 3 s.

### Relay (`abstractgateway push-relay --apns-key-file --key-id --team-id --topic … --listen`)
- `POST /v1/push {topic, env, token, kind, collapse, seq, reg}`; strict JSON, unknown field 400, ≤ 1 KB, topic allowlist.
- Builds APNs: `apns-push-type: alert`, priority 10 (approval/question) or 5, `apns-collapse-id`, expiration now+86400; body `{aps: {alert: {title-loc-key: "push.<kind>.title", loc-key: "push.<kind>.body"}, sound: "default", mutable-content: 1, interruption-level: time-sensitive|passive, thread-id: <kind>}, s: seq, r: reg}`.
- Answers 200 `{status: sent}`; 200 `{status: gone, since_ms}` (410, BadDeviceToken, DeviceTokenNotForTopic); 200 `{status: rejected, reason}` (other 4xx); 429/503 `{status: retry, after_s}` (own limits, APNs 429/5xx, network). Limits 30/h and 300/day per token, 600/h per source IP; logs hold `sha256(token)[:12]` only; no storage; `GET /v1/info` → `{topics, version}`; JWT reused ≤ 40 min.

### Device (watch and phone, service extension)
- Register at both sign-in paths and on every new token; `reg` is new at each sign-in.
- On a push: if `r` ≠ current `reg`, render passive "From an earlier sign-in"; else `GET /me/events?after=s-1&limit=1` and render like today's catch-up (approval/question time-sensitive with the "needs" userInfo; result/failure passive "<name> has a result"/"<name> failed"; notify passive with the published title). On timeout keep the localized generic text. The same notification id as the catch-up so nothing alerts twice.

## Acceptance criteria

- [ ] Routes: principal scoping, CSRF, token ownership moving between principals.
- [ ] Fake relay: one approval → exactly one call whose JSON keys equal `{topic, env, token, kind, collapse, seq, reg}`; unwiring the dispatcher turns the test red.
- [ ] First start over 500 old events sends nothing; restart with queued rows sends each (event, device) once; `attention.seen` before the send → zero calls.
- [ ] `gone` timestamp rule; relay down 2 h → rows drop at 1 h, ≤ 2 log lines, outbox bounded; split mode ≤ 3 s; `off`/no devices → no outbound socket.
- [ ] Relay unit tests: schema rejections, template, JWT reuse, status mapping, per-token limits.
- [ ] Operator E2E (sandbox): closed app shows "Approval needed" within 10 s, the extension replaces it with the real name, the next catch-up does not re-alert, watch + phone registered → one alert on the wrist.

## Operator decisions and hosting
- Host the relay (domain, the `.p8` key, team id) — then flip the packaged default of `--push-relay`.
- Time-sensitive entitlement on both App IDs; the watch's push entitlement.
- Whether to merge the two app families (until then: watch-first).

## Scope
- In: gateway routes, store, dispatcher, outbox, relay subcommand, console "Notifications" devices list, docs, tests; device side in abstractassistant (watch + iPhone) against this contract (built by the assistant seat).
- Out: other vendors' push; badges; silent sync pushes; a device-side toggle.

## References
- 1046, 1047, 1050; ADR-0040; `abstractgateway/events_stream.py`, `routes/me_events.py`, `mail/notifications.py`; watch `AnswerNotifier.swift`, `Auth.swift`.

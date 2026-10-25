# 1049 — Apple push relay for the watch and the phone

> Package: gateway, assistant
> Type: feature
> Created: 2026-10-25 12:50:00 +0200
> Priority: P2
> Labels: events-and-attention, push, apns, watch

## Summary

A `push` channel on the notification outbox: the watch and phone apps register an APNs device token per principal; a small relay run by the app's developer holds the APNs key and accepts signed requests from any self-hosted gateway; the gateway sends `attention.raised` as a push (alert) and `run.finished` as a silent push that refreshes the complication. Until then the watch uses the catch-up endpoint on its background refresh (1047).

## Why

True real time while the watch app is closed needs push. Gateways are self-hosted and the APNs key belongs to the app developer, so the key must not live in gateways.

## Scope

### In scope

- Token registration route, outbox channel, relay protocol (signed, replay-protected), relay reference implementation.

### Out of scope

- Any other vendor's push.

## Current code reality

- No push exists; the outbox has `console` and `email` (`mail/notifications.py`), 1046 adds `tray`.

## Acceptance criteria

- [ ] A test-fire reaches a closed watch app as a notification within seconds.

## Testing

- `cd abstractgateway && python -m pytest tests -q -k push_channel`

## References

- 1046, 1047; round-2 finding 7.

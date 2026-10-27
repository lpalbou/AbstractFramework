# 1058 — One push system: typed events delivered to every OS and to other systems

> Package: root (cross-package), abstractgateway (push/, routes/me_events.py), abstractruntime (events, automations notify), apps
> Type: architecture / feature
> Created: 2026-10-27
> Priority: P2
> Labels: push, events, notifications, apple, windows, linux, webhooks, replay

## Summary

Today push is Apple-only: `abstractgateway.push` (root 1049; gateway 0940 fixes "phone first") turns
`attention.raised` events of the caller's stream (root 1046, `/api/gateway/me/events`) into APNs requests
through the publisher-hosted relay. Desktop apps, Windows, Linux and other systems get nothing, and an
automation's `notify` (runtime `automations/models.py`) reaches only email (root 0992) or the tray.

Build ONE push system: typed events (CloudEvents-shaped, the same records the replayable ledger holds:
messages, events, artifacts, gates) are published once by the gateway and delivered by pluggable
transports: Apple push (existing relay), Windows toast and Linux desktop notifications (through the native
apps and the tray), web push for browser apps, an outbound signed webhook (Standard Webhooks, the mirror of
the inbound trigger ingress of 1042) for other systems, and the in-app SSE stream that already exists.
Apps and workflows push in one way (`push(event)`), the transport is the person's device registration.

## Why

Operator, 2026-10-27: "a unified push system that we can wire to different OS while abstracting how it
works; then for any app or system, we can just push (typed) events in a unified manner… it seems related to
the replayable ledger of messages, artifacts, events and gates."

## Design constraints

- Source of truth stays the ledger and the per-user event stream (1046): a push is a delivery of an event
  that exists, with its `seq`, never a second record. The replay view (0993, runtime 0853) is what a device
  opens on tap.
- Typed: an event schema id per kind (attention.raised, run.waiting_for_approval, artifact.ready, …), a
  localized fixed message per kind on the transport side (no free text crosses a relay).
- Registration is per device and per account with explicit channels (today's `PUT /me/push/devices`),
  one table for every transport.
- Delivery is at-least-once with a durable outbox per transport (today `push/store.py` SQLite outbox) and a
  dead-letter the console shows.
- Security: outbound webhooks signed, destinations allow-listed per account, admin-visible; RBAC per 1060.
- Performance: no transport may block the event loop or the run that raised the event (1060 latency rule).

## Links

- Existing: gateway `push/` (1049), `routes/me_events.py` (1046), triggers ingress (1041/1042, inbound
  mirror), `mail/notifications.py` (0992), runtime `automations/attention.py` (notify payloads).
- Related: 0993 (replay view), 1056 (workflows as the primitive: `notify` is a workflow effect), 1059, 1060.

## Acceptance (for promotion to planned)

- [ ] ADR in the gateway: one event publication, N transports; the APNs path becomes transport #1 unchanged.
- [ ] A second transport proven end to end (outbound webhook or Linux/Windows desktop) with a test that goes
      red when the transport is removed.

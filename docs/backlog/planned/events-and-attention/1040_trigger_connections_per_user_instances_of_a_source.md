# 1040 — Trigger connections: per-user instances of a source

> Package: runtime
> Type: feature
> Created: 2026-10-25 12:50:00 +0200
> Priority: P1
> Labels: events-and-attention, runtime, triggers, connections

## Summary

A `TriggerConnection{connection_id, principal, source_id, source_version, config (sealed secrets), status, created_at, last_event_at}` store in the runtime plane, a `needs_connection` flag on `TriggerSource` descriptors, and bindings that reference `connection_id`. A source is a type (email received, feed item, webhook received); a connection is this user's mailbox, this feed URL, this webhook secret, reusable across automations and sessions.

## Why

The operator wants to register the events one can listen to once, in the gateway, and reuse them from any automation or session, as simply as n8n. The registry of source types already exists; what is missing is the per-user instance layer.

## Scope

### In scope

- `TriggerConnectionStore(plane_dir)` with list/get/create/update/delete, JSON files, atomic writes, secrets sealed with the plane's existing sealing (same mechanism as email accounts).
- `TriggerSource.needs_connection: bool` and `connection_schema` in the descriptor; host validation of a binding's `connection_id` at create time (adapters stay pure).
- Inbox streams keyed by connection: `stream = f"trigger:{connection_id}"`; `recent events` = `EventInbox.read(stream, after_seq)`.
- Test-fire = append a synthetic envelope `{data: {test: true}}` to the connection's stream (manual@1 is the precedent).

### Out of scope

- The console page and HTTP routes (1041).
- Multi-binding controller (N bindings = N automations in v0).

## Current code reality

- `triggers/registry.py:28-41` registry + entry points; `GET /api/gateway/trigger-sources` (`routes/automations.py:119-141`).
- `email/inbox.py` `EventInbox{append(stream, event_id, payload, dedupe_key)→seq; read(after_seq, stream)}`, fcntl-serialized, retention 90 d / 10k with consumer-cursor protection.
- `email_received.py:231, 274-278`: `account` enum `["self"]` refuses anything else.

## Acceptance criteria

- [ ] A connection can be created, listed, updated and deleted per principal; another principal cannot see it.
- [ ] A binding with an unknown or foreign `connection_id` is refused at create time with a clear error.
- [ ] `EventInbox.read(stream="trigger:<id>")` returns the events a test-fire appended.

## Testing

- `cd abstractruntime && python -m pytest tests -q -k 'connection or inbox'`

## References

- Round-2 finding 3.
- [0929](../0929_automations_v2_external_triggers_durable_inbox.md)

## Receipts

- design note: `untracked/design/attention-triggers-replay-2026-10-25.md` (two adversarial rounds)

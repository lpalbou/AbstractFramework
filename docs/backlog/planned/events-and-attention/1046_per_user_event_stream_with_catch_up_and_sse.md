# 1046 — Per-user event stream with catch-up and SSE

> Package: gateway
> Type: feature
> Created: 2026-10-25 12:50:00 +0200
> Priority: P0
> Labels: events-and-attention, gateway, events, attention, sse

## Summary

The gateway writes a per-user stream `user:<principal>` in the `EventInbox` holding only what is not a step of a run: trigger events, `wake.scheduled|cancelled`, `attention.raised|seen`, `notification.sent|failed`, and pointers `run.started|finished {run_id, session_id, origin}` (written after the run store save with `event_id = "run.started:<run_id>"`, idempotent, rebuildable). It serves `GET /api/gateway/me/events?after=<seq>&limit=` and `GET /api/gateway/me/events/stream` (SSE, `id` = seq, `Last-Event-ID`). Prerequisite bug: mailbox fan-out and due tracking stop depending on `run_scan_limit` (use the by-key waiter path).

## Why

Every client polls full pages today and the watch waits 15 minutes; a per-user ordered stream is the one transport all apps can share, and the record that makes every ping explainable. Round 1 found that the 500-cap mailbox and the 200-run scan silently lose events.

## Scope

### In scope

- Writers in the host for the five event families; attention events carry the ledger `record_key`, not a body copy.
- Catch-up and SSE routes with principal scoping; heartbeat; `after` semantics identical to the ledger stream.
- Fan-out via `list_event_waiters` by key (`json_files.py:1521`) instead of `list_runs(limit=run_scan_limit)`; due tracking without the cap.
- Notification outbox channels `console` and `tray` recorded as `notification.sent`.

### Out of scope

- APNs push relay (proposed separately).
- Session index and reducer corpus (0993).

## Current code reality

- SSE exists only per object (`/runs/{id}/ledger/stream`, entity replay, model downloads).
- `runner.py:2407-2417` fan-out via `list_runs(RUNNING|WAITING, limit=run_scan_limit)`; `:1432-1436` due tracking degrades past the cap; `json_files.py:1313-1317` documents the starvation hole.
- `attention.py:14-17` attention records in controller ledgers; per-principal seen cursors in `routes/automations.py:152`.

## Acceptance criteria

- [ ] With 300 parked automations, a durable emit_event reaches its mailbox and a wake fires on time (regression test).
- [ ] A client with `Last-Event-ID` reconnects and misses nothing; two principals never see each other's events.
- [ ] `run.started` pointers are rebuilt idempotently after a simulated crash between save and append.

## Testing

- `cd abstractgateway && python -m pytest tests -q -k 'me_events or fanout or attention_stream'`

## References

- Round-1 F2/F3, round-2 findings 6 and 7.

## Receipts

- design note: `untracked/design/attention-triggers-replay-2026-10-25.md` (two adversarial rounds)

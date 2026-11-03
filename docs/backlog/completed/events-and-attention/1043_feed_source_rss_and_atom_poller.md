# 1043 — Feed source: RSS and Atom poller

> Package: runtime
> Type: feature
> Created: 2026-10-25 12:50:00 +0200
> Priority: P2
> Labels: events-and-attention, runtime, feed, rss

## Summary

A `feed.item@1` trigger source (connection config: `url`, `every` ≥ 60 s, `max_batch`) polled by a feeder that parses RSS 2.0 and Atom, appends one envelope per new item (`subject` = item id or link, `dedupekey` = the same, `data` = title, link, published, summary, author) to the connection's stream, and coalesces into one admission per tick.

## Why

The operator named news feeds as an event source and as a test bed. Feeds are the simplest external stream with a stable standard.

## Scope

### In scope

- Parser with stdlib only (xml.etree), conditional GET (ETag / Last-Modified), per-connection cursor, bounded item count.
- Feeder wired like the email watcher (poll loop owned by the gateway plane).

### Out of scope

- WebSub push (needs a public callback).
- Full-text fetching of linked pages.

## Current code reality

- No feed support exists; `email_received.py` is the batching precedent (never below 60 s).

## Acceptance criteria

- [ ] Against a recorded fixture and against one reputable live feed, new items appear once each; a second poll adds nothing.
- [ ] A bound automation runs with `input_data.event.data.title` set.

## Testing

- `cd abstractruntime && python -m pytest tests -q -k 'feed'`

## References

- Round-2 v0 list item 6.

## Receipts

- design note: `untracked/design/attention-triggers-replay-2026-10-25.md` (two adversarial rounds)

## Completion report

> Completed: 2026-10-25 18:30:00 +0200
> Original path: `docs/backlog/planned/events-and-attention/1043_feed_source_rss_and_atom_poller.md`
> Final path: `docs/backlog/completed/events-and-attention/1043_feed_source_rss_and_atom_poller.md`

**Outcome.** feed.item@1 (RSS 2.0 + Atom, conditional GET, coalescing, human field titles) polled by the gateway's worker tick only while used; proven live on the operator's BBC connection. Tests: feed fixtures + network-marked live test.

**Commits.** runtime 643b2dc, d12d605 (all local, unpushed, unpublished; per-repo receipts under `untracked/lanes/`).

**Validation.** Lane receipts with per-item mutation checks: `untracked/lanes/L1-runtime.md`, `L2-gateway-triggers.md`, `L3-gateway-events.md`, `L4-flow-console.md`, `L5-consumers-e2e.md`, `UX-A-flow.md`, `UX-O-observer.md`; UX reviews `untracked/ux-review/REPORT.md` and `REPORT-2.md`; live evidence `abstractgateway/untracked/live-email-2026-10-25/`.

**Follow-ups.** See proposed [1050](../../proposed/1050_events_and_attention_follow_ups.md).

# 1048 — End-to-end examples, tests and documentation for events and attention

> Package: framework
> Type: task
> Created: 2026-10-25 12:50:00 +0200
> Priority: P1
> Labels: events-and-attention, docs, e2e, coredoc

## Summary

Three documented, tested end-to-end examples: (1) "watch my second mailbox and tell me when something important arrives" (email.received on the second account, an LLM judgement in the occurrence, attention raised, received in the tray, Assistant and watch); (2) "a digest of a news feed" (feed.item on a reputable RSS feed); (3) "run this flow when an external system calls my webhook" (signed curl). Then the coredoc pass on every touched package (docs, llms files, changelog, version) without publishing.

## Why

The operator asked for 2–3 end-to-end examples covering registering an event, designing what runs on it in Flow, and receiving the push in the apps, plus tests against the two registered accounts and a news feed.

## Scope

### In scope

- Hermetic gateway on a scratch port and data dir for the automated tests; a live run against the operator's gateway for the email example with their two accounts, with the operator informed before the gateway is restarted on the new code.
- Docs: gateway (triggers, connections, webhooks, events stream), runtime (sources, envelope, SCHEDULE_RUN), Flow (triggerable flows), apps; changelogs; versions bumped, nothing published.

### Out of scope

- Publishing any package (needs the operator's explicit go per release).

## Current code reality

- See the items above.

## Acceptance criteria

- [ ] The three examples pass in a hermetic run and are documented with the exact commands.
- [ ] The email example ran once for real between the operator's two accounts, with the notification received on at least two apps; evidence kept under `untracked/`.
- [ ] Coredoc pass complete: core doc set, llms.txt / llms-full.txt regenerated, changelogs, version bumps.

## Testing

- `cd abstractgateway && python -m pytest tests -q -k 'e2e_events'`

## References

- All items of this track.

## Receipts

- design note: `untracked/design/attention-triggers-replay-2026-10-25.md` (two adversarial rounds)

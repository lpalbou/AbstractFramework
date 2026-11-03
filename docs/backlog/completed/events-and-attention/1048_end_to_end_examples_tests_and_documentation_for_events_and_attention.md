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

## Completion report

> Completed: 2026-10-25 18:30:00 +0200
> Original path: `docs/backlog/planned/events-and-attention/1048_end_to_end_examples_tests_and_documentation_for_events_and_attention.md`
> Final path: `docs/backlog/completed/events-and-attention/1048_end_to_end_examples_tests_and_documentation_for_events_and_attention.md`

**Outcome.** Three hermetic E2E examples (webhook, feed digest, mailbox watch incl. second mailbox) + docs/events-examples.md; live email test on the operator's gateway passed end to end (mail → inbox → automation → local-model judgement → attention → tray/console/email); coredoc passes with local version bumps (core 2.29.0, runtime 0.12.0, agent 0.4.0, gateway 0.16.0, flow 0.11.0, code 0.11.0/0.12.0, assistant 0.15.0, watch 0.5.0, iPhone 0.7.0, ui-kit 0.8.8); nothing published.

**Commits.** gateway 67f1dd52, 7b9e202e, a549635b, 7a0888ad, 74fa8767; runtime b0b55d1, d4439f9; agent 63b05f4; flow f809f2f, 9889731, 8a15724; code 25917d6; assistant 3cc77d5, 656f5d8; abstractcore 833cba05 (all local, unpushed, unpublished; per-repo receipts under `untracked/lanes/`).

**Validation.** Lane receipts with per-item mutation checks: `untracked/lanes/L1-runtime.md`, `L2-gateway-triggers.md`, `L3-gateway-events.md`, `L4-flow-console.md`, `L5-consumers-e2e.md`, `UX-A-flow.md`, `UX-O-observer.md`; UX reviews `untracked/ux-review/REPORT.md` and `REPORT-2.md`; live evidence `abstractgateway/untracked/live-email-2026-10-25/`.

**Follow-ups.** See proposed [1050](../../proposed/1050_events_and_attention_follow_ups.md).

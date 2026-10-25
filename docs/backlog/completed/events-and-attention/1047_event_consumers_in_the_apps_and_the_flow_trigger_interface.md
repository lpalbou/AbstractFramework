# 1047 — Event consumers in the apps and the Flow trigger interface

> Package: assistant, code, gateway, flow
> Type: feature
> Created: 2026-10-25 12:50:00 +0200
> Priority: P1
> Labels: events-and-attention, apps, flow, tray, watch, tui

## Summary

Every app consumes the per-user stream: the gateway tray (OS notification per `attention.raised`, badge count), the Assistant desktop (banner + tray badge; replaces the full-page polls), the watch (catch-up endpoint on each refresh and at launch; complication from it), Code TUI (attention chip from the stream instead of 15 s polls) and WUI. Flow: the automation trigger picker gains a connection selector for sources with `needs_connection`, and a triggerable flow declares an `event` input pin (the CloudEvents envelope) that `on_trigger`/the entry node exposes as outputs.

## Why

This is the (c) of the operator's end-to-end: receiving the push in the apps that can accept it, and the (b): designing what runs on an event in Flow with the envelope as structured input.

## Scope

### In scope

- One client per app against `/me/events` + SSE with reconnect; unseen counts derived from `attention.raised` minus `attention.seen`.
- Flow selector + `event` pin + docs; Flow validation that a triggerable flow has the pin.

### Out of scope

- APNs push to the watch (proposed).
- New UI beyond a banner, badge, chip and the selector.

## Current code reality

- TUI polls 15 s summing `pending_waits+unseen_count` (`attention.rs:23-27`); tray polls `GET /automations?limit=50` (`tray/client.py:133-137`) and has OS notifications (`tray/app.py:547`); watch projects `/runs?status=waiting` (`GatewayClient.swift`) on a 15-min refresh; Flow already offers every trigger source (`triggerSources.ts`, `AutomationDefaultsModal.tsx`) with forms from `config_schema`.

## Acceptance criteria

- [ ] A test-fire on a connection bound to an automation produces, within seconds, an OS notification from the gateway tray and the Assistant desktop, a chip change in the TUI, and the watch complication after its next refresh.
- [ ] A flow created from `+ New automation` with a feed connection runs with `event.data.title` available on the entry node.

## Testing

- `cd abstractcode && cargo test -p abstractcode-tui attention`
- `cd abstractassistant && python -m pytest tests/basic -q -k 'events or attention'`
- `cd abstractflow && npm test -- trigger`

## References

- 1046 (transport), 1040/1041 (connections).

## Receipts

- design note: `untracked/design/attention-triggers-replay-2026-10-25.md` (two adversarial rounds)

## Completion report

> Completed: 2026-10-25 18:30:00 +0200
> Original path: `docs/backlog/planned/events-and-attention/1047_event_consumers_in_the_apps_and_the_flow_trigger_interface.md`
> Final path: `docs/backlog/completed/events-and-attention/1047_event_consumers_in_the_apps_and_the_flow_trigger_interface.md`

**Outcome.** Assistant desktop, watch, iPhone, Code TUI and WUI follow the stream with dedupe; Flow: automation-first New flow, human trigger picker, Growing budget from the gateway default, typed start/end pins, Turn it on (one automation per flow), Run as if triggered with real sampled data, Email type, Mail nodes, Publish to channel; Observer: prefilled form, triggers in words, run card. Tests: desktop 1289, watch 101, AssistantKit 276, code terminal 1138 / web 493, flow 1173, observer 663.

**Commits.** assistant 206ea46, 3a3f6d1, c7005b8, 56dce7e, 09a2ab8, 8e1187a, 8800e9f, 69aa5d8, 97df40b, b69e7f4; code 9b7b4b0, df2e024, 39cf558; flow 4441300 … b6041a9 (22 commits); observer/ui-kit per the UX-O receipt (all local, unpushed, unpublished; per-repo receipts under `untracked/lanes/`).

**Validation.** Lane receipts with per-item mutation checks: `untracked/lanes/L1-runtime.md`, `L2-gateway-triggers.md`, `L3-gateway-events.md`, `L4-flow-console.md`, `L5-consumers-e2e.md`, `UX-A-flow.md`, `UX-O-observer.md`; UX reviews `untracked/ux-review/REPORT.md` and `REPORT-2.md`; live evidence `abstractgateway/untracked/live-email-2026-10-25/`.

**Follow-ups.** See proposed [1050](../../proposed/1050_events_and_attention_follow_ups.md).

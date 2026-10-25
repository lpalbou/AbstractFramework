# 1042 — Webhook source with signed ingress

> Package: gateway, runtime
> Type: feature
> Created: 2026-10-25 12:50:00 +0200
> Priority: P1
> Labels: events-and-attention, gateway, runtime, webhook

## Summary

A `webhook.received@1` trigger source (config: content expectations, optional JSON path for `subject`) and a public ingress `POST /api/gateway/triggers/webhooks/{connection_id}` verified per Standard Webhooks (`webhook-id`, `webhook-timestamp`, `webhook-signature` HMAC-SHA256 with the connection's secret, replay window), appending a CloudEvents-shaped envelope to the connection's inbox stream and waking its consumers.

## Why

Webhooks are the universal way external apps deliver events (n8n, Zapier, GitHub, Stripe). With a signed ingress any external system can trigger an automation without new code per system.

## Scope

### In scope

- Runtime source + feeder; gateway route outside the bearer-token family (signature is the auth), rate limited, body size capped, origin allowlist not applied.
- Unsigned or stale requests refused with 401/409; duplicates (same `webhook-id`) deduped by `dedupekey`.
- Wake of consumers of the stream (generalise `wake_email_automations`).

### Out of scope

- Outbound webhooks (egress, 0073).
- Public reachability (Tailscale funnel, port forwarding) is the operator's.

## Current code reality

- No ingress exists; `POST /api/gateway/commands {type: emit_event}` needs the bearer token.
- `email/automations.py:41-66` `wake_email_automations` wakes consumers of the email stream.

## Acceptance criteria

- [ ] A signed POST creates one inbox event and wakes a bound automation; the occurrence receives `input_data.event` with the body as `data`.
- [ ] A tampered signature, a timestamp outside the window, and a replayed id are each refused and recorded.
- [ ] Documented curl example in the gateway docs.

## Testing

- `cd abstractgateway && python -m pytest tests -q -k 'webhook'`

## References

- Standard Webhooks spec.
- Round-2 finding 4.

## Receipts

- design note: `untracked/design/attention-triggers-replay-2026-10-25.md` (two adversarial rounds)

## Completion report

> Completed: 2026-10-25 18:30:00 +0200
> Original path: `docs/backlog/planned/events-and-attention/1042_webhook_source_with_signed_ingress.md`
> Final path: `docs/backlog/completed/events-and-attention/1042_webhook_source_with_signed_ingress.md`

**Outcome.** webhook.received@1 with Standard Webhooks verification; public ingress POST /triggers/webhooks/{id} (401/409/404/413/429); docs with set-up and try-it walkthroughs (GitHub's own signature not accepted: follow-up 1050). Tests: webhook ingress + e2e 22 passed.

**Commits.** runtime f0552dd; gateway 55ef99a3, d3db1324, 08bd9459 (all local, unpushed, unpublished; per-repo receipts under `untracked/lanes/`).

**Validation.** Lane receipts with per-item mutation checks: `untracked/lanes/L1-runtime.md`, `L2-gateway-triggers.md`, `L3-gateway-events.md`, `L4-flow-console.md`, `L5-consumers-e2e.md`, `UX-A-flow.md`, `UX-O-observer.md`; UX reviews `untracked/ux-review/REPORT.md` and `REPORT-2.md`; live evidence `abstractgateway/untracked/live-email-2026-10-25/`.

**Follow-ups.** See proposed [1050](../../proposed/1050_events_and_attention_follow_ups.md).

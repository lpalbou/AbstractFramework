# 1050 — Events and attention follow-ups named by the lanes

> Package: gateway, runtime, assistant, observer
> Type: task
> Created: 2026-10-25 18:30:00 +0200
> Priority: P2
> Labels: events-and-attention, follow-up

## Summary

The follow-ups the 2026-10-25 wave left open, each small and independent, kept here so they are not lost in lane receipts.

## Why

Named by the workers and the two UX reviews (`untracked/ux-review/REPORT-2.md`); none blocks the local deployment, several block a release.

## Scope

### In scope

- Release prerequisites: merge the diverged abstractgateway `main` with `origin/main` (31 commits behind incl. 0.15.2–0.15.11); publish order abstractcore 2.29.0 → abstractruntime 0.12.0 → abstractagent 0.4.0 → abstractgateway 0.16.0 → ui-kit 0.8.8 → observer (dependency `^0.8.8` + lockfile) → flow → assistant/code → root pins; Observer CI installs kit 0.8.7 until then.
- Operator-side configuration: the admin's `endpoint:airelay` key is refused for background runs (401); a Google OAuth client registered on the gateway (or a built-in client shipped, a publisher decision) so "Sign in with Google" appears.
- Webhooks: accept GitHub's `X-Hub-Signature-256` and Svix-style headers, or document a relay; outbound webhook egress (0073) for servers.
- Push: APNs relay (1049) for the watch and phone; the time-sensitive entitlement on the App IDs (operator decision).
- Mail: the runtime resolves any of the person's mailboxes by address (needs a mailbox list from the gateway); the terminal console still calls the older `/me/email/discover`; password-added mailboxes show provider "imap" (derive from the IMAP host).
- Automations: an `automation.changed` stream event so the tray can drop its 5-minute reconciliation; `schedule_run` for CodeAct/MemAct agents; occurrence rows could carry what arrived so Observer skips one read per run.
- Pre-existing red: `POST /api/gateway/entities/{name}/sessions` lacks an authorization decision (operator commit fd57f04e).
- Backlog 0993 (session index + projection corpus) and 0991 (admission + model residency) stay the next architecture steps.

### Out of scope

- A bus beside the ledger (rejected by two adversarial rounds).

## Acceptance criteria

- [ ] Each bullet above is either done with evidence or moved to its own item.

## Testing

- `cd abstractgateway && python -m pytest tests/test_gateway_route_authorization_contract.py -q`

## References

- Completed track [events-and-attention](../completed/events-and-attention/README.md); design `untracked/design/attention-triggers-replay-2026-10-25.md`.

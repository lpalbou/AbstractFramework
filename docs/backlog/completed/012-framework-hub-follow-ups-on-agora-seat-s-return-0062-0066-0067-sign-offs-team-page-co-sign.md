# 012-framework: [TASK] Hub follow-ups on agora seat's return: 0062/0066/0067 sign-offs + Team-page co-sign

> Package: framework
> Type: task
> Created: 2026-07-14 05:55:55 +0200
> Priority: P2
> Labels: decision-gate

## Summary
Delegated sign-offs (0062 dead-ask closure authority, 0066, 0067) plus the Team page hub-side co-sign wait on the agora seat's return; agency holds the delegate record of what was agreed.

## Why

Operator delegated sign-off authority to agency for hub rulings 0062/0066/0067 in their absence; the agora seat was dark when the rulings landed. The Team page (continuum) consumes the hub API and its contract deserves the hub owner's co-sign.

## Scope

### In scope

- 0062/0066/0067 signed off on the hub with receipts
- Team page contract co-signed by agora (allowlist, ack semantics, authorship rules)
- Decision keys recorded in the commons store

### Out of scope

- Re-litigating the rulings themselves (already ruled)
- New hub features

## Acceptance criteria

- [x] Each sign-off posted with receipt (agora c2340: 0062/0066/0067 shipped in agorahub 0.9.0, live on this hub)
- [x] Team-page co-sign recorded (decision:team-page-hub-cosign; continuum's c2268 confirms the endpoint map landed with zero hub gaps)

## Receipts

- Delegation: operator DM (2026-07-13); Team page contract: c1696; rulings thread: 0062/0066/0067
- STATUS 2026-07-15 (framework backlog reconciliation): agora seat back and active; asked for status on commons c2339 ask 1.
- CLOSED 2026-07-15 (agora c2340, same hour): the WORK had shipped in agorahub 0.9.0 (0062 closure semantics per ADR-0003, 0066 addressed-scoped stickiness, 0067 dark-episode alerts); the missing store RECORDS now exist — decision:delegate-signoff-0062-0066-0067 + decision:team-page-hub-cosign (commons store). Thread closed by asker (framework) citing both keys.

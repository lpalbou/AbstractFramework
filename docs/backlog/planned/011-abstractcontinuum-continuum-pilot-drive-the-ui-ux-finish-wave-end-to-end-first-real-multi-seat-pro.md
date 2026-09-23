# 011-abstractcontinuum: [TASK] Continuum pilot: drive the UI/UX finish wave end-to-end (first real multi-seat project)

> Package: abstractcontinuum
> Type: task
> Created: 2026-07-14 05:55:55 +0200
> Priority: P2
> Labels: decision-gate

## Summary
OPERATOR DECISION GATE (never assignable): GO pending. On GO, continuum drives the UI/UX wave through its own machinery end-to-end: intake cards, DoR gate, dispatch (hub or exec pipeline), Supervision tracking, verified closes. Agency stays verifier/escalation.

## Why

OPERATOR DECISION GATE: operator ruled "what we do should actually be supervised in continuum" and asked "how ready is continuum to try to handle a project?" (c2022). Agency answered pilot-ready with this exact wave as the recommended pilot (c2041, B1 detail c2067). GO = operator word + first findings batch.

## Scope

### In scope

- Wave cards flow finding -> card -> DoR -> dispatch -> verify -> promote inside continuum
- Operator follows the wave from :3003 Supervision without asking agency for state
- Retro note: what the pilot proved/broke

### Out of scope

- Replacing agency's delegate briefs (tables continue, reading FROM the board)
- Forcing the exec pipeline where hub dispatch fits better

## Acceptance criteria

- [ ] All wave cards tracked in continuum with receipts
- [ ] Operator can name the wave state from Supervision alone
- [ ] Retro posted; failure mode honored (direct dispatch resumes same-hour if stalled)

## Receipts

- B1 detail: commons c2067; readiness answer: c2041
- GATE: operator GO (pending)

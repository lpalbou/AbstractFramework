# 007-framework: [TASK] UI/UX finish wave: operator re-test findings intake and fix dispatch

> Package: framework
> Type: task
> Created: 2026-07-14 05:55:55 +0200
> Priority: P1
> Labels:

## Summary
Operator re-tests the 7-item menu (purge refusal, phase radio + own-time arming, cognition meter, graph hover/click, observer fast-connect, supervision view, sign-in modal) plus the Team page on the fresh :8080/:3003 serve. Each finding becomes a child card dispatched to the owning seat.

## Why

Operator (2026-07-13/14): "i have asked a lot of improvements on the UI/UX side today. it's not yet finished." The re-test after the 03:42 stack bounce is the acceptance pass for the whole UI/UX wave; findings must not live in chat scrollback.

## Scope

### In scope

- Intake: one child card per operator finding (owner, repro, acceptance named)
- Dispatch to owning seat (uic / entity / observer / gateway / continuum) via hub or exec pipeline
- Run-verified closes, promoted with receipts

### Out of scope

- New feature requests beyond the tested surfaces (separate cards)
- The continuum-pilot question itself (card 011)

## Acceptance criteria

- [ ] Every operator finding from the re-test recorded as its own card with owner + repro
- [ ] Each fix verified by running (co-sign discipline), promoted with receipt
- [ ] Wave closes when the operator says the menu passes

## Receipts

- Test menu: dm:agency--laurent seq 32 (2026-07-14 03:45)
- Stack bounce receipt: commons c2013
- Migration claim: claim:agency-board-to-continuum (commons store)

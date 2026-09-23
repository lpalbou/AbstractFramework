# 010-framework: [TASK] agora-collaboration skill: re-derivation, adversary pass, co-sign, shelf promotion

> Package: framework
> Type: task
> Created: 2026-07-14 05:55:55 +0200
> Priority: P2
> Labels:

## Summary
Skill seat re-derives the agora-collaboration draft against the live hub 0.10.0 contract from both ruled sources (AgoraHub SKILL.md @ pinned hash + operator guidance doc), folds the fleet-bench context-cost finding (failure ledger moves to references/), runs a fable5 adversary, then requests designer co-sign before shelf promotion.

## Why

Operator ruling (c1764): the skill = adopt + co-author from AgoraHub's SKILL.md. The fleet bench (--skill arm) is the acceptance vehicle; its context-cost finding on small models is already folded into the design. Skill seat claimed this lane (c2086).

## Scope

### In scope

- Re-derivation against 0.10.0 (anti-lurk mechanics, owed-debt wake, per-ask addressing)
- fable5 adversary pass + findings folded
- Designer co-sign request; shelf promotion with bench evidence in the validation record

### Out of scope

- Hub-side protocol changes (agora seat's lane)
- New bench choreography (existing 3-seat bench is the acceptance)

## Acceptance criteria

- [x] Re-derived draft + adversary report posted on commons (c2124 — 2P0+7P1 folded)
- [x] Designer co-sign recorded (c2255 conditional → P1 fixed → c2374 UNCONDITIONAL on tree 8f7f9453…); skill PROMOTED to shelf (c2402 — commit 9505213, byte-identical tree, 156 green, shelf at 12 skills)
- [x] Bench evidence (c1833) linked in the validation record (named as behavioral evidence; agency's v1.1 re-run stays open at their return, non-gating per the designer)

## Receipts

- Skill claim: commons c2086 (claim:agora-collaboration-rederivation)
- Ruling: c1764; bench: c1833
- STATUS 2026-07-15 (framework backlog reconciliation): re-derivation + fable5 DONE per skill's claim record (c2124 — tree 366d7d286b62c382…, commit 23132dc, 2P0+7P1 folded).
- CORRECTED 2026-07-15 (agora c2340): the designer co-sign was DELIVERED at c2255 (17:47), CONDITIONAL on one P1 — the DM ballot template lost the vote tag (parser requires it) — plus 2 P2s. The ball is skill's: fix the P1, post the corrected tree hash; agora's co-sign stands on it without re-review, then shelf promotion proceeds. NOTE: skill seat is OFFLINE as of this note (hub presence + dark-episode alerts) — the P1 fix waits for its return.
- CLOSED 2026-07-15 evening (skill c2371 fix → agora c2374 unconditional co-sign → skill c2402 PROMOTION): registry/skills/agora-collaboration live at commit 9505213, tree byte-identical to the co-signed 8f7f9453…, SHELF_POLICY + validation record (12 records) carry the full provenance chain; agency's v1.1 re-run left open at their timing, explicitly non-gating (designer's word) — promotion is not immunity, a later FAIL reopens a fix wave. Framework's c2398 reachability datum (agency dark) is cited in skill's closure as the deciding fact.

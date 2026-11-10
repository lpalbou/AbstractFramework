# 1194 — The night's authoring budget as a Mind setting (`sleep.authoring_budget`)

> Package: AbstractRuntime (cognition profile + `build_consolidator` authoring_cap), AbstractGateway (cognition-profile route GET/PUT), AbstractEntity (Sleep card field)
> Type: feature
> Status: planned
> Created: 2026-11-10
> Priority: P2
> Labels: entities, sleep, authoring, mind-settings, next-wave

## Summary

The number of title/summary authoring calls a sleep may spend (today a runtime constant, 64 per night; the topics stage
reserves 25 % of it before the repair) is not a Mind setting. The operator asked on 2026-11-10 how fast an entity's
backlog of untitled memories gets repaired; the honest answer was "about ten nights at the default budget, not raisable
from the app". Expose it like the other sleep fields: `sleep.authoring_budget` (integer ≥ 1, default 64) in the
cognition profile, validated with a sentence + code, served and set through the existing cognition-profile route, a
field in the Entity app's Sleep card beside after_hours / after_events / after_fragmented_share.

## Current code reality (2026-11-10)

Runtime 0.19.0 `identity/life.py` build_consolidator: `authoring_cap` constant; the topics share `TOPICS_AUTHORING_SHARE
= 0.25` taken before the repair; memory's `communities_pass(budget=)` gets the remainder. Cognition profile `sleep`
block: after_hours, after_events, after_fragmented_share only. Entity 0.12.0 Sleep card shows those three.

## Validation

A profile with `sleep.authoring_budget: 200` makes the next night declare/author up to 200 fields (repair 150 + topics
50); an invalid value is refused with the sentence; the Entity app field round-trips; red tests on each layer.

## Related

1146 (titles), 1190, 1191, 1193; the communities design (graph-topics/COMMUNITIES-DESIGN.md).

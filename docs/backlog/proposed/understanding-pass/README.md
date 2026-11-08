# Understanding pass backlog track (proposed half)

## Status

Proposed. The track index, the landed commits and the governing ADRs live in the planned half:
[`../../planned/understanding-pass/README.md`](../../planned/understanding-pass/README.md).
Paused by operator ruling 2026-11-08 (pause all dev); resume = explicit go.

## Items

- [1172](1172_ripple_revise_election_and_wake_cue.md): the entity's `revise` election seeds a ripple, the drain
  runs the reconsiderations, sleep consolidates them and the wake cue says so (runtime draft 0870 over memory 0061).
  Depends on [1171](../../planned/understanding-pass/1171_understanding_drain_in_turns_and_idle_windows.md).
- [1173](1173_extraction_capability_gets_its_consumer.md): the `extraction` capability (configurable, set to
  theforge on nerin) gets the consumer it was reserved for (memory 0050/0051).

## Reading order

1171 first (the drain both items use), then 1172, then 1173.

## Promotion criteria

1171 merged and live; the operator's go for the item; for 1172 the ripple's distance threshold calibrated from the
backfill's repeated rewrites (memory ADR 0001 d1); for 1173 memory 0050/0051 built.

## Non-goals

Surprise as a feeling or valence (operator: words only for now); retiring the night voice's 20 h throttle (1150).

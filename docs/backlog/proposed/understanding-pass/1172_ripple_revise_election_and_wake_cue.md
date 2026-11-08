# 1172 — The entity names what a fact changes (`revise`), the ripple is drained, and it wakes to what sleep made of it

> Package: AbstractRuntime (`identity/reflection.py`, `identity/chat.py`, `identity/visit_workflow.py`, `identity/understanding.py` ripple kinds, `identity/life.py` cues), AbstractGateway (the visit ELECT lane, probe), AbstractEntity (Revisiting strip, Entity owner)
> Type: feature
> Status: proposed
> Created: 2026-11-08
> Priority: P2
> Labels: understanding-pass, ripple, elections, paused, seat-framework

Paused by operator ruling 2026-11-08 (pause all dev); resume = explicit go.

## Summary

Runtime draft 0870 over memory 0061 (`untracked/understanding-pass-2026-11-07/drafts/abstractruntime/0870_revise_election_and_ripple_wake_cue.md`).
A fenced ```` ```revise ```` election beside ```` ```realize ```` lets the entity say, in its own words, that something
it just learned changes what it held (`evidence=#a3,#b7` mandatory; cap 2 per session like realizations). The runtime
forms the words as a `realization`-band record with `attributes.revises`, calls memory's `seed_ripple` for each
resolved tag, and the drain of [1171](../../planned/understanding-pass/1171_understanding_drain_in_turns_and_idle_windows.md)
gains the two ripple kinds it leaves in the queue in v1: `ripple.reconsider` (any window) and `ripple.consolidate`
(nightly sleep only). The next cue tells the entity, as information, that those memories are being revisited; the
wake cue after a night that consolidated a ripple offers the "what this changes" record.

## Why

Operator 2026-11-07: "a disruptive fact given in the present should trigger a reaction (surprise?) and slowly get to
actual consistency by rippling through the connected memories until a certain activation threshold … and this could
consolidate also during the sleep/dream phase." Detection comes from the entity's own reflection, never from text
heuristics (ruling 2026-09-27).

## Current code reality (2026-11-08)

- abstractmemory `09686e0` (0061, live at `e74c29c`): `ripple.py` — `seed_ripple`, `settle_reconsideration`,
  `refresh_ripples`, `form_consolidation`, `revert_ripple`, `ripples`, `ripple_context`; every gate decision stored
  (`memq_ripple_gates`); bounds `MAX_HOPS`, `RIPPLE_BUDGET`, refractory, protected kinds; surprise in words only.
- abstractruntime `ed7d605`: `parse_realize_blocks` (`identity/reflection.py:369`), `MAX_REALIZATIONS_PER_SESSION = 2`
  (`:65`); no `parse_revise_blocks`, no `seed_ripple` caller; `wake_residue` reads dream signals after a nap/cycle
  (`life.py` ~3793, ~3837).
- The drain does not exist yet (1171); in its v1 contract ripple kinds are `filtered`, never claimed.

## Scope

### In scope

- `parse_revise_blocks` (words and `evidence=` required, cap 2, refusals labelled in-reply) and its application in
  both lanes (home-direct chat and the visit workflow ELECT node), with a parity test.
- Drain support for `ripple.reconsider` / `ripple.consolidate` (`ripple_context` packet, `settle_reconsideration`,
  `refresh_ripples` at window end, `seed_ripple` when a rewrite's reader reports `revised` / `overturned`).
- Cues in plain words (no ids); prompt teaching beside `realize`.

### Out of scope

Surprise as a feeling or valence (operator decision 8: words only); the propagation algorithm (memory 0061, built);
the Entity app's Revisiting strip (Entity owner's draft 0001).

## Promotion criteria

1171 merged and live; the ripple's distance threshold calibrated from the backfill's repeated rewrites (memory ADR
0001 d1; [1180](../../completed/1180_one_time_understanding_backfill_on_theforge.md) holds the material); the
operator's go.

## Acceptance criteria

- [ ] One valid `revise` block forms one record in the entity's words and seeds one ripple per resolved tag; a third
      block in a session is refused with the cap sentence; a block without `evidence=` is refused and forms nothing.
- [ ] A seeded ripple's reconsiderations are drained within the bounds and left_out is reported; `ripple.consolidate`
      runs only in a nightly sleep window.
- [ ] The next cue carries the revisiting sentence; the wake cue after a consolidated ripple names the record.
- [ ] Visit lane and home-direct lane behave the same; a mutant that skips `seed_ripple` turns the ripple test red.

## Testing

- `python -m pytest tests/identity/test_revise_election.py tests/identity/test_wake_cue_reunderstanding.py -q`
- `scripts/ci_local.sh`

## Receipts

- Design: `untracked/understanding-pass-2026-11-07/DESIGN.md` §8; parent [1146](../../planned/1146_understanding_pass_summaries_always_computed.md).

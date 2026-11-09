# Understanding pass backlog track

## Status

Mixed: planned (this folder), proposed ([`../../proposed/understanding-pass/`](../../proposed/understanding-pass/README.md))
and one completed record. **Paused by operator ruling 2026-11-08 (pause all dev); resume = explicit go**, item by item.

## Purpose

Every memory of an entity (episode, session summary, card, dream) used to be mechanical text. The understanding pass
makes the words model-written and keeps them current: rewritten in place with versions (memory 0059), queued as
memory tasks (memory 0060), drained by the runtime in turns and idle windows (1171), rippled through connected
memories when a fact changes what the entity held (1172), and released together (1179). The parent item is
[1146](../../completed/1146_understanding_pass_summaries_always_computed.md) (operator rulings, root cause, coordination; completed 2026-11-10 for the authored title-and-summary part, the rest stays in this track); the
authoritative design is `untracked/understanding-pass-2026-11-07/DESIGN.md` (§15 build plan, §17 operator decisions)
and its per-package drafts under `untracked/understanding-pass-2026-11-07/drafts/<repo>/`.

## Items

| ID | State | Item | Owner |
|---|---|---|---|
| [1171](1171_understanding_drain_in_turns_and_idle_windows.md) | planned, paused | The runtime drains the memory-task queue in turns and idle windows (runtime draft 0869 + the drain parts of gateway draft 1013) | framework seat (runtime + gateway halves) |
| [1172](../../proposed/understanding-pass/1172_ripple_revise_election_and_wake_cue.md) | proposed | The entity names what a fact changes (`revise`), the ripple is drained, the wake cue says what sleep made of it (runtime draft 0870 over memory 0061) | framework seat |
| [1173](../../proposed/understanding-pass/1173_extraction_capability_gets_its_consumer.md) | proposed | The `extraction` capability gets its consumer (memory 0050/0051) | memory owner + framework seat |
| [1179](../1179_release_wave_understanding_pass.md) | planned, paused | Release wave: memory → runtime (voice in parallel) → gateway → apps → root | framework seat (release sequence) |
| [1181](../../completed/1181_one_time_understanding_backfill_on_theforge.md) | completed 2026-11-08 | One-time backfill of 2,176 texts in four homes on theforge (drafted as "1137", filed under a free id) | Entity owner |

Related, outside this folder: sleep/dream redesign [1150](../../proposed/1150_sleep_and_dream_phases_on_request_or_accumulation.md)
and the generation gate as a design item [1152](../../proposed/1152_inference_resource_orchestration.md) (both carry a
2026-11-08 note on how they meet this track); durable entity activity [1145](../../completed/1145_entity_activity_is_durable_in_the_runtime.md).

## What already landed (all local on main, nothing published; facts as of 2026-11-08 15:00 Paris)

- abstractmemory: 0059 versions in place `3fbaf10`, 0060 task queue `5997b68`, 0061 ripple v1 `09686e0`; stored text
  never cut `8ac6df4`, `566f174`; read-time provenance `e74c29c`.
- abstractruntime: cognition profile `1468f965` + `376cd6e` (lookback.context); restored look-back `e53ee30`; live at
  `da03304`.
- abstractgateway: cognition-profile route `c7c9bc70`, `56aa6219`, `3b42be73`; serve stored understanding (draft 1012)
  `1b3832b7`, `fa75c70a`, `79f47c5b`; live at `2a68b105`.
- abstractentity: Settings → Mind `4f5a975`, `60770af`.
- The live gateway was restarted at 13:30 on runtime `da03304` / gateway `2a68b105` / memory `e74c29c` / voice
  `14a628c`.

## Reading order

1146 (why) → DESIGN.md → 1171 (the drain, its contract and the eleven corrections) → 1172 → 1173 → 1179.

## Governing ADRs

Root [ADR 0026](../../../adr/0026-truncation-policy-and-contract.md) and
[ADR 0054](../../../adr/0054-stored-text-is-never-truncated.md) (stored text is never cut; oversize work is skipped
with its count, never truncated); [ADR 0050](../../../adr/0050-ci-passes-locally-before-any-push.md) (local CI before
push); abstractmemory ADR 0001 (altered memories ripple), ADR 0002 (memory owns the graph and the queue) and ADR 0003
decision 6a (a record's understanding is the one mutable cell, amended 2026-11-08 with 0059).

## Scope

The reader side of the memory-task queue, the ripple's runtime half, the extraction consumer and their release.

## Non-goals

- The host-wide generation gate (runtime draft 0868): a design item under 1152, not built here.
- Retiring the night voice's 20 h throttle: 1150 (operator 2026-11-08: not now).
- Any app screen beyond what each item names (the Entity owner's drafts 0001/0002 own the app).

## Notes for future agents

- The drafts' ids (runtime 0867–0870, gateway 1012/1013, root 1137) were "re-check on landing" ids. Runtime 0867–0870
  and gateway 1013 were never filed in their repos; gateway 1012 and root 1137 are other items. Use the root ids above.
- Root ids are global across the framework this week: 1166 is the gateway's session-kinds item, 1167/1168 are root,
  1169/1170 were reserved and filed by the framework seat; this track starts at 1171.
- Resume only on an explicit go per item; the operator checks every fix personally before any release.

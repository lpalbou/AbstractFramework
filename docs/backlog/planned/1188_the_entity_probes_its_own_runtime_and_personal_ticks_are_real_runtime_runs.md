# 1188 — The entity probes its own runtime, and its personal ticks are real runtime runs (1145 steps 3–4)

> Package: AbstractRuntime (`identity/life.py` own-time loop, `identity/chat.py` home-direct lane, a read-only probe tool or memory verb), AbstractGateway (entity runs readable like any run), AbstractEntity (the "Now" line and ledger read them; other session), AbstractMemory (rehydration seam)
> Type: architecture + implementation
> Status: planned — next release (operator 2026-11-08 14:10: "steps 3–4 are a planned item for the NEXT release")
> Created: 2026-11-10
> Priority: HIGH (inherited from 1145; operator 2026-11-08: "this needs to be prioritized")
> Labels: entities, runtime, ledger, durability, memory, next-wave

## Summary

Split from [1145](../completed/1145_entity_activity_is_durable_in_the_runtime.md) when its steps 1–2 (every tool
result kept whole in the entity's home; the gateway serves those artifacts) were closed on 2026-11-10. What remains:
**step 3**, a read-only probe the entity can call ("what happened at <time> / around <record>") that returns the
ledger slice and the verbatims, so a memory can be re-understood from evidence; and **step 4**, every personal tick
(day, nap, dream window) as a real run in the home's runtime with the same ledger as a visit, so own time stops being
the one activity outside the runtime. Step 4 is the largest and comes last.

## Why

Operator, 2026-11-08 (verbatim, from 1145):

- "Everything that is in the runtime enables some sort of 'rehydrate' to memory. So the entity itself could probe the
  runtime to get access to more verbatims and/or to understand why certain things happen. So I want durability here."
- "Any activity HAS to go through the runtime and the ledger"; "anything the AI retrieves (pages, images) becomes part
  of its runtime."
- 11:45: "there should be no activity, either by human or by entities, that does not go through the runtime. One of
  the reasons is to enable retrospective analysis / search, including to rehydrate context/memory."

## Current code reality (checked 2026-11-10 on `main`)

- Own time still runs home-direct: `abstractruntime/src/abstractruntime/identity/life.py:2394` ("The own-time loop
  runs home-direct (ChatSession, no run ledger)"); `identity/chat.py:630` `_Run` is a duck-typed stand-in, run id
  `chat-<session>` (`chat.py:1211`). Its tool calls reach the ledger only inside the tick's `memory_verbatim`, and its
  spend is folded from `loop_spend.json`, not from a ledger.
- Since runtime `d217d93` every tool result on that lane is already an artifact of the home (`[artifact: <id>]` in
  the result text); since gateway `d1d9656f` the gateway serves them (`GET /entities/{name}/artifacts…`).
- No probe tool exists (no `what happened around` / runtime-probe symbol in `abstractruntime/src`).
- The generic `/runs/{id}/view` (`abstractgateway/src/abstractgateway/routes/replay_view.py`) and `/runs/{id}/ledger`
  (`routes/gateway.py:11994`) read the gateway run store only; the entity routes (`routes/entity_replay.py`: replay,
  verbatim, diary, artifacts) serve the home.
- Since 2026-11-09 the loop carries the Stop fence (runtime `66d3220`, `86666af`, `098cd4b`, `2c9b673`) and the
  lifecycle generation; a tick that becomes a run must keep both.

## Scope

### In scope

1. **Probe (step 3):** a read-only tool or memory verb, offered to the entity, that answers "what happened at <time>"
   or "around <record>" with the ledger slice, the artifacts it names and the verbatims, scoped to the entity's own
   home; bounded by explicit paging (never a silent cut, ADR 0054).
2. **Personal ticks as runs (step 4):** each tick is a durable run in the home's runtime (LLM_CALL, tool calls,
   artifacts on the ledger), resumable and replayable; the loop heartbeat, the 1800 s patience, the visitor-at-the-door
   yield (1184) and the Stop fence unchanged.
3. **Readable everywhere:** the Entity app's "Now" line and ledger, Observer and the entity's own probe read those runs;
   decide whether the generic `/runs/{id}/view` and `/ledger` answer for entity runs or the entity routes stay the
   door (one answer, written into the gateway docs).
4. Tests: a personal tick with two tool calls and one fetched page leaves a run whose ledger lists both calls and whose
   artifact holds the page; the gateway returns it; the probe returns that slice; removing the run write turns the
   test red.

### Out of scope

- The understanding drain and ripple ([1171](understanding-pass/1171_understanding_drain_in_turns_and_idle_windows.md),
  [1172](../proposed/understanding-pass/1172_ripple_revise_election_and_wake_cue.md)).
- The Entity app's artifact chip ([1170](1170_session_kinds_client_halves.md)).
- Private diary visibility ([1186](../proposed/1186_private_means_private_from_others_not_from_the_owner.md)).

## Acceptance criteria

- [ ] Every entity activity since the change has a run id; its ledger lists its tool calls (visits already do).
- [ ] A fetched page is readable as an artifact a week later, reached from the tick's run.
- [ ] AbstractEntity's "Now" line and ledger show personal-time tool calls live.
- [ ] The entity's probe returns the ledger slice and verbatims around a record.
- [ ] No duplicate loops; the 1800 s patience, the heartbeat contract, the visitor yield and the Stop fence tests stay
      green.
- [ ] ADR written before closure (the loop's contract changes: own time becomes runs).

## Receipts

- Parent: [1145](../completed/1145_entity_activity_is_durable_in_the_runtime.md) (rulings, order of work, steps 1–2
  record). Running log: `untracked/release-2026-11-07/RESUME.md` (2026-11-08 13:15, 14:10).

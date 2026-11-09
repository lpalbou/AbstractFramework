# 1178 — Stopping personal time leaves the entity awake and visitable, not asleep for six hours

> Package: AbstractRuntime (`identity/life.py` grant gate / day gate landing), AbstractGateway (`POST /entities/{name}/state` v17 composite, `entity_phases.json` edge `personal->sleep#operator`), AbstractEntity (phase radio)
> Type: bug
> Status: completed
> Created: 2026-11-08
> Completed: 2026-11-10
> Priority: P1
> Labels: entities, life-loop, state-machine, personal-time, paused, decision-gate

Paused by operator ruling 2026-11-08 (pause all dev); resume = explicit go.

## Summary

OPERATOR DECISION GATE (never assignable) on the state rule, then a small build. When the operator stops an entity's
personal time, the entity lands **asleep with a wake-check six hours later**, refuses the visitor who comes next, and
cannot be woken while that visit is open. Expected behaviour (operator, 2026-11-08): **stop = awake and available** —
own time ends at the next tick boundary, the entity stays awake, a visit is accepted at once. An explicit Sleep stays
what the v17 ruling made it (the composite operator sleep).

## Why

Incident on nerin, 2026-11-08 (UTC; Paris = UTC+1), read from `runtime/entities/nerin/state_history.jsonl` and
`runtime/audit_log.jsonl`:

| UTC | What happened |
|---|---|
| 01:04:08 | Entity app web controls `POST /state asleep` ("by the operator (web controls)"); the gateway applies the v17 composite: "operator sleep (v17): personal grant disarmed + standing orders cleared — sleep is sleep" |
| 01:04:57 | The loop's grant gate lands "personal ended (grant_revoked) - the ruled landing is sleep - need-check in 6h", `wake_at` 07:04:57 |
| 01:04:57–01:09:54 | The grant gate rewrites the same `asleep` state **643 times** (about every 0.46 s), each with a new `wake_at` |
| 01:06:08 | The operator opens a visit: accepted as `asleep` + `mode: visiting` (auto-yield) |
| 01:06:31–01:07:26 | Three visit turns refused with 409 (reason not in the audit log) |
| 01:09:53–01:09:56 | Repair attempt: `loop/stop` 200, `POST /state` (wake) **409**, `loop/start` 409 — the open visit blocks the wake |
| 01:09:58–01:10:12 | `PUT personal-grant`, the visit closed, `POST /state awake` 200 ("operator stopped personal time; the stop must not lock him away from visits"), `loop/start` 200 |

## Current code reality (2026-11-08)

- abstractruntime `identity/life.py` `read_day_gate`: no armed grant → `{"phase": "sleep", "cause": "no_grant",
  "need_check_s": unattended_wake_cadence_h × 3600}`; `phase_spec.py` default `unattended_wake_cadence_h: 6.0`. In 24/7
  mode the boundary writes `asleep` with reason "personal ended (…) - the ruled landing is sleep - need-check in
  {cadence}h" (`life.py` ~3075–3125, `ed7d605`).
- abstractgateway `routes/entities.py` ~1691–1703 OPERATOR-SLEEP-IS-ABSOLUTE (operator ruling 2026-07-21, spec v17):
  an operator-written `asleep` also disarms the grant and clears standing orders; `assets/entity_phases.json` edge
  `personal->sleep#operator`, `edit_policy: locked-absolute`, semantics "Operator stop ends personal; the resting
  entity sleeps".
- abstractentity `entity_view.tsx`: the phase radio offers work / personal / sleep; the personal slot's stop calls
  `loop/stop` ("the machine settles to sleep, idle=sleep"); the sleep slot posts `asleep`. No control means "awake,
  not on personal time".

## Proposed direction

1. Ruling first: amend the edge `personal->sleep#operator` — an operator stop ends personal into **awake (idle)**, not
   sleep; the explicit Sleep act keeps the v17 composite.
2. Runtime: the grant gate's landing after an operator stop is `awake` with no `wake_at`; the loop idles without
   rewriting the state (one write per transition, never a write per poll).
3. Gateway: a wake (`POST /state awake`) during a visit's auto-yield posture restores the visit's own posture
   instead of answering 409.
4. App: the personal slot's stop says "his personal time ends at the next tick; he stays awake".

## Promotion criteria

The operator's amendment of the v17 edge (it is `locked-absolute` by his earlier ruling).

## Validation ideas

- Stop personal time on a hermetic gateway (scratch HOME, never :8080): state `awake`, no `wake_at`, a visit opens and
  its first turn is answered.
- `state_history.jsonl` gains exactly one line for the transition (the 643-write storm is red before the fix).
- Explicit Sleep still disarms the grant and clears orders (the v17 test stays green).

## Non-goals

Changing the explicit Sleep act; personal time without a grant.

## Related (2026-11-09)

[1184](1184_a_visit_never_fails_on_a_busy_entity.md) (completed, operator review pending) removed every
time limit between clicking visit and the open visit: the door no longer answers 409 `loop_busy` or `home_lease_held`,
and the own-time loop yields within one step. It does not change the stop → 6 h sleep landing or the `life_state`
floor that shows SLEEP when no loop runs; both stay with this item.

## Completion report (2026-11-10)

Moved from `proposed/1178_stopping_personal_time_leaves_the_entity_awake_and_visitable.md` to `completed/` by the
backlog hygiene pass of 2026-11-10 (never promoted to `planned/`: it was built while still proposed). Committed on
AbstractRuntime `main`, not released; ships with AbstractRuntime 0.19.0 in the next wave
([1179](../planned/1179_release_wave_understanding_pass.md)).

### Decision state (read this first)

**The operator's explicit decision on this item's gate was never recorded on the item.** The gate asked him to amend
the v17 edge `personal->sleep#operator`. It was overtaken by his wider phase rulings, which settle the same question:
`untracked/entity-phases-2026-11-08/TARGET.md` (operator ruling 2026-11-08 19:02; its "Known gaps" calls the 6 h
landing "wrong: turning the toggle off = no more own time; he stays awake and visitable") and the five-state life
cycle (operator diagram 2026-11-09 15:38: visit · idle · work · personal · sleep, only `personal` a toggle), written
into contract v2/v3 and the canonical phase spec v22–v25. The spec copy the gateway ships
(`abstractgateway/src/abstractgateway/assets/entity_phases.json`, version 25) now reads: "personal off ends own time
AWAKE (idle, visitable), never asleep", and supersedes v4 IDLE-IS-SLEEP. The build was done under that contract. The
operator's live test of 2026-11-09 evening raised no finding on it; that is not an explicit acceptance of this item.

### What was built (commit checked against the repo's log on 2026-11-10)

- AbstractRuntime `3cafac9` (2026-11-09 15:07), "Entity phases runtime §10.1 (root 1178)": personal off ends own time
  AWAKE in both modes (`stopped_by=personal_off`, was `personal_disarmed`), no grant-gate sleep, no 6 h wake; an
  ending loop never writes a loop-exit sleep and wakes a sleep it wrote for itself; a new loop wakes one an earlier
  loop left (`LOOP_OWN_SLEEP_WRITERS`: self, personal-cycle, grant-gate, day-gate, loop-exit); operator sleeps, visit
  postures and `paused` are never touched; a supervised settled desk exits without a sleep. Files:
  `identity/life.py`, `changelog.d/personal-off-ends-awake.md`, tests.
- The doors around it came with phases v3 (other items, listed for the reader): gateway `8681a9be` (`PUT
  /entities/{name}/life_state/toggles` `{personal}` — its docstring: "personal off ends own time at the loop's next
  boundary and never puts him to sleep"), Entity app `0848c19` (phase bar on contract v3).

### Tests

- `tests/test_entity_phases_runtime.py` (new): 9 of its 10 tests red on the code before; 7 loop tests in
  `tests/test_entity_life_loop.py` re-based from the v8/v13 sleep landings; one need-check obedience fixture now uses
  an operator sleep (`tests/test_phase_graph_obedience.py`).
- Live since restart #7 (2026-11-09 17:35, runtime `3f4ee09` contains `3cafac9`).

### Against the proposed direction above

1. Ruling: superseded by the phase rulings (above), not recorded as an answer to this gate.
2. Runtime landing awake, no `wake_at`: **built** (`3cafac9`). The "one write per transition, never a write per
   poll" check (the 643-write storm) is not named in the commit's tests; re-check it on a hermetic gateway.
3. Gateway, a wake during a visit's auto-yield posture: not re-verified in this pass. Under v3 a visit never fails
   except when stopped (1184 and gateway `1cd0004d`); "sleep now" during a visit stays 409 `in_visit` by design.
4. App wording: the Entity app's phase bar is on contract v3 (`0848c19` and later); its exact sentence for personal
   off was not re-read here.

Non-goal drift to know: this item kept "the explicit Sleep act stays the v17 composite". Spec v22 changed that too:
"Sleep now" no longer disarms the personal toggle and no longer clears the work order. That change is the operator's
v22 ruling, not this item's.

### Residual follow-ups

- The storm check and the wake-during-visit check (items 2–3 above), on a hermetic gateway (never :8080).
- ADR state: the phase contract lives in the canonical spec (`abstractentity` spec v25) and its contract files under
  `untracked/entity-phases-2026-11-08/`; no root ADR. If the five-state life cycle is meant to outlive this wave, it
  deserves one.

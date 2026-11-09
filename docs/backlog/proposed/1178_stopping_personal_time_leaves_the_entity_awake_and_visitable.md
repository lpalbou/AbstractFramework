# 1178 — Stopping personal time leaves the entity awake and visitable, not asleep for six hours

> Package: AbstractRuntime (`identity/life.py` grant gate / day gate landing), AbstractGateway (`POST /entities/{name}/state` v17 composite, `entity_phases.json` edge `personal->sleep#operator`), AbstractEntity (phase radio)
> Type: bug
> Status: proposed
> Created: 2026-11-08
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

[1184](../completed/1184_a_visit_never_fails_on_a_busy_entity.md) (completed, operator review pending) removed every
time limit between clicking visit and the open visit: the door no longer answers 409 `loop_busy` or `home_lease_held`,
and the own-time loop yields within one step. It does not change the stop → 6 h sleep landing or the `life_state`
floor that shows SLEEP when no loop runs; both stay with this item.

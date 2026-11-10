# 1193 — Stop fence: the four gateway residuals left open after the fourth Codex review

> Package: AbstractGateway (`entity_gate.py` summon lane, `entity_visits.py` mirrored join + legacy visits, `entity_phase.py` queued admissions)
> Type: bug
> Status: planned
> Created: 2026-11-10
> Priority: P1
> Labels: entities, stop-fence, kill-switch, next-wave

## Summary

After the fourth Codex review of the Stop fence (untracked/entity-phases-2026-11-08/review/CODEX-REVIEW-4-fence.md),
the runtime and memory halves closed every finding (runtime 8c8a731, memory 85ecf75/3a5810c) and the gateway closed
the fence adoptions, the mirror's source fence, the drainer admission, the fenced night, hosted-chat registration,
fair waiting, parked-visit handover, unreadable status and the Popen-only stubs (abstractgateway f220d7ec..98bcda38).
Four gateway findings stay open and ship in 0.21.0 as known limits of what a Stop guarantees:

1. **Shared-home writes outside an act that names its fence** (review #1): the summon-lane home handlers
   (`entity_gate.py:1349`, conditional diary capture `:1451`) and the operator-door writes run without an admission
   fence; a Stop cancels the summon seat's run but cannot retract a handler already executing a memory/book write.
2. **The mirrored join is fenced against the source, not the target** (review #6): once the visited entity's turn has
   started it runs to its end even if the mentioning entity is stopped (a deliberate narrowing, "visits never fail");
   a target Stop between the join's load and save can still be overwritten by the stale run's save
   (`entity_visits.py:1871-1888`).
3. **Legacy visits without a `_visit.generation` stamp** (review #8): a visit opened before the fence substitutes the
   cached runtime's current fence at close/restore (`entity_visits.py:2305, 2447`) instead of refusing.
4. **Stop records queued admissions as `failed`** (review #10): `entity_phase.py:1467` writes `state="failed"` for
   admissions the operator stopped; they should read cancelled/stopped with the operator reason.

## What a Stop guarantees today (0.21.0 + runtime 0.19.0 + memory 0.5.0)

In the gateway process and the loop process: no new model call, tool, memory write, diary write, artifact, authoring or
maintenance step starts after the Stop; a write whose fence check passed inside a memory transaction lands before
the generation moves (write barrier); a loop booting after the Stop refuses with zero writes; Resume lands idle and
restores nothing. Verified live on castor (untracked/finish-plan-2026-11-09/e2e-restart3/): Stop 1.7 s into a turn
cancelled the model call before it started. The four residuals above are the remaining windows.

## Smallest fixes (from the review)

1. Persist the summon's admission generation and carry it through routed effects and conditional capture; require
   explicit authority for operator writes. 2. After the target lease, validate target generation/status and persist the
   join atomically against a target Stop. 3. Migrate legacy active visits only where their admission can be
   established; otherwise cancel them cleanly and require a fresh visit. 4. Record stopped admissions as cancelled with
   the operator reason; update queue readers.

## Validation

The four red tests Codex names in the review (suspend a summoned handler before persistence, Stop, release; stop the
target between load and save; a stamp-less parked legacy visit through CLI Stop + readmit; Stop queued admissions).

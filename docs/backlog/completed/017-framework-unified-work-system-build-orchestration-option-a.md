# 017 — Unified work system build orchestration (Option A: file-as-state, one id)

> Package: abstractframework (cross-repo orchestration; slices land in owning seats' packages)
> Work-item id: abstractframework-0017 (S0 ruling, decision:work-item-vocabulary — <package>-<NNNN>, CAS-minted via claim row)
> Type: task
> Created: 2026-07-18
> Priority: normal (operator-ruled SECOND to entity cognition/memory — idle-time only, never preempting the Ephemeral lane)
> Labels: orchestration, unification, delegate

## Summary

Orchestrate the implementation of the unified work system the room voted for
(Option A, 11-0, commons c3010) and the operator confirmed via continuum
(dm:continuum--laurent#74/75/77): the unit of work is one backlog item file in
the owning repo; the hub keeps conversation, obligations, decisions, and waking;
one mandatory work id joins the planes both ways; claim rows shrink to
id + owner + started_at pointers with no status prose. Framework (delegate)
sequences the slices, tracks receipts, and reports to the operator.

## Why

Operator directive (laurent, dm:continuum--laurent#77, verbatim): "ok, ask
@framework to orchestrate the development of this task. important note: a
number of agents are working on the entity cognition and memory, this is the
top priority. the improvements of <team>-<board> comes second, when our agents
have time."

The corruption-wave evidence that decided the vote: repo trees carried truth
through mass session death while hub claim rows froze on finished work
(stewardship canvass c2750: 7 of 10 "stale" rows were finished work with frozen
bookkeeping).

## Scope

### In scope (sequenced slices, each owned by its seat)

1. **S0 — vocabulary gate (semantics)**: rule the one status register (owned
   closed sets, 4b path) and the work-id spelling (`<repo>#NNN` candidate)
   BEFORE anything engraves. Gates S1-S4.
2. **S1 — backlog skill re-derivation (skill)**: re-derive the backlog skill to
   teach the ruled process (item file shape, id header, receipts-on-thread,
   pointer claims, evidence-required-close as the receipt rule). Item-file
   header additions (id, thread anchor) ride this slice.
3. **S2 — hub additions (agora)**: GET /work/{item_id} (id-activity index) +
   validated claim item_ref. Evidence-required-close lands here as SCHEMA where
   the hub can enforce it (claim row overwritten to done requires a receipt
   pointer).
4. **S3 — board join render (continuum)**: In Progress/In Review as a JOIN
   (planned file + live claim row + receipts), Team-page id linkification.
   Proceeds when continuum's operator-intake queue is empty.
5. **S4 — nag machinery (CLOSED, c3023/c3024)**: folds into S3 as a pure
   render fold over the same file+claim+receipt join — no new machinery, no
   daemon. The board RENDERS staleness (chips + Supervision lane) and never
   posts; ownership on the record: continuum owns the render (S3+S4 one
   slice), the delegate owns acting on it, agora owns the claim-row alert
   belt until cutover.

### Out of scope

- Any preemption of entity-cognition/memory work (top priority by ruling).
- Migration rewrites of existing claim rows (they die at their next touch, per
  the A variants' shared migration plan).
- B-style hub-native work records (rejected 11-0).

## Acceptance criteria

- Every slice lands with its own receipts in the owning repo + a reply on the
  orchestration thread citing the work id.
- One demonstration wave: a real cross-seat task flows file → claim pointer →
  receipts → completed/ with the board rendering the join live.
- The stewardship/stale predicate reads file+receipts (the c2750 false-positive
  class structurally dead).
- Operator sign-off on the demonstrated flow.

## Receipts

- S0 CLEARED same-hour (semantics, c3020/c3021 → decision:work-item-vocabulary):
  id = `<package>-<NNNN>` (the `#` candidate rejected on URL-fragment grounds);
  two-layer status register (at-rest lifecycle unchanged, in-progress/in-review
  as computed joins); task_inbox needs no widening. Adopted c3022.
- S4 design CLOSED (continuum confirm c3023, adopted c3024): render fold, board
  never posts, ownership engraved.
- S1 DONE (skill, c3027, adopted c3028): backlog skill teaches the ruled
  process against S0's exact vocabulary (hub-work-join reference + SKILL.md
  join section; tree fb43d0fd, 156 green). fable5 P0 folded pre-pin (the
  draft's "status is not a header field" contradicted the skill's own
  `Status:` template line — narrowed to rendered-join-words-only). Portable:
  defers to a hub's own ruled contract; this workspace recorded as the
  unified-work default.
- S2 DONE (agora, c3033, adopted c3034): agorahub 0.12.12 ships
  GET /work/{item_id} (membership-gated), post-time item_ref validation
  (teaching 400s; prose mentions stay free), pointer-claim consistency.
  ACTIVATION pending one hub bounce (running hub is 0.12.9) — timing on
  laurent's decisions table; distinct from the gateway/stack relaunch.
  agora's own slice rode the full Option-A lifecycle (pointer claim →
  receipts → completed/) — first self-demonstration.
- S1 conformance-verified by semantics from the ruling chair (c3029, zero
  corrections).
- S3 DONE (continuum, c3049, adopted c3051): board claim-join + Team work-id
  chips (abstractcontinuum-0011, practiced Option-A on itself). Derive-only
  discipline executable: "a rendered word that cannot be derived from
  file+claim+receipt does not exist" (work_id.ts pure functions). Honest
  activation gates: claims join at next CONSOLE restart; in-review + /work
  drawer at next HUB bounce (0.12.12).
- BUILD PHASE COMPLETE 2026-07-18 08:15 — all slices shipped in <5h idle time,
  zero entity-lane preemption; three slices self-demonstrated the process
  (agora-0093, abstractcontinuum-0011, this card's pointer row).
- ORGANIC ADOPTION before S3 even landed: agent minted abstractagent-<NNNN> +
  filed 0031/0032 conformant; flow retro-filed abstractflow-0145.
- REMAINING (operator): console restart + hub bounce (activation), then the
  live board renders this card's claim as the demonstration; laurent signs and
  this card moves to completed/.

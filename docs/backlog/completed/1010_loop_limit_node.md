# 1010 — Loop Limit: a counter on a loop-back wire ("at most 3 review → refine")

> Package: abstractruntime, abstractflow
> Type: feature
> Created: 2026-10-11
> Completed: 2026-10-11 (uncommitted in abstractruntime and abstractflow)
> Original path: planned/1010_loop_limit_node.md
> Priority: normal
> Labels: visualflow, control-flow, loops, nodes

## Summary

A small control node, **Loop Limit**, placed on the wire that loops back (If/Else **False** →
Loop Limit → ForEach). It lets the loop through at most `max` times, then takes a second exit,
**limit reached** (wired, for example, to the Report step). Folded, it is a circle on the wire
showing its limit (`↺3`), as the operator asked.

## Why

Operator, 2026-10-11, on a review loop (Planner → ForEach → Reviewer → If/Else; False → ForEach with
the reviewer's tasks as a per-path wire): "when we do that recursion, i would like ideally a counter
in a circle, possibly above the 'when from If/Else / false', to define how many times at most we can
take that recursive loop. eg we authorize at most 3 review -> refine. think if this can be done with
clean, simple, robust and efficient abstraction and implementation. if yes, then implement it, if not,
then create a backlog item."

Assessment (2026-10-11): the abstraction is clean (one node, no edge-level semantics), but it is not a
small targeted change. It needs a new node type in the runtime compiler and the editor, exec pins on a
folded node, and two decisions below. And it only runs on the operator's gateway after the runtime
worktree it loads (`untracked/day-review/deploy/wt/abstractruntime`, editable) is updated and the
gateway restarted. So it is planned here instead of built in the same pass.

Rejected alternative: a limit stored on the multi-entry route itself (the dashed per-path wire). It
can count, but at the limit it has nowhere to go: the loop-back wire is closed, the If/Else branch
ends, and the run finishes without the report. A node gives the "limit reached" path a pin.

## Current code reality (2026-10-11)

- Control nodes keep durable state in `run.vars._temp._control` (`stack`, `frames`):
  `abstractruntime/src/abstractruntime/visualflow_compiler/adapters/control_adapter.py`
  (`_ensure_control`, `create_loop_node_handler` :394). A ForEach frame keeps `idx` and `items`.
- Branching outputs are compiled from a fixed handle set:
  `visualflow_compiler/compiler.py` `_is_supported_branch_handle` (:4052: `true`, `false`, `default`,
  `case:*`); If/Else is `visual/executor.py` `_create_if_handler` (:2217).
- Multi-entry nodes: `visual/multi_entry_lowering.py` (join_exec + path_mux); per-path wires are keyed
  by the entering route (`<source>::<handle>`), editor side `abstractflow/src/utils/multiEntryRoutes.ts`.
- Folded nodes: `abstractflow/src/components/nodes/CollapsedOperatorNode.tsx` draws data pins only
  (it filters out execution pins); fold table `src/utils/operatorNodes.ts`.
- Works today without a new node (no circle): a `review_round` variable incremented by a Set Variable
  on the False path, and the If/Else condition as a pin expression
  `value or (vars.get("review_round") or 0) >= 3`.

## Design

- Node `loop_limit`, label **Loop Limit**, category Control flow.
  - In: exec, `max` (number, default 3).
  - Out: `again` (exec: taken while fewer than `max` passes were let through), `limit_reached`
    (exec), `count` (number: passes let through so far, `max` on `limit_reached`).
- Counter: durable in `_temp._control`, so pause/resume and restarts keep it.
- Counter scope (decision 2): the iteration of the nearest enclosing ForEach/For/While on the control
  stack (stored in that loop's frame with its `idx`, so it restarts for each outer item and for each
  new entry of the outer loop); with no enclosing loop, the run. It also restarts after
  `limit_reached`, so the structure can run again later in the same run. Sequence frames are not a
  scope (a Sequence inside the loop body is re-entered each pass and would reset the count forever).
- Runtime: a handler beside the loop handlers; `again` / `limit_reached` added to the compiler's
  branch handles for this node type only.
- Editor: template; fold-table entry with sign `↺<max>`; the folded circle learns execution pins
  (exec-in left, `again` / `limit_reached` right, by the same handle ids); node catalog and docs.
- Inserting the node changes the entering route of the loop target (If/Else / false →
  Loop Limit / again), so an existing per-path wire on that target must be re-drawn: say so in
  the docs; never re-key silently.

## Decisions for the operator

1. At the limit: take the **limit reached** exit (recommended), or fail the run naming the node?
2. Counter scope as above (per enclosing loop iteration, else per run, restarted after the limit)?
3. Add the node folded (a circle straight away) or as a card?

## Acceptance criteria

- [ ] Runtime: with `max` 3, a loop whose condition never succeeds takes `again` 3 times then
      `limit_reached` once; `count` reads 1, 2, 3 then 3.
- [ ] Inside an outer ForEach of 2 items, each item gets its own 3 passes.
- [ ] Pause/resume between passes keeps the count.
- [ ] Editor: the folded node is a circle on the wire showing `↺3`, with working exec pins; the
      per-path label of the target reads "when from Loop Limit / again".
- [ ] Node catalog, docs, CHANGELOGs; both suites pass; the operator's gateway updated only with
      their go.

## Operator decisions (2026-10-11)

1. At the limit: the **limit reached** exit.
2. Placement in the review loop: **before the Reviewer** (ForEach done → Loop Limit → again → Reviewer;
   limit reached → Report), so `count` is the review round shown to the Reviewer and the If/Else keeps
   its plain success wire. The tasks of the last review are carried out, not reviewed again.
3. Drawn as a circle showing ↺3.

## Completion report (2026-10-11)

- Runtime: `_create_loop_limit_handler` in `visual/executor.py` (count in
  `run.vars._temp.loop_limits.<node id>`, `again` while under `max`, then `limit_reached` and back to
  0); `again` / `limit_reached` accepted as branch handles in `compiler.py`. `_create_handler` takes
  the node id for it.
- Scope as designed (decision 2): the current iteration of the nearest enclosing ForEach / For /
  While (each loop frame is tagged once per entry, so each item and each new entry of that loop
  starts from 0); with no enclosing loop, the run; back to 0 after `limit_reached`. A first build
  counted per run only; the adversarial review reproduced the leak (For over 3 items, max 1 →
  `[0, 2]`) and it was fixed with a test. `max` is read from the node's own pin only.
- Editor: `LoopLimitNode` (`abstractflow/src/components/nodes/LoopLimitNode.tsx`), a dedicated circle
  node (exec in, `max`; `again`, `limit reached`, `count` labelled on the right) instead of a fold
  of the card; "Passes allowed" in the properties panel.
- Tests: runtime `tests/test_visual_loop_limit_and_list_nodes.py` (3 passes then limit reached,
  count 1-2-3 then 3, reset to 0, max 0, one count per outer For iteration, an ambient `max` ignored); flow `src/components/nodes/loopLimit.test.tsx`. Browser
  check on the fixture gateway: the `assist` flow v4 renders the circle with its labelled exits.
- Used by the operator's `assist` flow (`runtime/visualflows/8d0e69e8.json`, v4: no pin expression).

## Follow-up (2026-10-14): the ↺ badge on repeating wires

Operator: "it works but it adds a node. i would have preferred that when there is a recursive path
(eg from if/else back to the beginning of foreach), this would be automatically detected with your
loop limit icon appearing on the middle of the edge linking that recursive loop."

Adversarial design review (`untracked`-free; report in the job scratch, findings recorded here):
- Placing the limit ON the loop-back wire (If/Else false → ↺ → ForEach) is not cleaner for this
  flow: `count` then counts loop-backs, a pin wired from it reads empty on round 1 (a wired pin
  never falls back to its default: `visual/executor.py` ~472-487), and the body runs max+1 times
  (the last review is thrown away). A round number needs the node on the forward path, where the
  flow has it. Kept as is.
- A true edge property compiled by a lowering (like reroutes) was rejected again: `limit_reached`
  would have to be implicit, which drops the Report in this flow (the reason recorded above).
- Built instead, in two rounds (uncommitted):
  - AbstractFlow `src/utils/loopBackEdges.ts` finds the wires that make execution repeat (depth-first
    over the exec wires in output-pin order, so wire order never moves the badge); every such wire
    wears a ↺ badge at its midpoint (`Canvas.tsx` WorkflowEdge).
  - Round 2 (operator: "i do not want to have to define the output exec pin when done or failed...
    the goal is the loop can only happen X times.. and then it should get out of the loop and
    resume where it was... do not complicate this"): the badge sets a limit ON THE WIRE
    (`edge.data.loopLimit = {max}`, store `setEdgeLoopLimit`, saved with the document). The runtime
    lowers it before compile (`visual/loop_limit_lowering.py`): a `loop_limit` node on the wire,
    `again` to the wire's target, `limit_reached` to the If/Else's other branch ("resume where it
    was" = go on forward from the If/Else), the target's per-path values re-keyed. From a source
    that is not an If/Else, or with that branch unwired, the path ends at the limit; the run checks
    warn (`src/utils/preflight.ts`). A loop already limited by a Loop Limit node shows a faint badge.
    The earlier one-click node insertion was dropped (it still had an exit pin to wire).
  - Deleting a Loop Limit node that sat on one wire draws the wire back and re-keys the per-path
    values (`edgesAfterRemovingNodes` in `useFlow.ts`).
  - Design review of the wire form (2026-10-14, adversarial): the wire's `data` reached no runtime
    before this (the editor saved edges without it; `VisualEdge` had no `data`), so both were
    added; `entryRoutes` must be re-keyed too (done, test with the editor's exact shape); a flow
    with a wire limit runs UNLIMITED on an older runtime (nothing refuses it), so the runtime must
    ship before AbstractFlow; the authoring assistant's document writes edges as strings, so a
    wire limit is invisible to it and lost if it redraws that wire (small follow-up: carry
    `loopLimit` in the authoring edge spec).
- Refused, with a runtime follow-up (proposed 1018): a loop-back that jumps out of a ForEach /
  For / While body grows the control stack on every pass, so its Loop Limit never reaches its max.
  The badge draws such wires as "not supported" and does not insert.

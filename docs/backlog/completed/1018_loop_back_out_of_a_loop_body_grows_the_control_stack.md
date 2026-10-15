# 1018 — A loop-back wire that leaves a loop body grows the control stack

> Package: abstractruntime
> Type: bug
> Created: 2026-10-14
> Completed: 2026-10-15
> Priority: normal
> Labels: visualflow, control-flow, loops, runtime

## Summary

An execution wire that goes from inside a ForEach / For / While body back to a node outside the
body (e.g. an inner loop's If/Else "false" wired to the outer loop's entry) re-enters the outer
loop without leaving the inner one: the control stack grows by one frame per pass
(`['outer', 'inner', 'outer', 'inner', ...]`), and anything scoped to the stack grows with it. A
Loop Limit on such a wire never reaches its max (its count is scoped per enclosing-loop
iteration), so the run never ends.

## Why

Found by the adversarial design review of the ↺ badge on repeating wires (1010 follow-up,
2026-10-14), probe (b): inner For body → If false → Loop Limit (max 1) → outer For: stack grows,
`count` never passes 1, the run never ends. The editor now draws such a wire's badge as "not
supported" and refuses to insert a limit there, but the wire itself still compiles and runs.

## Current code reality (2026-10-14)

- Loop frames: `abstractruntime/src/abstractruntime/visualflow_compiler/adapters/control_adapter.py`
  `create_loop_node_handler` (~435-449): a loop entered while its own frame is not on top pushes a
  new frame; nothing pops the inner frames a loop-back jumped over.
- Loop Limit count scope: `visual/executor.py` `_create_loop_limit_handler` (`_scope`: the loop
  frames on the stack with their progress).
- Editor detection: `abstractflow/src/utils/loopBackEdges.ts` (`leavesLoopBody`).

## Options

1. On entry of a loop that is already on the stack below the top, unwind the stack to it (pop the
   frames above): the natural reading of "go back to the outer loop".
2. Refuse at compile time a loop-back wire that leaves a loop body, with a clear error naming the
   wire (the editor could then show the same message).

## Promotion criteria

A flow that needs a loop-back out of a body, or an operator ruling on option 1 vs 2.

## Done (2026-10-15, operator ruling: option 2)

The operator chose to refuse the wire at compile time. AbstractRuntime 0.10.0
(`visualflow_compiler/visual/loop_back_check.py`, called from `visual_to_flow` after reroutes are
lowered and before a wire's limit is) walks the execution wires the way the editor finds its ↺
badges and raises on the first loop-back that leaves a loop body: "Wire <source>.<pin> -> <target>
goes back out of <loop>'s loop body: the run would never end. A path inside a loop body can only
repeat within the body; to repeat the whole loop, wire the loop-back after the loop's done." A
loop-back through the loop's `done`, or one that stays inside the body, is unchanged; a limit on
the offending wire does not make it acceptable (tests: `tests/test_visual_loop_back_out_of_body.py`,
5 cases). AbstractFlow 0.9.0's run checks say the same sentence on the wire's source node, as a
blocking issue before Run or Publish (`src/utils/preflight.ts`, `LoopBackWire.leavesLoop`), and the
wire's badge card carries it. Option 1 (unwind the stack to the outer loop on re-entry) stays open
if a flow ever needs a loop-back out of a body; it would need a ruling on what the outer loop's
index means after the jump.

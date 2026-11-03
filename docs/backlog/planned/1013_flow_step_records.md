# 1013 — Flow-step records: the runtime records what control and state nodes did

> Package: abstractruntime, abstractgateway, abstractobserver, abstractcode (web)
> Type: feature
> Created: 2026-10-11
> Priority: normal
> Labels: runtime, ledger, observability, visualflow
> Followed by: 1014 (AbstractFlow run window built from these records)

## Summary

VisualFlow control and state nodes on the execution chain (Sequence, Parallel, ForEach / For /
While, If/Else, Switch, Set Variable / Set Variables / Set Variable Property) run without leaving
any ledger record, so no client can show them. Add one small, opt-in ledger record per executed
control/state node, `abstract.flow_step`, carrying what the node did (branch taken, loop item i/n,
control stack before and after, a summary of a variable written), and keep it out of every
consumer that must not count or show it.

## Why

Operator, 2026-10-11, on a running `assist` flow: "why does it show 'pending' for the first branch
when it was just about setting variables?" and "the level of stack of execution is not really well
shown here... including the for loop that is completely absent?" Then, after a dry run: "create a
backlog item(s) ... explaining they will need adversarial reviews to make sure the abstraction and
implementation are as clean, simple, robust and efficient as possible."

Observed on run `31855b6b` (2026-10-11): the run was healthy (Sequence then:0 had set `history` and
`knowledge`; ForEach on item 1 of 13; Task Executor sub-run working), but the ledger held only
`llm_call`, `answer_user` and `start_subworkflow` records, so the run window showed the Set
Variable branch as "Pending…" and no ForEach.

## Case 2 (2026-10-12): the run spotlight trail skips silent nodes

Operator, 2026-10-12, on a running `assist` flow (v4, run `0cd8a82d`), screenshot with Task
Executor spotlit: "i think the decaying highlight you created didn't work or skip certain nodes,
the foreach is not highlighted for instance".

- The trail (AbstractFlow run spotlight, `abstractflow/src/utils/runSpotlight.ts` `withTrailStep`,
  fed by `setExecutingNodeId` in `src/hooks/useFlow.ts`) is built from `node_start` events, which
  `src/hooks/useWebSocket.ts` (~379) derives from ledger records. The trail code works; it is
  never told about the silent nodes.
- The run's ledger held only `node-3` Planner (`llm_call`), `node-5` Show Message (`answer_user`) and
  `node-8` Task Executor (`start_subworkflow` / `llm_call`), repeated per item: 27 records, none for
  ForEach, Start the run (Set Variables), Add to history / Add to knowledge (Add to List
  Variable), Loop Limit or the String Templates. So with Task Executor spotlit, the trail read
  Show Message → Planner, and ForEach never lit.
- Rejected UI-side fix: inferring the skipped steps from the exec wires between two recorded
  nodes. It cannot know which way an If/Else or Loop Limit went, and the return from a loop body
  to its ForEach has no wire at all, so the trail would sometimes be wrong.
- With flow-step records, the trail (and the run window, 1014) shows every executed node exactly:
  ForEach item i/n, the branch an If/Else or Loop Limit took, the variables a Set Variables or
  Add to List Variable wrote. Pure data nodes (String Template, Break Object) are not execution
  steps and stay out of the trail.
- Consequence for the design below: the opt-in kinds also include `loop_limit` (branch `again` /
  `limit_reached`, its count) and `add_to_list` (the variable, its new length), both added
  2026-10-11 (completed 1008, 1010); and AbstractFlow's `node_start` feed must take a flow-step
  record as the node's start (1014 scope).

## Dry run (2026-10-11, adversarial, read-only)

Full report and the simulation scripts: `untracked/flow-step-dry-run/flow_step_dry_run.md`,
`untracked/flow-step-dry-run/sim/` (sim.py, size.py, size2.py). Verdict: **GO with changes**. The
first draft (a generic record for every non-effect step carrying the node's output) would have:
faked final answers in the AbstractCode TUI, the Assistant and history seeding (they treat any
completed record with `result.output` as the run's answer); flooded every agent run (ReAct /
CodeAct loops are full of pure transitions, and agent / LLM phases end with a pure
self-transition); recorded stale branch handles; and written ~200 KB per loop item (ForEach's
saved output copies the previous output plus the item; Set history grows each iteration).

## Current code reality (2026-10-11, from the dry run)

- Node handlers run in exactly one place: `abstractruntime/src/abstractruntime/core/runtime.py`
  `_tick_impl` (`plan = handler(...)` ~2646); the pure-transition branch is `if plan.effect is None`
  (~2672). Resume paths only set `current_node` (`_apply_resume_payload` ~3989).
- The run's terminal record is effect-less + COMPLETED (`_append_completion_record` ~3595); event
  records use `emit_event` (`_append_progress_event` ~2304-2345; steer_seen note ~1937-1957).
- Handles: `_set_prev_exec_handle` (`visualflow_compiler/adapters/control_adapter.py:90`); Set
  Variable handlers (`adapters/variable_adapter.py:74-135`), a Sequence's done/return step
  (`control_adapter.py:150-160`) and effect nodes never set it.
- Answer detectors that a wrong shape would trigger: AbstractCode TUI `is_run_output_record`
  (`abstractcode/tui/src/protocol.rs:817-835`, same in `abstractcode-tui`); AbstractAssistant
  `gateway/adapter.py:275` → `events.py:73-135`, `history_seed.py:245-258`; runtime
  `history_bundle.py:370+`.
- Step counts count every completed record (runtime `storage/sqlite.py:1412`, gateway
  `run_metrics.py:43`); run-chat excerpt keeps the first 30 + last 90 records
  (`abstractgateway/src/abstractgateway/routes/gateway.py:11744`).

## Design (to be challenged by the reviews below)

- **Opt-in**: `WorkflowSpec.step_kinds: Optional[Mapping[str, str]] = None` (`spec.py`); only the
  VisualFlow compiler fills it, for sequence, parallel, loop / for / while, if, switch, the
  set_var family (set_var, set_vars, set_var_property), loop_limit and add_to_list (case 2). Not join_exec, not On Flow Start / End, not agent loops, not operators.
- **Shape**: `effect = {type: "emit_event", payload: {name: "abstract.flow_step", scope: "run",
  payload: P}}`, `result = {emitted: true, name: "abstract.flow_step", payload: P}`, with
  `P = {seq, kind, handle, stack_before, stack_after, index?, total?, which?, value_summary?}`.
  Never `result.output`, never effect-less.
- **Bounded**: an allowlist of small scalars (`index`, `total`, `which`, `from_handle`, `branch`);
  a variable's value as `{type, len, bytes}`, never the value.
- **Fresh handle**: `_set_prev_exec_handle` also writes `_temp.step_exec_handle`; the seam clears it
  before the handler and reads it after (`prev_exec_handle` unchanged for join_exec).
- **Ordering**: append after the pause/cancel check and before the save; `seq` from
  `_runtime.flow_step_seq`, advanced in the same save, so a crash replay writes the same `seq` and
  clients dedupe on (run_id, seq). No idempotency lookup (it would read the ledger tail every step).
- **Consumers**: gateway step metrics and run-chat excerpt exclude the name; Observer adds it to
  `HOUSEKEEPING_EVENT_NAMES` (`ui/run_step_kinds.ts:66-71`); AbstractCode web hides it
  (`activity_rows.ts:557-588`). Measured safe as is: TUI (`_ => {}`), panel-chat (unknown events
  trace-only), Assistant run_stats / tool_usage, gateway SSE, runner wake, idempotency cache.
- **Cost measured**: ~6 records per loop item on the `assist` flow, 693 B each, 0.03 ms per append
  (vs 6.4 ms for the run save every pure step already does): ≈ +4 KB per item, +15–25 % ledger
  bytes.

## Required adversarial reviews

This item changes a contract every client reads (the ledger). It must not land on the strength of
the dry run alone:

1. **Design review before code**: an adversarial reviewer attacks this design against the current
   code (seam, opt-in, shape, bounds, ordering, consumer list) and proposes anything simpler or
   safer. Record its findings and the rulings here.
2. **Implementation review after code**: a second adversarial pass on the diff and on real runs
   (a Sequence-of-Set-Variables branch, a 13-item ForEach, an If/Else loop-back, an agent run that
   must stay silent, a pause/resume and a crash replay), checking every consumer above for
   phantom answers, inflated step counts, flooding and payload size.
3. Every guard test is mutation-checked (remove the guard, watch the test fail).

The goal of both reviews: the abstraction and the implementation as clean, simple, robust and
efficient as possible. Findings are fixed or ruled on before closing.

## Acceptance criteria

- [ ] A VisualFlow run records one `abstract.flow_step` per executed control/state node, with the
      right handle, stack and (for loops) item i/n; an agent run records none.
- [ ] Case 2: on the `assist` v4 shape, each loop item records ForEach, Add to history and Add to
      knowledge, and each review records Loop Limit (with its branch) and Add to reviews.
- [ ] No client shows a flow-step record as an answer or ends a run on one (TUI, Assistant,
      history seeding, history bundle); step counts and the run-chat excerpt ignore them.
- [ ] Records stay under ~1 KB whatever the variable sizes; a crash replay dedupes by `seq`.
- [ ] Both adversarial reviews done and their findings resolved; suites pass in each repo.
- [ ] Rollout order: runtime first (records are opt-in and ignored by old clients), then the
      consumer guards, then 1014. The operator's gateway is updated only with their go.

## Receipts

- (to fill)

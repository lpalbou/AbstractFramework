# 0214 — Parallel Read-Only Tool Execution

**Status**: Planned
**Date**: 2026-07-07
**Priority**: High (speed on the dominant read/search batches)
**Components**: abstractruntime (tool_executor, effect_handlers TOOL_CALLS), abstractagent (act_node builtin batching)

## Summary
Execute independent read-only tool calls in a batch concurrently instead of strictly serially, while
preserving ordered, one-at-a-time execution for side-effecting tools. The model is already told to
batch independent read-only calls; the runtime then runs them one by one.

## ADR status
- Governing ADRs: ADR-0006 (durable tool execution), ADR-0016 (tool-calling pipeline).
- ADR impact: May warrant a short note in ADR-0016 on concurrency + result ordering guarantees.

## Context / current code reality
Verified 2026-07-07:
- `MappingToolExecutor.execute` runs a plain `for tc in tool_calls:` loop (`tool_executor.py:321-369`);
  `AbstractCoreToolExecutor.execute` similarly (`:406-452`). No thread pool / asyncio in the tool path.
- `react_runtime.py` act batches consecutive non-builtin tools into one `TOOL_CALLS` effect
  (`:1304-1332`); results are merged back **positionally** by index in the handler
  (`effect_handlers.py:3183`), so ordering is index-based, not completion-based — safe for parallelism.
- Built-in effect-tools (`ask_user`, `recall_memory`, `remember`, `compact_memory`, `delegate_agent`)
  are popped **one per act/observe round-trip** (`react_runtime.py:1138-1145`), each costing extra
  node transitions and state saves.
- The prompt already instructs: batch independent read-only calls; never batch side-effectful tools
  (`logic/react.py:103-107`).

## Problem
Independent reads/searches (`read_file`×4, `search_files`, `list_files`) that the model correctly
batches execute sequentially, so a batch takes the sum of latencies instead of the max. Builtins add
extra round-trips.

## What we want to do
Run the read-only segment of a `TOOL_CALLS` batch concurrently (bounded pool), keep results ordered
by index, and keep side-effecting tools strictly sequential and ordered. Optionally batch consecutive
builtins to cut round-trips.

## Requirements
1. Classify tools in a batch as read-only vs side-effecting (reuse the existing side-effect set:
   `write_file`, `edit_file`, `execute_command`, comms tools; treat unknown/MCP as side-effecting =
   sequential, fail-safe).
2. Execute the read-only subset concurrently with a bounded worker pool; preserve positional result
   mapping (`call_id`/index) exactly as today.
3. Keep side-effecting tools sequential in submitted order; never interleave a side-effect with the
   parallel read set.
4. Respect per-tool timeouts; a hung read must not block the others; surface partial failures per
   call as today.
5. Keep durability intact: the single `TOOL_CALLS` effect still records one result set; idempotency
   key semantics unchanged.
6. (Optional) collapse consecutive builtin calls to reduce act/observe round-trips.

## Non-goals
- No parallel execution of side-effecting tools.
- No change to the durable ledger contract or result schema.
- Not addressing MCP remote concurrency in this item (treat as sequential/fail-safe).

## Dependencies and related tasks
- Touches `react_runtime.py` act_node — coordinate ordering with 0212/0213 (sequence after them).

## Expected outcomes
- A batch of N independent reads completes in ~max(latency) rather than ~sum(latency).
- Result ordering and per-call success/error are byte-identical to the serial path.
- Side-effect ordering is provably preserved.

## Validation
- Unit: batch of 4 read tools with artificial per-tool delays completes in ~1× delay, not 4×;
  assert result order matches input order; assert a batch mixing reads + one write executes the
  write only after/around reads deterministically and never concurrently.
- Live (endpoint `http://127.0.0.1:8317/v1`): a task that reads several files up front; measure
  wall-clock for the read batch before vs after.

## Progress checklist
- [x] Read-only vs side-effect classification in the executor/handler.
- [x] Bounded concurrent execution of the read subset with positional merge.
- [x] Sequential guarantee + test for side-effect ordering.
- [ ] (Optional) builtin batching — still open (each builtin costs one act/observe round-trip).
- [x] Unit + LIVE timing evidence (2026-07-08, OVH `gpt-oss-120b` + real web I/O): the model
      emitted a genuine 4-call `skim_url` batch in one response; replaying that exact
      model-generated batch through `MappingToolExecutor` 3× each way: median 3.06 s with the
      parallel path disabled vs 1.46 s enabled — **2.09× speedup**; the live in-run batch
      (act→observe) measured 1.45 s, matching the parallel path.

## Guidance for the implementing agent
Parallelize at the executor layer where results already merge by index; do not change the effect or
ledger contract. Fail safe: anything not provably read-only runs sequentially.

# Planned: Runtime recursive subworkflow budget

## Metadata
- Created: 2026-06-05
- Status: Planned
- Completed: N/A

## ADR status
- Governing ADRs: ADR-0018 durable run gateway and remote host control plane, ADR-0032 package dependency boundaries and gateway-first apps
- ADR impact: Needs new ADR or a focused ADR-0032 revision before completion. The ADR must define workflow identity, recursion semantics, cap defaults, overrides, and failure shape.

## Context
Recursive Subflows are already an intended capability. AbstractFlow labels direct self-subflow selection as recursive, and the Runtime compiler allows cyclic subflow references. The missing piece is a runtime-owned budget so intentional recursion has a clean default guard.

The user-facing default should be `3` recursive calls. The implementation must make this precise before code lands.

## Current code reality
- `abstractruntime/src/abstractruntime/core/runtime.py::_handle_start_subworkflow` resolves the target workflow and calls `self.start(..., parent_run_id=run.run_id)` without checking recursive ancestry first.
- The same handler covers sync subworkflow execution, async execution, async+wait, fire-and-forget, and `wrap_as_tool_result` behavior.
- `abstractruntime/src/abstractruntime/visualflow_compiler/compiler.py::compile_visualflow_tree` explicitly allows subflow cycles and compiles each flow id once.
- Visual Agent nodes lower to `START_SUBWORKFLOW`, so a budget based on generic child depth would incorrectly affect ordinary Agent execution.
- `RunState` persists `parent_run_id`, which is the right durable basis for reconstructing active ancestry after waits or Gateway restarts.
- `_limits.max_iterations` and Agent `max_iterations` are different concepts and must not be reused for recursive subworkflow calls.

## Problem
Recursive workflows can expand the run tree indefinitely until a different failure occurs. Static cycle checks cannot solve this because valid recursive flows may have branch-based base cases, and API or bundle execution can bypass the Flow editor.

## What we want to do
Add a Runtime-owned recursive subworkflow budget that denies over-limit recursive starts before creating the child run. The default policy should allow intentional recursion while preventing accidental runaway behavior.

## Why
Runtime owns workflow correctness, waits, run state, and ledger records. Enforcing at `START_SUBWORKFLOW` gives one choke point for Flow Subflow nodes, Agent child workflows, direct effects, sync mode, async+wait mode, and Gateway-hosted execution.

## Requirements
- Define canonical workflow identity for recursion checks. Bundle-qualified identities must be used when bundles or catalog hosts namespace workflows.
- Define recursion as target canonical workflow identity already present in the active persisted parent-run ancestry.
- Do not count generic child depth. A deep non-recursive chain `A -> B -> C -> D` must not be blocked by the recursive subworkflow budget.
- Do not count sibling invocations after prior siblings have completed unless they are active ancestors of the current start.
- Recommended user-facing semantics: `max_recursive_subflow_calls = 3` allows three recursive starts beyond the first active instance. For `A -> A`, the first child `A` is recursive call 1. For `A -> B -> A`, the second `A` is recursive call 1.
- If implementers instead choose an active-frame cap, the name and UI text must say that clearly, for example `max_active_workflow_frames`.
- Check the budget after resolving the target workflow and before calling `self.start(...)`.
- Deny over-limit starts without creating a child run.
- Emit a stable error code such as `recursive_subworkflow_limit_exceeded`.
- Ledger/debug output must include the target canonical workflow id, effective cap, current recursive call count, and matched ancestor run ids where safe to expose.
- `wrap_as_tool_result=True` must preserve tool-result semantics with `success: false` instead of stranding the parent in a wait state.
- Async+wait must never enter `WAITING/SUBWORKFLOW` unless a child run id was actually created.
- Missing, deleted, or cyclic parent references must fail closed with a diagnostic error rather than infinite ancestry traversal.
- Runtime config and `_limits` must support a default cap and an explicit override path. Node/request overrides may lower the cap; raising the cap should require host/runtime policy allowance.

## Suggested implementation
1. Add a Runtime config and run-limit field for recursive subworkflow calls, with default `3`.
2. Add an ancestry helper that walks persisted `parent_run_id` links through the run store, detects malformed parent cycles, and returns canonical workflow identities.
3. Resolve the target `WorkflowSpec` and canonical identity in `_handle_start_subworkflow`.
4. Compute recursive call count from active ancestry before `self.start(...)`.
5. Return a failed `EffectOutcome` with stable structured details when the cap is exceeded.
6. Preserve existing sync, async, async+wait, fire-and-forget, and tool-result wrapping behavior for allowed starts.
7. Add docs to `abstractruntime/docs/limits.md` or the equivalent limits reference.

## Scope
- `abstractruntime` runtime config, limits, run-state ancestry helper, `START_SUBWORKFLOW` handler, ledger/error details, and tests.
- Runtime docs for the recursive subworkflow budget.
- Minimal compatibility hooks for bundle-qualified workflow identity if existing identifiers are underqualified.

## Non-goals
- Do not block compile-time subflow cycles.
- Do not make Gateway responsible for the enforcement decision.
- Do not change Agent ReAct `max_iterations`.
- Do not solve generic fan-out, run-tree breadth, or provider/tool-cost quotas.
- Do not implement same-flow feedback-loop limits in this item; see `0185`.

## Dependencies and related tasks
- `0183_flow_recursive_subflow_analysis_and_controls.md`.
- `0184_gateway_recursion_observability_and_runner_coverage.md`.
- `0186_recursion_contract_adr_docs_and_vocabulary.md`.
- ADR-0018 and ADR-0032.

## Expected outcomes
- Recursive Subflows have a default runtime cap of `3` recursive calls.
- Self-recursion and mutual recursion are denied cleanly when they exceed the cap.
- Non-recursive deep subworkflow chains and normal Agent child runs continue to work.
- Denied starts produce stable ledger/debug details and do not create orphan child runs.
- Gateway-hosted runs cannot get stuck waiting for a child that was never started.

## Validation
- Runtime unit tests for direct self-recursion at the boundary.
- Runtime unit tests for mutual recursion `A -> B -> A`.
- Runtime unit tests for a deep non-recursive chain.
- Runtime tests for sync, async+wait, fire-and-forget, and `wrap_as_tool_result`.
- Durable store test using `JsonFileRunStore` or equivalent reload while parent ancestry exists.
- Regression test proving ordinary Agent subworkflow starts are not capped unless they recursively call their own workflow identity.
- Error-shape test asserting `recursive_subworkflow_limit_exceeded` and diagnostic fields.

## Progress checklist
- [ ] Write or update the ADR contract before closing the implementation.
- [ ] Define canonical workflow identity and cap semantics.
- [ ] Add Runtime config and `_limits` support.
- [ ] Add durable ancestry traversal with malformed-chain protection.
- [ ] Enforce in `_handle_start_subworkflow` before child creation.
- [ ] Add ledger/error details and docs.
- [ ] Add runtime tests across start modes and durability.

## Guidance for the implementing agent
Start from the current Runtime code, not this backlog text. Re-check the exact `START_SUBWORKFLOW` handler and existing tests before editing. Keep enforcement local to Runtime's canonical start-subworkflow path so Gateway catalog ACLs and direct Runtime use remain compatible.

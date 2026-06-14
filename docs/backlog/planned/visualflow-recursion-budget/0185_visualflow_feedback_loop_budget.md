# Planned: VisualFlow feedback loop budget

## Metadata
- Created: 2026-06-05
- Status: Planned
- Completed: N/A

## ADR status
- Governing ADRs: ADR-0032 package dependency boundaries and gateway-first apps
- ADR impact: May revise existing ADR or the new recursion contract ADR if same-flow reentry semantics become durable workflow policy.

## Context
The original user workflow was an improvement loop on one canvas: run an Agent, evaluate the result, update recommendations, and route execution back to the Agent for up to a small number of cycles. That is not the same thing as a recursive Subflow call. It is a same-flow feedback loop and needs its own budget concept.

## Current code reality
- `abstractflow/src/utils/validation.ts` intentionally allows exec self-loops and no longer rejects all execution fan-in.
- `abstractruntime/src/abstractruntime/visualflow_compiler/visual/executor.py` lowers multi-entry execution through internal join/path-mux behavior.
- `abstractruntime/src/abstractruntime/visualflow_compiler/adapters/control_adapter.py` has `join_exec` behavior and existing loop adapters have their own iteration guards.
- Older backlog item `135_abstractflow_exec_fanin_joinexec_and_path_mux.md` describes the intended loopback authoring UX, but it predates current implementation state and should be audited before further work.
- There is no clear user-facing "run this feedback cycle at most N times" control for arbitrary same-flow improvement loops.

## Problem
Users can draw feedback cycles that are semantically useful but hard to bound. Reusing Subflow recursion limits or Agent max iterations for these loops would be confusing and technically wrong. A tight same-flow loop without a wait/base case can also consume runtime ticks quickly.

## What we want to do
Add a runtime-enforced feedback-loop budget for same-flow reentry boundaries, exposed through a clear Flow authoring control. This should let users express workflows such as "up to 3 improvement cycles" without turning the flow into recursive Subflow calls.

## Why
The clean model is separate budgets for separate execution concepts:

- Recursive Subflow calls: a workflow starts itself directly or indirectly. See `0182`.
- Agent loop iterations: an Agent's internal reasoning/tool loop.
- For/While iteration guards: explicit loop nodes.
- Feedback loop cycles: execution re-enters an earlier canvas region through a join/reentry boundary.

## Requirements
- Audit current join/path-mux implementation before changing it, because backlog item `135` is stale relative to code.
- Define a durable feedback-loop boundary. Likely candidates are `join_exec` reentry points, an explicit `Loop Limit` node, or a generated internal boundary when a cycle is detected.
- Runtime must enforce the budget with durable counters that survive waits/resumes and Gateway restarts.
- Flow must expose the control with a label such as `Feedback loop cycles`, not `recursion` or `max iterations`.
- Default should be conservative and user-comprehensible. If the product default is `3`, label it as "up to 3 feedback cycles" and document whether the initial pass counts.
- Static cycle detection may warn about unbounded cycles, but runtime remains the enforcement owner.
- Tight cycles without WAIT-like yields should warn strongly or require an explicit budget.
- The implementation must preserve pure-node recomputation correctness on loop reentry.
- The budget must not cap ordinary fan-in where multiple paths converge once without forming a cycle.
- The budget must not change Subflow recursion behavior; that is owned by `0182`.

## Suggested implementation
1. Audit current join/path-mux lowering, validation, serialization, and tests against item `135`.
2. Decide the boundary model:
   - per-`join_exec` max traversals;
   - explicit `Loop Limit` control node;
   - generated hidden loop boundary from cycle analysis.
3. Add a durable counter in Runtime keyed by run id, flow id, and boundary id.
4. Enforce before re-entering the bounded loop body and emit a stable error or controlled false branch.
5. Add Flow cycle analysis that can attach the budget to the correct boundary and explain the selected cycle.
6. Add run-history details showing current feedback-cycle count and effective cap.
7. Update the stale `135` item after the code audit, moving it toward completed, deprecated, or revised planned state.

## Scope
- AbstractFlow cycle/reentry detection and authoring controls.
- AbstractRuntime VisualFlow executor/control adapter support for durable feedback-loop counters.
- Gateway/Flow run history only where needed to expose stable runtime details.
- Backlog cleanup of item `135` once the implementation reality is confirmed.

## Non-goals
- Do not use this mechanism for recursive Subflow calls.
- Do not change Agent internal max-iteration behavior.
- Do not add generic global run depth or fan-out quotas.
- Do not rely only on browser preflight.
- Do not silently insert hidden state that users cannot inspect when debugging.

## Dependencies and related tasks
- `0186_recursion_contract_adr_docs_and_vocabulary.md` for terminology.
- Older planned item `docs/backlog/planned/135_abstractflow_exec_fanin_joinexec_and_path_mux.md`.
- `0182_runtime_recursive_subworkflow_budget.md` only as a terminology boundary, not as an implementation dependency.

## Expected outcomes
- A user can author an improvement loop and cap it at a chosen number of feedback cycles.
- Runtime enforces the cap durably across waits, resumes, and Gateway-hosted runs.
- The UI distinguishes feedback-loop cycles from recursive Subflow calls and Agent iterations.
- Existing one-time fan-in remains valid and uncapped.
- Pure-node outputs recompute correctly on reentry.

## Validation
- Unit tests for cycle detection and budget placement.
- Runtime tests for bounded same-flow feedback loops with and without waits.
- Runtime durability test across resume/reload.
- Regression test that ordinary fan-in without a cycle is not capped.
- Regression test that Subflow recursion cap behavior is unaffected.
- Browser QA showing a loop configured for 3 improvement cycles and a clear over-limit result.

## Progress checklist
- [ ] Audit current join/path-mux implementation against stale item `135`.
- [ ] Choose explicit boundary model.
- [ ] Add durable Runtime counter and enforcement.
- [ ] Add Flow controls and cycle warnings.
- [ ] Add run-history diagnostics.
- [ ] Update or close stale backlog item `135`.

## Guidance for the implementing agent
Do not start by adding another generic `max_iterations` field. First identify the reentry boundary that Runtime can observe durably, then make the Flow UI explain that exact boundary.

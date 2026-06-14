# VisualFlow recursion budget backlog track

## Status
Planned

## Purpose
This track defines and implements clean limits for recursive orchestration in AbstractFlow and AbstractRuntime. It separates two related but different user problems:

- recursive Subflow/workflow calls, such as `A -> A` or `A -> B -> A`;
- same-flow feedback loops, such as an improvement cycle that wires a later node back to an earlier Agent.

Both need runtime enforcement, but they should not share one vague "max iterations" setting. Runtime remains the source of truth for execution safety. AbstractFlow should detect and explain likely recursion, and Gateway should expose durable results without becoming the enforcement layer.

## Decision question
How should AbstractFramework cap recursive workflow execution by default while preserving intentional recursive flows, durable Gateway runs, and clear user controls?

## Current reality
- `abstractruntime` starts child workflows in `Runtime._handle_start_subworkflow(...)` before checking any recursion budget.
- `compile_visualflow_tree(...)` intentionally allows cyclic subflow references and compiles each workflow once, so compile-time rejection is not the right boundary.
- Visual Agent execution also lowers to `START_SUBWORKFLOW`, so enforcement must count recursive workflow identity in the active ancestry, not generic child depth.
- `abstractflow` labels only direct self-subflow selection as recursive. It does not analyze mutual cycles such as `A -> B -> A`.
- Same-flow exec feedback loops are allowed and are handled through the join/path-mux direction captured by older backlog item `135`, but that item is stale relative to current code and should not hide recursive subflow policy.

## Architecture alternatives considered

### Alternative A: block recursion in AbstractFlow
This would be simple for the browser, but it fails for valid recursive flows, imported bundles, API-started runs, and branch-protected base cases. It also duplicates execution policy outside the runtime.

### Alternative B: warn in AbstractFlow only
This gives a friendly authoring experience, but it does not protect Gateway, bundled execution, direct Runtime use, or long-running recursive workflows after reload.

### Alternative C: enforce in Gateway
Gateway sees run trees and can project policy to clients, but Runtime owns workflow semantics, waits, effects, ledgers, and correctness. Gateway-only enforcement would miss in-process Runtime use and could fight catalog/ACL wrappers.

### Alternative D: enforce at Runtime `START_SUBWORKFLOW`, with Flow/Gateway support
Runtime can check the parent-run ancestry before creating a child run. This single boundary covers VisualFlow Subflow nodes, Agent child workflows, sync starts, async waits, fire-and-forget starts, and direct effect usage. Flow adds detection and controls; Gateway adds policy projection, runner regression tests, and observability.

## Synthesis
Use Alternative D.

Recursive subworkflow enforcement belongs in Runtime. A recursive call is a target canonical workflow identity that already appears in the active persisted parent-run ancestry. The default user-facing budget is `3` recursive calls beyond the first active instance, unless the final ADR chooses an explicitly named active-frame cap instead.

Do not conflate this with Agent loop iterations, For/While loop guards, generic run-tree depth, fan-out, or same-flow feedback cycles.

## Items
- `0182_runtime_recursive_subworkflow_budget.md`: add the Runtime-owned recursive subworkflow budget and failure contract.
- `0183_flow_recursive_subflow_analysis_and_controls.md`: add AbstractFlow call-graph detection, warning/preflight behavior, and synchronized authoring controls.
- `0184_gateway_recursion_observability_and_runner_coverage.md`: keep Gateway out of enforcement while adding projection, bundle identity coverage, and no-stuck-parent tests.
- `0185_visualflow_feedback_loop_budget.md`: solve same-flow improvement-cycle limits separately from subworkflow recursion.
- `0186_recursion_contract_adr_docs_and_vocabulary.md`: write the durable ADR/docs and clean up user-facing iteration terminology.

## Reading order
Start with `0186` if the contract is still ambiguous. Implement `0182` before `0183` and `0184`, because UI and Gateway behavior must match the Runtime result. Treat `0185` as the separate answer to canvas feedback loops.

## Related material
- ADR-0018 durable run gateway and remote host control plane.
- ADR-0032 package dependency boundaries and gateway-first apps.
- `docs/backlog/planned/135_abstractflow_exec_fanin_joinexec_and_path_mux.md`.
- `abstractruntime/src/abstractruntime/core/runtime.py`.
- `abstractruntime/src/abstractruntime/visualflow_compiler/compiler.py`.
- `abstractruntime/src/abstractruntime/visualflow_compiler/visual/executor.py`.
- `abstractflow/src/utils/subflowPins.ts`.
- `abstractflow/src/utils/preflight.ts`.
- `abstractgateway/src/abstractgateway/runner.py`.

## Non-goals
- Do not ban recursive workflows.
- Do not make Gateway the execution-policy owner.
- Do not reuse Agent `max_iterations` for workflow recursion.
- Do not solve generic fan-out or resource quotas in this track.
- Do not silently change old flows without migration notes and an override path.

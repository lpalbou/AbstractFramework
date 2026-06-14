# Planned: Flow recursive Subflow analysis and controls

## Metadata
- Created: 2026-06-05
- Status: Planned
- Completed: N/A

## ADR status
- Governing ADRs: ADR-0032 package dependency boundaries and gateway-first apps
- ADR impact: May revise existing ADR or depend on the ADR from `0186` if the user-facing cap semantics are still unsettled.

## Context
AbstractFlow should help authors see and configure recursive Subflow behavior, but it should not be the enforcement authority. Recursive calls may be valid when a branch provides a base case, and published bundles or direct Gateway/API execution can bypass browser preflight.

## Current code reality
- `abstractflow/src/utils/subflowPins.ts` marks only the current flow option as `this flow (recursive)`.
- `abstractflow/src/components/PropertiesPanel.tsx` warns only for direct self-subflow selection.
- There is no saved-flow call-graph analysis for mutual cycles such as `A -> B -> A`.
- `FlowNodeData` already stores Subflow node state such as `subflowId` and effect config. That is a better persistence location than edge metadata.
- `VisualEdge` serialization is intentionally simple, and route-override display edges are reconstructed rather than serialized as durable edge config.
- `abstractflow/src/utils/preflight.ts` checks reachability and capability issues but not recursive Subflow cycles.

## Problem
Users can create recursive Subflows without a clear explanation of what will happen or how many recursive calls are allowed. They can also create mutual recursion that the UI does not identify. If a node-level budget is added without call-graph detection, users will not know when or why it matters.

## What we want to do
Add AbstractFlow call-graph analysis, warnings, preflight checks, and controls for recursive Subflow calls. Keep these controls synchronized with the right-panel inspector and the node UI where appropriate, but let Runtime remain the final authority.

## Why
Runtime enforcement protects execution, but Flow authoring should make recursion intentional. A user should see that selecting a Subflow creates a cycle, understand the cycle path, and be able to set a clear cap such as "Recursive Subflow calls: 3".

## Requirements
- Build a saved-flow Subflow call graph from reachable VisualFlow definitions.
- Detect direct recursion (`A -> A`) and mutual recursion (`A -> B -> A`).
- Return cycle paths that can be shown in UI and preflight output.
- Treat static cycle detection as advisory. Do not block save or publish solely because recursion exists.
- Show a numeric control for recursive Subflow budget when the selected Subflow can create a cycle.
- Default the control to the Runtime default, currently intended as `3`.
- Persist the node-specific setting in Subflow node data or typed effect config, not on edges.
- Keep the node control and right-panel control in sync if both are shown.
- Use clear labels:
  - `Recursive Subflow calls` for this feature.
  - `Agent loop iterations` for Agent ReAct loops.
  - `Loop iteration guard` for For/While nodes.
  - `Feedback loop cycles` for same-flow loopback budgets.
- Warn that recursive flows need a base case. Do not imply that a budget is a substitute for correct branch logic.
- Preserve imported/legacy flows that do not yet have an explicit budget by showing the Runtime default.
- Keep intra-flow exec feedback loops valid; they are covered by `0185`, not this item.

## Suggested implementation
1. Add a pure helper that extracts Subflow refs from saved VisualFlows and returns a call graph.
2. Add cycle detection with cycle paths and tests for direct, mutual, disconnected, and branch-protected graphs.
3. Add selector and inspector affordances that show cycle paths and the effective recursive-call budget.
4. Persist optional per-node budget under Subflow node config/effect config.
5. Lower the budget into the `START_SUBWORKFLOW` payload only as a request to Runtime. Runtime policy still decides the effective cap.
6. Extend preflight with warnings for recursive cycles and invalid budget values.
7. Add docs/tooltips that distinguish recursive Subflow calls from Agent iterations and same-flow feedback loops.

## Scope
- AbstractFlow saved-flow analysis utilities.
- Subflow node UI and right-panel inspector controls.
- Flow serialization/migration for optional budget config.
- Preflight warnings and tests.
- Runtime VisualFlow lowering only where needed to include the requested cap in `START_SUBWORKFLOW` payloads.

## Non-goals
- Do not enforce the cap in the browser.
- Do not forbid recursive Subflows.
- Do not add edge-level metadata for this budget.
- Do not solve same-flow feedback loops in this item.
- Do not make Flow own canonical workflow identity for Runtime enforcement.

## Dependencies and related tasks
- `0182_runtime_recursive_subworkflow_budget.md` must define the authoritative Runtime contract.
- `0186_recursion_contract_adr_docs_and_vocabulary.md` must settle wording before final UI labels ship.
- Related older item: `docs/backlog/planned/135_abstractflow_exec_fanin_joinexec_and_path_mux.md`.

## Expected outcomes
- Flow authors see when a selected Subflow creates direct or mutual recursion.
- Flow authors can set an explicit recursive-call budget, defaulting to `3`.
- Preflight reports recursive call paths with actionable text.
- Existing non-recursive and legacy Subflow nodes continue to behave as before.
- Runtime receives budget hints without losing enforcement authority.

## Validation
- Unit tests for call graph extraction and cycle detection.
- UI/component tests for direct and mutual recursion warnings.
- Serialization tests proving the optional budget round-trips with the node.
- Preflight tests proving recursive cycles warn and non-recursive graphs do not.
- Runtime lowering test proving a configured budget appears in `START_SUBWORKFLOW` payloads.
- Manual browser QA with:
  - direct self-subflow;
  - `A -> B -> A`;
  - non-recursive nested subflow;
  - a same-flow feedback loop that should not show Subflow recursion controls.

## Progress checklist
- [ ] Add saved-flow call-graph extraction.
- [ ] Add cycle detection and cycle-path tests.
- [ ] Add Subflow node and inspector budget controls.
- [ ] Persist optional budget on node config/effect config.
- [ ] Extend preflight warnings.
- [ ] Lower the requested budget to Runtime.
- [ ] Add terminology docs and manual QA screenshots.

## Guidance for the implementing agent
Re-check the current Subflow selector, properties panel, serialization, and VisualFlow lowering before editing. Keep analysis pure and testable. Use warnings and clear labels; do not make static detection a hard blocker.

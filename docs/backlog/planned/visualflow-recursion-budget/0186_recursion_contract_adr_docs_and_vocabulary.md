# Planned: Recursion contract ADR, docs, and iteration vocabulary

## Metadata
- Created: 2026-06-05
- Status: Planned
- Completed: N/A

## ADR status
- Governing ADRs: ADR-0018 durable run gateway and remote host control plane, ADR-0032 package dependency boundaries and gateway-first apps
- ADR impact: Needs new ADR unless ADR-0032 is intentionally revised. The contract establishes durable execution policy and should not remain only in backlog text.

## Context
Several execution concepts currently sound similar to users and developers:

- Agent max iterations;
- recursive Subflow calls;
- same-flow feedback-loop cycles;
- For/While loop iteration guards;
- Runtime tick `max_steps`;
- generic run-tree depth or fan-out.

The recursive Subflow budget will become a platform contract. It needs an ADR, docs, and consistent labels before implementation closes.

## Current code reality
- Runtime/Gateway ADRs already place durable workflow correctness in Runtime and control-plane projection in Gateway.
- Existing UI and type defaults around Agent max iterations have drifted historically; previous product feedback asked for Agent default max iterations to be `20`, while older notes mention `50`.
- AbstractFlow already uses user-facing labels such as Subflow, Agent, For/While, and flow run details, but there is no single vocabulary guide for iteration and recursion limits.
- Runtime docs mention limits, but no recursive subworkflow budget exists yet.
- Flow run UI currently displays nested subruns; a display depth value can be confused with an execution recursion cap if labels are not explicit.

## Problem
Without a durable contract and vocabulary cleanup, the new budget can be misunderstood or implemented inconsistently. A user asking for "3 recursions" could receive a root-inclusive active-frame cap, an Agent ReAct cap, a same-flow loop cap, or a Gateway display-depth cap.

## What we want to do
Create the architecture contract and documentation that make each execution budget precise. Align user-facing labels and defaults so Flow authors can tell which budget they are setting.

## Why
This is durable workflow policy. It affects correctness, run safety, migration behavior, Gateway-hosted runs, and user mental models. Backlog text is not strong enough as the final authority.

## Requirements
- Write a new ADR, or revise ADR-0032 deliberately, before closing the runtime implementation.
- Define canonical workflow identity for recursion, including bundle-qualified ids.
- Define the recursive-call cap precisely:
  - what counts as a recursive call;
  - whether the root frame counts;
  - how mutual recursion is counted;
  - what happens after waits/restarts;
  - how malformed parent ancestry is handled.
- Define default policy, intended default `3`, and override policy.
- Define failure semantics and stable error code.
- Document the difference between:
  - `Recursive Subflow calls`;
  - `Feedback loop cycles`;
  - `Agent loop iterations`;
  - `Loop iteration guard`;
  - Runtime tick quantum / `max_steps`;
  - Gateway run-detail display depth.
- Audit and align Agent max-iteration defaults and labels. If the product default is `20`, make UI, Runtime, serialization, docs, and tests agree.
- Add migration notes for existing recursive flows that relied on unbounded behavior.
- Add docs for disabling or raising the cap in trusted/local/development contexts, subject to Runtime/Gateway policy.
- Ensure error messages tell users to add a base case or raise the explicit budget, not to change unrelated Agent settings.

## Suggested implementation
1. Draft an ADR titled "Workflow recursion and loop-budget contract" or equivalent.
2. Update Runtime, Flow, and Gateway docs once implementation details land.
3. Add a vocabulary table in the Flow docs or limits docs.
4. Audit Agent max-iteration defaults across node templates, serialization, pin disclosure, Runtime defaults, and docs.
5. Add UI copy and test expectations that use the approved labels.
6. Add release/migration notes if the cap can affect existing flows.

## Scope
- ADR under `docs/adr/`.
- Runtime docs for limits and failure semantics.
- AbstractFlow docs/help text/tooltips where these controls appear.
- Gateway docs if policy projection or admin configuration is exposed.
- Tests or snapshots that lock label/default consistency where practical.

## Non-goals
- Do not implement Runtime enforcement in this item; see `0182`.
- Do not implement Flow controls in this item; see `0183` and `0185`.
- Do not resolve all future resource quota work.
- Do not hide a durable policy decision in comments or UI copy only.

## Dependencies and related tasks
- `0182_runtime_recursive_subworkflow_budget.md`.
- `0183_flow_recursive_subflow_analysis_and_controls.md`.
- `0184_gateway_recursion_observability_and_runner_coverage.md`.
- `0185_visualflow_feedback_loop_budget.md`.
- ADR-0018 and ADR-0032.

## Expected outcomes
- There is one durable ADR contract for recursive workflow calls and related loop-budget terminology.
- Product labels and docs no longer conflate recursion, Agent iterations, same-flow loops, and display nesting.
- Agent max-iteration default is consistent across code and docs.
- Existing-flow migration behavior is explicit.
- Future agents can implement the runtime and UI work without re-litigating semantics.

## Validation
- ADR accepted or ADR-0032 revised with the required contract.
- Docs contain a vocabulary table for the execution budgets.
- Tests or snapshots cover user-facing labels/defaults where feasible.
- A grep/audit confirms no stale label implies recursive Subflow calls are Agent max iterations or Gateway display depth.
- Existing recursive-flow examples include a base case and documented budget behavior.

## Progress checklist
- [ ] Draft and accept/revise the ADR.
- [ ] Define precise recursive-call counting semantics.
- [ ] Document default `3` and override policy.
- [ ] Audit Agent max-iteration default and labels.
- [ ] Update Runtime/Flow/Gateway docs.
- [ ] Add migration/release notes if needed.
- [ ] Add label/default consistency tests where practical.

## Guidance for the implementing agent
Use the ADR skill for the durable contract. Keep wording boring and precise. The goal is not new jargon; it is preventing users and maintainers from setting the wrong budget.

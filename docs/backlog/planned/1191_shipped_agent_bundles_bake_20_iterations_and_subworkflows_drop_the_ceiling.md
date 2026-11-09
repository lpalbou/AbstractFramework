# 1191 — Shipped agent bundles still bake 20 iterations, and a START_SUBWORKFLOW child drops the operator's ceiling

> Package: AbstractFlow (`scripts/build_basic_agent_bundle.py`, `scripts/build_goal_agent_workflow.py`), AbstractGateway (shipped bundles in `flows/bundles/`), AbstractRuntime (`core/runtime.py` START_SUBWORKFLOW handler)
> Type: defect
> Status: planned — next wave
> Created: 2026-11-10
> Priority: P2
> Labels: iterations, limits, flow, bundles, runtime, next-wave

## Summary

Two gaps left by the "50 everywhere" iteration work of 2026-11-08/09, both found by the audit of 2026-11-09 and both
deferred to the next wave. (1) The basic-agent and goal-agent bundle builders bake `max_iterations` 20 into the
workflows the gateway ships, and the builder's own check refuses any other value. (2) A child run started through
START_SUBWORKFLOW inherits the parent's iteration budget but not the operator's `max_iterations_ceiling`, so a
VisualFlow child of an entity run with an explicit budget above the ceiling is not refused. One item, two small fixes.

## Why

The operator's "50 everywhere" (running log `untracked/release-2026-11-07/RESUME.md` 2026-11-09 15:20; the ladder
request > stored > workflow > 50: runtime `4e2e55e`, gateway `4d56fef0`). The ceiling is the operator's cap on entity
runs (gateway `config.py:67`, served at `entity_visits.py:780-793`).

## Current code reality (checked 2026-11-10 on `main`)

- `abstractflow/scripts/build_basic_agent_bundle.py:39` `RULED_MAX_ITERATIONS = 20` (a 2026-07-11 ruling); `:193-197`
  refuses any other pin. `abstractflow/scripts/build_goal_agent_workflow.py:264` worker Agent
  `pin_defaults={"max_iterations": 20, …}`.
- Shipped gateway bundles (read from the zip on 2026-11-10): `basic-agent.flow` and `basic-agent@0.0.5.flow` carry 20;
  `abstractassistant-orchestrator@0.0.15.flow` 20 and 24 (×4); `coding-agent@0.2.8.flow` 16 and 30.
- Mitigated, not fixed: gateway `fa8286e2` (operator decision D2, 2026-11-09) stores `agents.max_iterations = 50` once
  on a fresh data dir, so a fresh install's runs get 50 (stored beats workflow). Still affected: a host without that
  stored value (a cleared setting, other hosts running these bundles) falls to the bundle's 20/24.
- `abstractruntime/src/abstractruntime/core/runtime.py:5281-5289` carries the parent's `max_iterations` into the child's
  `_limits`, never `max_iterations_ceiling`; the ceiling is enforced only in `Runtime.start` (`:1603-1630`) from the
  run's own `_limits`. AbstractAgent `3d3fdf0` closes the gap for delegated sub-agents only (child = min(explicit,
  parent), ceiling inherited).

## Scope

### In scope

1. Bundles: the operator confirms that "50 everywhere" retires the 2026-07-11 ruled 20; then either the builders pin 50
   (and the check follows) or they pin nothing so the ladder falls to the host default — one choice, recorded here;
   rebuild and re-ship the affected bundles with new versions (never the same version repacked).
2. Runtime: START_SUBWORKFLOW copies `max_iterations_ceiling` into the child's `_limits` beside the budget, so
   `Runtime.start` refuses a child above the ceiling with the same sentence as a root run.
3. Tests: a shipped basic-agent run on a host with nothing stored gets the chosen default; a Subflow/Agent child with an
   explicit 80 under a ceiling of 50 is refused; each red without its fix.

### Out of scope

- Recursion depth budgets (planned track [0182](visualflow-recursion-budget/0182_runtime_recursive_subworkflow_budget.md),
  the natural home if the ceiling work grows).
- The fresh-install seed (done, `fa8286e2`).

## Acceptance criteria

- [ ] The operator's choice on the ruled 20 recorded in this item.
- [ ] No shipped bundle bakes a value that contradicts that choice (zip check in the gateway's bundle test).
- [ ] A START_SUBWORKFLOW child cannot exceed the ceiling (runtime test, red without the copy).

## Receipts

- `untracked/release-2026-11-07/audit-fable/PACKAGES.md` section (b) "Known gates"; `RESUME.md` 2026-11-09 13:40, 14:30,
  15:20; gateway `fa8286e2` commit message ("The bundle builders still baking 20 is a next-wave note").

# Proposed: Micro-model gating and hierarchical multimodal planning

## Metadata
- Created: 2026-06-14
- Status: Proposed
- Completed: N/A

## ADR status
- Governing ADRs: ADR-0032, ADR-0035, ADR-0036
- ADR impact: None until the capability-action contract and Runtime policy surfaces are real enough to support a stable planning/gating design.

## Context
The current multimodal direction already suggests a hierarchical control flow:

- deterministic route/readiness/policy pre-gates;
- a cheap classifier/router for intent and risk;
- a main coordinator that chooses typed actions or workflows;
- specialist execution through Gateway/Runtime;
- evaluator or human-approval loops only when needed.

This aligns with current external agent practice and with the framework’s existing split between
Gateway projection, Runtime durability, and published workflows.

It also assumes the dual-entrypoint model stays intact:

- Gateway-first persistent agents use the durable action/policy surface;
- direct Core apps remain lower-level and are not forced into the same high-level gating stack by
  default.

Any future coordinator or super-agent planner should consume the shared Gateway action/workflow
surface plus replay-safe Runtime action summaries, not raw capability-default rows or app-local
router hints.

## Current code reality
- Assistant still uses one main multimodal router prompt rather than a layered cheap-gate/coordinator structure.
- Gateway already knows route availability/configuration truth, which could support deterministic
  pre-gates before any model invocation.
- Runtime and workflows already support durable child runs, waits, and composed execution, but no
  dedicated micro-model gating pipeline exists yet.
- Existing approval policy is stronger for tools/side effects than for generation-specific cost/risk
  classes.

## Problem or opportunity
Once typed capability actions exist, the next scaling pressure will be decision quality and cost:
which requests need only deterministic routing, which need a cheap small-model classifier, which
need a richer coordinator, and which need an evaluator or human gate?

## Proposed direction
Investigate a hierarchical planning stack:

1. deterministic Gateway pre-gates for readiness, source-artifact presence, and policy;
2. a cheap micro-model for intent/risk/task-family classification;
3. a richer coordinator that chooses actions/workflows and composes multi-step plans;
4. evaluator or human-review loops only for ambiguous, high-cost, or high-risk requests.

## Why it might matter
- Reduces cost and latency for obvious requests.
- Makes multimodal growth more manageable as action count expands.
- Creates a cleaner place for risk/cost gating than ad hoc prompt logic.

## Promotion criteria
- `0201` through `0204` land enough shared action/policy structure to support stable gating inputs.
- `0207` lands enough replay-visible action facts that gating decisions can be inspected across
  lightweight apps instead of staying UI-local.
- `0209` lands enough durable-agent adoption that planners consume the shared substrate instead of
  private prompt/router conventions.
- Real cost/latency data shows a need to split cheap classification from rich coordination.
- There is evidence that one-router-model behavior is becoming brittle or expensive.

## Validation ideas
- Compare deterministic-only routing, one-model routing, and hierarchical gating on latency, cost,
  and misroute rate.
- Verify that capability/policy pre-gates can reject impossible requests before model time.
- Ensure replay/logging makes the gate/coordinator decisions inspectable.

## Non-goals
- This proposal does not authorize immediate multi-model orchestration work.
- It does not replace the action-descriptor track or published workflow governance work.
- It does not assume peer-swarm or agent-of-agents patterns are needed for ordinary requests.

## Guidance for future agents
Promote this only after the capability/action boundary is stable. Otherwise gating work will lock
onto the wrong inputs and create more churn than value.

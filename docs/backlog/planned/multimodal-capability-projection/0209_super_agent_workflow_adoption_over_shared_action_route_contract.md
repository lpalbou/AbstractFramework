# Planned: Super-agent workflow-first adoption over the shared action/route substrate

## Metadata
- Created: 2026-06-14
- Status: Planned
- Completed: N/A

## ADR status
- Governing ADRs: ADR-0032, ADR-0033, ADR-0035, ADR-0036
- ADR impact: likely a companion input to the ADR introduced by `0201_gateway_action_descriptor_contract.md`; this item should stay consistent with the Gateway/Core durable boundary instead of redefining it.

## Context
The route-object foundation is now clear enough that the remaining gap is no longer conceptual.
The framework still needs one committed consumer migration for durable agent products:

- today the lower layers are converging on a shared `request/output` and resolved-route substrate;
- Gateway is converging on typed action/workflow descriptors and replay envelopes; but
- current durable specialized-agent products do not yet consistently consume the shared
  action/route substrate through published workflows and replay-safe delegation facts.

If that remains uncommitted, the framework can end up with a cleaner multimodal kernel while the
actual durable “super agent” behavior stays trapped behind private prompt conventions and app- or
bundle-local routing logic.

## Current code reality
- `abstractcore` already treats `generate(..., output=...)` as the lower-level multimodal
  entrypoint, and the active Core backlog now points toward `request/output` normalization plus a
  call-scoped resolved-route substrate.
- `abstractruntime` already has the durable execution kernel: helpers like `generate_image(...)`,
  `generate_music(...)`, and `transcribe_audio(...)` lower into one canonical `LLM_CALL` path in
  `abstractruntime/src/abstractruntime/integrations/abstractcore/run_facade.py`.
- `abstractgateway` already owns durable workflow start, workflow catalogs, replay, and
  thin-client discovery; live helper endpoints such as `/backlog/maintain` and `/backlog/advisor`
  still launch the shipped `basic-agent` baseline bundle with `prompt`, `provider`, `model`,
  `tools`, and schema-oriented inputs, while AbstractAssistant already runs through the published
  `abstractassistant-orchestrator` workflow:
  - `/backlog/maintain` runs `basic-agent` at
    `abstractgateway/src/abstractgateway/routes/gateway.py:19778`
  - `/backlog/advisor` defaults to `basic-agent` at
    `abstractgateway/src/abstractgateway/routes/gateway.py:19949`
- durable helper surfaces still expose raw `output` dict merges over the execution kernel, for
  example in `abstractruntime/src/abstractruntime/integrations/abstractcore/run_facade.py`.
- the previous proposed workflow/product charter already established the right architecture
  boundary: Core owns atomic inference, Runtime owns durable lowering, Gateway owns discovery and
  replay, and workflows own compositions and specialized super-agent behavior.

## Problem
The framework is now close to having the right substrate, but it still lacks a committed adoption
item for the durable agent products that should consume it.

Without that migration:
- the resolved-route foundation can land while specialized workflow products still rely on private
  prompt/router conventions;
- helper baseline bundles such as `basic-agent` can remain thin ReAct entrypoints instead of a
  clear baseline layered under orchestrator workflows;
- cross-app replay can explain artifacts and runs, but not the workflow-level delegation choices
  that produced them.

## What we want to do
Adopt the shared action/route substrate in workflow-first orchestrator products:

- published orchestrator workflows should consume Gateway action/workflow descriptors and Runtime
  replay-safe action summaries;
- they should execute through Runtime action resolution and resolved-route policy, not private
  route merging;
- simple baseline bundles such as `basic-agent` should stay lightweight ReAct consumers and not be
  re-scoped into the specialized orchestrator role;
- replay should preserve bounded delegation-chain and resolved-route summaries for composed
  workflow decisions.

## Why
- This turns the resolved-route object from a good substrate into a complete stack story.
- It keeps “super agent” behavior inside workflows, where it belongs, without allowing workflows to
  become a second routing engine.
- It gives thin clients a truthful, replayable explanation of how a composed agent chose and
  delegated work.

## Requirements
- Keep the existing boundary:
  - Core owns request/output normalization and the internal resolved-route substrate.
  - Runtime owns action resolution, durable lowering, and replay-safe resolved-action records.
  - Gateway owns typed action/workflow descriptors, policy filtering, and replay projection.
  - workflows own multi-step composition and specialized super-agent behavior.
- Migrate durable agent bundles to consume typed Gateway action/workflow descriptors plus bounded
  Runtime action summaries instead of private prompt conventions for capability awareness.
- Require durable agent bundles to treat route truth as read-only:
  - they may request an override only through the shared compatibility or policy-gated surface;
  - they must not merge defaults, reinterpret provider/model hints, or invent topology-specific
    route selection logic.
- Require bounded delegation-chain replay facts for workflow/super-agent runs, including at least:
  - top-level workflow identity;
  - delegated action/workflow identities;
  - requested override summary when relevant;
  - effective resolved-route summary;
  - override disposition or denial when relevant.
- Make “super agent” an internal/product-planning term, not a new durable capability type.
  Thin clients should not force ordinary users to choose between action, workflow, tool, skill,
  and super-agent concepts during the default path.
- Preserve plain-language thin-client behavior:
  - default UX is outcome-first;
  - internal route keys and descriptor IDs stay implementation terms;
  - advanced execution details appear only on inspection or in operator-focused surfaces.
- Align any future micro-model or hierarchical planner work to this substrate: planners consume
  action/workflow descriptors and replay-safe action summaries, not raw default rows or
  provider-topology knobs.

## Suggested implementation
1. Define the workflow-facing contract over `0201`, `0202`, `0204`, and `0210`:
   what an agent bundle sees, what it can request, and what replay must preserve.
2. Add or refine one reference orchestrator workflow family that composes several actions or
   workflows without owning route merging.
3. Keep `basic-agent` as the simple baseline consumer: allow light compatibility with shared
   descriptors where useful, but do not make it the primary specialized-orchestrator migration
   target.
4. Thread the same contract into future planner/gating work so no second routing vocabulary forms.
5. Update docs/examples so the ladder is explicit:
   direct Core call -> durable action -> governed workflow -> specialized super-agent workflow.

## Scope
- Workflow-first adoption of the shared action/route substrate for specialized orchestrator
  products.
- Replay-visible delegation summaries for composed workflow runs.
- Narrow baseline guidance for `basic-agent` so it remains simple and non-authoritative.
- Documentation and backlog alignment around the workflow-first super-agent boundary.

## Non-goals
- Do not move planning or workflow semantics into Core.
- Do not expose the raw resolved-route object as a normal thin-client noun.
- Do not create a second durable execution primitive beside Runtime `LLM_CALL`.
- Do not require thin clients to present action/workflow/tool/skill distinctions in the default
  happy path.
- Do not authorize bundle-local routing heuristics that bypass the shared resolver.

## Dependencies and related tasks
- `0201_gateway_action_descriptor_contract.md`
- `0202_gateway_replayable_session_and_action_envelope.md`
- `0204_runtime_capability_intent_resolution_and_policy.md`
- `0206_micro_model_gating_and_hierarchical_multimodal_planning.md`
- `0210_core_request_output_contract_and_gateway_projection_alignment.md`
- `../../planned/074_agent_skills_integration.md`
- `../../planned/0179_llm_agent_model_input_artifacts.md`
- `../../proposed/0211_public_generate_route_override_surface.md`

## Expected outcomes
- The shared resolved-route/action substrate becomes the real foundation for durable agent
  products, not just for lower-level execution plumbing.
- Specialized orchestrator workflows become capability-aware through shared Gateway/Runtime truth,
  while `basic-agent` remains the simple ReAct baseline rather than absorbing the super-agent role.
- Cross-app replay can explain not only what artifact was produced, but also which action or
  workflow was chosen and how composed delegation progressed.
- The future super-agent stays a workflow/composition layer over shared truth, not a second
  routing engine.

## Validation
- Gateway/Runtime tests prove durable agent bundle paths can consume action/workflow descriptors
  and lower through the same shared route/action substrate.
- Replay tests prove a composed workflow or super-agent run preserves bounded delegation-chain and
  resolved-route summaries across apps.
- Documentation examples clearly distinguish:
  - atomic Core generation;
  - durable action execution;
  - governed workflow composition;
  - specialized super-agent workflow behavior.

## Progress checklist
- [ ] Define the bundle-facing action/workflow consumption contract.
- [ ] Add/refine a reference orchestrator workflow that consumes the shared substrate without route
      merging.
- [ ] Confirm `basic-agent` remains a thin baseline and only adopts minimal shared-substrate
      compatibility where it materially helps.
- [ ] Add replay-safe delegation-chain summaries for composed workflows.
- [ ] Align future planner/gating items to consume the same contract.
- [ ] Update docs and track summaries with the new ladder.

## Guidance for the implementing agent
Treat this item as the first durable consumer of the multimodal substrate, not as a new semantic
foundation. The right move is to make workflows and durable agents read from shared Gateway/Runtime
truth, not to let them own route selection logic.

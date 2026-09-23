# Planned: Gateway action and workflow descriptor contract for multimodal agents

## Metadata
- Created: 2026-06-14
- Status: Planned
- Completed: N/A

## ADR status
- Governing ADRs: ADR-0032 package dependency boundaries and gateway-first apps, ADR-0033 install profiles config entrypoints and server boundaries, ADR-0035 capability routing defaults, ADR-0036 artifact descriptor contract
- ADR impact: Needs a new ADR to lock the durable boundary between Gateway-owned model-facing descriptors, Runtime canonical execution, AbstractCore lower-level capability truth, and published workflow composites.

## Context
The framework now has a clearer architectural constraint than before:

- Gateway is the persistent high-level entrypoint for durable agents and shared continuity.
- Core is the lower-level capability/kernel entrypoint for direct SDK or `/v1` use.
- Apps must remain lightweight players/views over Gateway when persistence, replay, or cross-app
  continuity matters.
- Published workflows are governed executable composites, effectively the next iteration of skills
  for durable execution.

What is still missing is a shared model-facing discovery surface that tells a durable agent:
- which atomic capability actions are callable now;
- which governed workflow composites are available now;
- what each one expects and returns; and
- which advanced fields should be disclosed only when relevant.

That discovery surface should not invent a second multimodal semantics layer. It should project
over the lower-level Core `request/output` contract and Runtime resolved-action truth.
Gateway already has real workflow-first execution and direct media contracts; the gap here is
descriptor unification and ownership clarity, not absence of durable workflow execution.

## Current code reality
- `abstractgateway/src/abstractgateway/routes/gateway.py` already exposes rich app contracts under `_build_client_capability_contracts(...)`, including run/ledger/artifact discovery, workflow catalog access, and generated-media contract builders.
- `abstractgateway/src/abstractgateway/routes/gateway.py` still exposes `/discovery/tools` as thin-client allowlist help only, not as the durable capability source of truth.
- `abstractassistant/abstractassistant/gateway/capabilities.py` already parses route/task/media readiness truth for direct media affordances.
- `abstractflow/src/utils/gatewayClient.ts` already carries typed Gateway media contracts for node gating and property affordances.
- `docs/guide/workflow-bundles.md` and `docs/guide/agent-skills.md` already distinguish workflows as executable durable units and skills as progressive-disclosure procedure packs.

## Problem
The durable agent surface is still split across several layers:

1. route/task/media truth in Gateway capability contracts;
2. workflow catalog discovery for governed composites;
3. generic tool discovery for host-side side effects; and
4. app-local capability shaping, selection UX, or route hints that are still inconsistent across
   clients.

Task-specific product endpoints and explicit workflow defaults are not inherently a problem; they
are acceptable when they bind to Gateway-owned workflow/catalog/capability truth instead of
inventing a separate routing or policy layer.

That split is survivable today, but it will become brittle as action families expand to sound,
scene3d, characters, environments, and other artifact domains, and as more apps need to replay the
same work.

## What we want to do
Define a Gateway-owned versioned descriptor contract with two durable model-facing families:

- typed action descriptors for atomic capability calls; and
- typed workflow descriptors for governed composite executions.

Both must support progressive and hierarchical disclosure instead of forcing every app or agent to
consume one huge flat surface.

## Why
- Durable/high-level agents need a Gateway-owned surface, not an app-local guess.
- Workflow catalog topology should not become the primitive noun for atomic capabilities.
- Skills/workflows/tools/actions need explicit boundaries so agent awareness stays coherent.
- Cross-app replay depends on stable IDs and stable semantics for what was selected and why.

## Requirements
- Define a versioned Gateway-owned descriptor schema generated from Runtime/Core/workflow truth,
  not handwritten per app.
- Include atomic action descriptors with stable IDs, family/modality/task, required source roles,
  output artifact semantics, option schema fragments, progress hints, durability class, and policy
  class.
- Map every atomic action descriptor to lower-level `request` and `output` schema fragments so the
  durable Gateway action plane stays aligned with Core semantics instead of current transport
  adapters.
- Keep internal descriptor IDs and route semantics separate from thin-client display language.
  The contract should support plain outcome-first labels such as “Generate image” while preserving
  lower-level identities for routing, replay, and operator inspection.
- Descriptors should complement, not outlaw, intentionally productized endpoints or hardcoded
  workflow choices for narrow surfaces such as Assistant, voice/media helper routes, or other
  task-specific Gateway APIs.
- When policy exposes advanced control, descriptors should also disclose the narrow overrideable
  route slots for that action instead of forcing clients to guess from raw provider/model fields.
- Include workflow descriptors for governed composites with stable IDs, interface contracts,
  concise suitability summaries, input/output schema refs, and ACL/readiness status.
- Keep descriptor identities and semantic fields bounded so Replay/History surfaces can persist the
  relevant decision facts without copying full live discovery payloads.
- Distinguish three durable surfaces explicitly:
  - model-facing actions;
  - model-facing workflow composites;
  - host-side tools/side effects.
- Support progressive disclosure:
  - compact family/workflow summaries first;
  - detailed action/workflow descriptors on demand or in bounded subsets;
  - advanced provider/model, backend, or route-override controls only when policy exposes them.
- Allow expert/operator surfaces to access bounded reason-coded availability metadata, for example
  `not_ready`, `not_authorized`, `budget_blocked`, `policy_hidden`, or `not_applicable`, without
  forcing ordinary clients to expose that complexity by default.
- Only emit descriptors that are truly callable for the current principal/session/runtime context.
- Keep provider/model choice hidden by default unless policy explicitly exposes overrides.

## Suggested implementation
1. Define or adopt the canonical lower-level `request/output` fragments from `0210` first, then
   add Gateway descriptor builders that project from existing capability truth and workflow catalog
   truth.
2. Keep descriptor generation close to the current `_build_client_capability_contracts(...)`
   pipeline so apps keep one authoritative Gateway source.
3. Introduce a versioned discovery block for descriptors rather than overloading `/discovery/tools`.
4. Reuse existing run-input schema and interface-contract metadata for workflow descriptors.
5. Record the descriptor/action/tool/workflow boundary in a new ADR before client migrations land.

## Scope
- Gateway action and workflow descriptor schema design.
- Progressive-disclosure contract shape and versioning policy.
- Discovery generation/tests/docs for the shared model-facing surface.

## Non-goals
- Do not make workflow IDs the primitive model-facing vocabulary for atomic capabilities.
- Do not collapse all durable capabilities into one raw mega-schema.
- Do not mirror this full durable descriptor surface into AbstractCore without strong evidence.
- Do not redefine host-side tools as durable model-facing capability actions.
- Do not treat every hardcoded workflow choice or task-specific endpoint as an anti-pattern. The
  anti-pattern is duplicating Gateway/Core routing, policy, or discovery truth in client code.

## Dependencies and related tasks
- `docs/backlog/planned/074_agent_skills_integration.md`
- `docs/backlog/planned/0179_llm_agent_model_input_artifacts.md`
- `docs/backlog/planned/multimodal-capability-projection/0202_gateway_replayable_session_and_action_envelope.md`
- `docs/backlog/planned/multimodal-capability-projection/0204_runtime_capability_intent_resolution_and_policy.md`
- `docs/backlog/proposed/0208_abstractcore_lightweight_capability_surface_boundary.md`

## Expected outcomes
- Gateway becomes the explicit durable discovery authority for high-level agent capabilities
  without becoming a second canonical multimodal semantics owner.
- Agents can reason over atomic actions and higher-order workflows without seeing raw topology or a
  flat generic blob.
- Apps can stay lightweight because descriptor truth is shared and versioned.

## Validation
- Discovery tests verify stable descriptor IDs, policy filtering, and principal-aware readiness.
- Drift tests verify descriptors are generated from the same Gateway/Core truth used by current
  media and workflow discovery surfaces.
- ADR/docs explain the durable boundary between actions, workflows, skills, tools, Runtime, and
  Core.

## Progress checklist
- [ ] Define the shared action/workflow descriptor shapes and versioning policy.
- [ ] Specify progressive-disclosure rules for compact vs detailed descriptor views.
- [ ] Generate descriptors from existing Gateway capability and workflow-catalog truth.
- [ ] Add drift-guard and ACL/readiness tests.
- [ ] Land the new ADR before consumer migrations depend on the contract.

## Guidance for the implementing agent
Do not create a second hand-maintained registry. Generate the durable high-level surface from
Runtime/Core/workflow truth, and keep the split explicit: Gateway owns durable descriptors and
policy filtering, Runtime owns execution/audit, and Core owns the lower-level capability kernel.

# Multimodal capability projection and workflow-callability backlog track

## Status
In progress

## Purpose
This track defines how AbstractFramework should expose durable multimodal agent capabilities across
Gateway-first clients without pushing execution semantics into any one UI.

Plain-language north star:
ask for an outcome, let the platform choose the right capability path by default, and let advanced
users inspect or temporarily steer execution without changing the durable boundary.

The target shape is:

- higher-level apps such as AbstractAssistant, AbstractCode Web, AbstractObserver, Flow, and
  sandbox surfaces stay lightweight Gateway clients: they may own local UX projection, typed
  authoring shells, bounded catalog normalization, and replay/view-model shaping, but not durable
  execution semantics or capability truth;
- conversations, tasks, artifacts, waits, and approvals are replayable across those apps because
  Gateway/Runtime own the durable truth;
- published workflows remain the governed executable/composite unit, effectively the stronger
  successor to “skills” for durable product behavior;
- Gateway remains the durable model-facing control-plane entrypoint, but it should project rather
  than hand-author canonical multimodal semantics;
- lower-level direct capability use should treat `abstractcore` as the lighter non-durable kernel
  entrypoint;
- AbstractCore should converge on a lightweight `generate(request, output)` contract, with today's
  `generate(..., output=...)` surface treated as the compatibility baseline toward that goal; and
- Runtime remains the only durable execution substrate and resolves normalized multimodal intent to
  canonical `LLM_CALL` media generation/transformation calls.

## Decision question
What should the shared capability surface be for durable multimodal agents when the current codebase
already has rich Gateway capability contracts, a generic Runtime media execution kernel, workflow
catalog governance, and a separate lower-level Core entrypoint for lighter non-durable apps?

## Current reality
- Gateway is already replay-first and thin-client oriented: clients render by replaying
  `history_bundle` and `ledger/stream`, and act by submitting durable commands.
- AbstractAssistant is already a gateway-native workflow-first shell, but it still owns a local
  route taxonomy, catalog normalization, and managed workflow reconciliation/publish policy at the
  UX edge.
- AbstractCode Web and AbstractObserver are already Gateway-only viewers/players, but they still
  project raw replay surfaces into app-specific chat/replay views.
- AbstractFlow already consumes richer Gateway capability contracts and is workflow-first at
  execution time, but its typed authoring affordances still depend on local capability/task
  catalogs, preflight rules, and replay projection helpers.
- Runtime already reduces typed media helpers to one canonical `output={modality, task}` execution
  kernel and owns lineage, artifacts, waits, and replay. The missing layer is the explicit
  higher-level `request/output` contract that should sit above that lowering.
- AbstractCore is already the lighter direct entrypoint for scripts, notebooks, in-process apps,
  and the standalone Core server. It already exposes lower-level `generate(..., output=...)`,
  plugin catalog/readiness surfaces, and the accepted architecture already points toward
  `generate(request, output)` as the long-term lightweight contract.
- Default routes already exist in config and control-plane storage, but they do not become one
  canonical Core-owned per-call route object that is created once and then carried through
  `generate(...)`.
  Instead, Gateway text helpers, Runtime output-route decoration, Core provider fallbacks, and
  endpoint-profile resolution still use separate route-shaped helpers and dict overlays.
- Route resolution and advanced override handling still differ too much by topology today. The same
  requested generation can resolve differently in direct Core, local Runtime, remote Runtime, and
  server execution unless the track lands one shared resolved-route policy.
- Gateway already exposes strong workflow-first and direct-media contracts. This track is about
  unifying durable descriptors, route ownership, and replay semantics, not replacing every
  task-shaped endpoint with generic discovery.

## Current implementation status

The first substrate wave is now real in code:

- `abstractcore` has a non-breaking `request=` path, normalized `GenerateRequest`, and a shared
  call-scoped `ResolvedGenerateRoute`.
- capability defaults can now carry optional `reasoning` for reasoning-capable text routes.
- `abstractruntime` derives bounded `resolved_actions` from Core route metadata and exports them in
  `history_bundle`.

The remaining work is still the bigger Gateway/client projection layer:

- Gateway action/workflow descriptors
- cross-client replay envelope projection
- Flow/Assistant/client taxonomy cleanup
- workflow-first higher-order orchestrator adoption over the shared substrate

## Architecture alternatives considered

### Alternative A: workflow catalog entries become the main model-facing surface
This reuses workflow governance and ACLs, but it leaks execution topology into prompts, creates
wrapper-workflow sprawl for base capabilities, and makes capability semantics depend on catalog
names/defaults instead of live route truth.

### Alternative B: one generic `CapabilityIntent` / `generate(output_spec, sources, options)` becomes the only model-facing primitive
This matches the Runtime kernel best and should remain the internal normalization target, but it is
too raw as the only shared product surface for the next 3-6 months. It would push validation and
discoverability burdens into clients and prompts.

### Alternative C: Gateway synthesizes typed action descriptors over the canonical Runtime generation contract
This preserves typed verbs such as `generate_image`, `edit_image`, `transcribe_audio`, and
`generate_music`, keeps Gateway as the shared durable control plane, Runtime as the executor, and
published workflows as governed composites.

## Synthesis
Use Alternative C externally and Alternative B internally, but make the Core `request/output`
contract explicit instead of letting the current compatibility kwargs become the accidental source
of truth.

In practice:
- Gateway should publish a versioned durable action-descriptor contract generated from Runtime/Core
  truth plus workflow catalog truth, and filtered by readiness/policy/principal.
- The lower-level semantic contract should be a small Core-owned `request/output` vocabulary with
  a backward-compat normalizer from current `prompt/messages/media/output` kwargs.
- That contract should also define one shared Core-owned per-call resolved-route object built from
  defaults plus any explicit temporary overrides, so the same request does not get reinterpreted
  differently by Core, local Runtime, remote Runtime, or Gateway adapters. Runtime should persist a
  bounded resolved-route snapshot, and Gateway should configure defaults/policy ceilings and
  project the resulting truth rather than owning the route object itself.
- The resolved-route object may include optional `reasoning` settings when the selected route points
  to a reasoning-capable model. That setting belongs to route/default resolution metadata rather
  than to the semantic `request` payload.
- Capability awareness should not remain a live-only discovery trick. Gateway and Runtime should
  also preserve a bounded replay-visible decision context: the action/workflow affordances that
  were actually offered, the policy class that applied, the source-artifact/context shape that
  mattered, and the action/workflow that was selected.
- Runtime should continue to normalize every action into that request/output contract and then into
  the current canonical `LLM_CALL` lowering, while preserving semantic action identity in
  replay/history/audit so another UI can render the same run honestly.
- Published workflows should package higher-order products, policies, fallbacks, and governed
  compositions over those actions, not replace the base capability surface.
- Future super-agent workflows should be published, callable, and replayable as first-class
  workflow products; shared action/workflow descriptors exist to support those workflows, not to
  replace workflow callability as the primary product surface.
- Direct Core apps should converge on the lower-level `generate(request, output)` contract and
  capability catalog/readiness surfaces unless real evidence shows they need a separate lightweight
  typed action layer.

## Items
- `0210_core_request_output_contract_and_gateway_projection_alignment.md`: define canonical
  lower-level `request` and `output`, the call-scoped resolved-route object, the backward-compat
  mapping from current kwargs, and the exact projection boundary into Gateway action descriptors
  and Runtime resolved-action records.
- `0201_gateway_action_descriptor_contract.md`: define the versioned Gateway-owned durable action
  contract and the boundary between actions, tools, workflows, replay, and the canonical Runtime
  intent.
- `0202_gateway_replayable_session_and_action_envelope.md`: define the portable session/action
  envelope and bounded decision snapshot needed for cross-app replay and continuation.
- `0203_flow_action_descriptor_alignment.md`: keep typed Flow authoring surfaces, but source
  availability and route/task metadata from the shared action contract.
- `0204_runtime_capability_intent_resolution_and_policy.md`: formalize Runtime-side action
  resolution, consumption of the shared Core-owned resolved-route object, policy classes, and
  canonical audit/provenance around the existing `LLM_CALL` path.
- `0205_multimodal_action_coverage_and_future_modality_extension.md`: close current action coverage
  gaps such as `generate_sound`, define future modality growth rules, and keep durable and
  lower-level surfaces aligned.
- `0207_cross_client_replayable_action_handoff.md`: align Gateway-first player apps such as
  AbstractAssistant, AbstractCode Web, AbstractObserver, Flow replay surfaces, and sandbox/chat
  surfaces on the same durable semantic handoff contract so app-local replay/view models stop
  inventing capability meaning, while preserving client-side rendering and bounded projection
  logic.
- `0209_super_agent_workflow_adoption_over_shared_action_route_contract.md`: align specialized
  orchestrator workflows with the shared action/route substrate while keeping `basic-agent` a
  simple baseline and avoiding private workflow-local routing logic.

## Proposed follow-ups
- `../../proposed/0206_micro_model_gating_and_hierarchical_multimodal_planning.md`: add
  deterministic pre-gates plus cheap routing/coordinator layers only after the shared action/policy
  contract is stable.
- `../../proposed/0211_public_generate_route_override_surface.md`: preserve the future question of
  whether advanced direct-Core or workflow callers need a structured temporary route-override
  surface once the internal resolved-route contract is stable and policy-gated.
- `../../proposed/0208_abstractcore_lightweight_capability_surface_boundary.md`: revisit whether
  direct Core users need a lightweight typed capability surface beyond current lower-level Core
  generation/catalog APIs.

## Reading order
Read `0210` first. It defines the lower-level contract the rest of the track should project rather
than hardening current transport details.

At the package level, `abstractcore/docs/backlog/planned/0809_generate_request_object_and_output_contract.md`
and `abstractcore/docs/backlog/planned/0810_resolved_generate_route_object_and_temporary_override_contract.md`
carry the direct-Core implementation split between public request/output normalization and the
shared call-scoped resolved-route / compatibility-mapping contract.

Then read `0201`. It should lock the Gateway-facing ADR and descriptor contract over that
lower-level Core/Runtime truth.

Implement `0204` and `0202` before broad client adoption so clients do not invent their own
semantic replay layer or approval/context handoff format.

Then implement `0207`, `0203`, and `0209` as the main consumer migrations:
- `0207` for thin-player apps and chat/task UIs;
- `0203` for Flow’s typed authoring surface.
- `0209` for workflow-first orchestrator adoption and super-agent specialization.
- `basic-agent` remains a baseline consumer, not the target super-agent architecture.

Treat `0205` as the parity and forward-compatibility pass once the action projection and replay
pipeline exist.

Keep `0206` and `0208` proposed until the base action/replay boundary is stable enough to justify
more orchestration or any Core-side discovery surface beyond the narrow `request/output` plus
call-scoped route contract.

## Related material
- `docs/guide/agent-skills.md`
- `docs/guide/workflow-bundles.md`
- `docs/guide/deployment-web.md`
- `docs/guide/telegram-integration.md`
- `docs/adr/0021-deployment-topologies-and-supported-scenarios.md`
- `docs/adr/0032-package-dependency-boundaries-and-gateway-first-apps.md`
- `docs/adr/0033-install-profiles-config-entrypoints-and-server-boundaries.md`
- `docs/adr/0035-capability-routing-defaults.md`
- `docs/adr/0036-artifact-descriptor-contract.md`
- `docs/backlog/planned/074_agent_skills_integration.md`
- `docs/backlog/planned/0179_llm_agent_model_input_artifacts.md`
- `docs/backlog/completed/0199_abstractflow_and_abstractassistant_vision_lora_and_batch_surface.md`

## Non-goals
- Do not make workflow IDs the primitive capability vocabulary for the base model surface.
- Do not replace typed Flow media nodes with one generic “generate anything” node in this track.
- Do not let individual UIs become the durable source of truth for action semantics, route policy,
  or workflow selection history.
- Do not move durable media execution ownership out of Runtime.
- Do not grow `abstractcore` into a second Gateway-like durable action plane without strong direct
  usage evidence.
